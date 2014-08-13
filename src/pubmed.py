from io import BytesIO
import re
import requests
import requests_cache
import lxml.etree
import lxml.html
import ref

def _split_range(n, m):
  low = 0
  for i in range(m / n + 1):
    high = min(low + m, n)
    yield (low, high)
    low = high

def _xmlget(url, params):
  req = requests.get(url, params=params)
  content = BytesIO(req.content)
  parser = lxml.etree.XMLParser(recover=True, encoding='utf-8')
  return lxml.etree.parse(content, parser)

def _htmlget(url, params):
  req = requests.get(url, params=params)
  parser = lxml.html.HTMLParser(recover=True, encoding='utf-8')
  return lxml.html.document_fromstring(req.content, parser=parser)


def _make_citmatch_str(refs, lo, hi):
  citmatch_str = u''
  for i in range(lo, hi):
    ref = refs[i]
    if hasattr(ref, 'journal') and hasattr(ref, 'year') and hasattr(ref, 'volume') and hasattr(ref, 'firstpage') and hasattr(ref, 'authors_str'):
      citmatch_str += (ref.journal     + '|' + \
                       ref.year        + '|' + \
                       ref.volume      + '|' + \
                       ref.firstpage   + '|' + \
                       ref.authors_str + '|' + \
                       str(i)          + '|' + \
                       '%0D\n')
  return citmatch_str

_pmid_re = re.compile(r'\d+')
def _pmids_by_citmatch(refs, lo, hi):
  citmatch_str = _make_citmatch_str(refs, lo, hi)
  if not citmatch_str:
    return
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi',
          params={'db': 'pubmed', 'retmode': 'xml', 'bdata': citmatch_str})
  pmids_raw = req.text
  pmid_lines = pmids_raw.split('\n')
  for pmid_line in pmid_lines:
    pmid_line = pmid_line.strip()
    if not pmid_line: continue
    pieces = pmid_line.split('|')
    pmid = pieces[-1].encode('utf-8')
    index = pieces[-2]
    index = int(index)
    if _pmid_re.match(pmid):
      refs[index].pmid = pmid

def _make_esearch_term(ref):
  if ref.authors_str == 'None':
    return u'({title}[Title])'.format(title=ref.title)
  else:
    author = ref.first_author()
    return u'({title} [Title]) AND ({author} [Author - First])'.format(title=ref.title, author=author)

def _pmid_by_author_title_search(ref):
  esearch_term = _make_esearch_term(ref)
  tree = _xmlget('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', params={'db': 'pubmed', 'term': esearch_term})
  ids = tree.xpath('/eSearchResult/IdList/Id/text()')
  if ids and len(ids) == 1:
    ref.pmid = ids[0].encode('utf-8')

def _pmid_by_author_title_scrape(ref):
  esearch_term = _make_esearch_term(ref)
  tree = _htmlget('http://www.ncbi.nlm.nih.gov/pubmed/', params={'term': esearch_term})
  idtag = tree.cssselect('.abstract .aux .rprtid .highlight')
  if not idtag == []:
    ref.pmid = idtag[0].text.encode('utf-8')

class Client:
  def __init__(self):
    requests_cache.install_cache('.req-cache')

  def add_pmids(self, refs):
    for (lo, hi) in _split_range(50, len(refs)):
      _pmids_by_citmatch(refs, lo, hi)

    for ref in refs:
      if not hasattr(ref, 'pmid'):
        _pmid_by_author_title_scrape(ref)

  def add_pubmed_data(self, refs):
    pmids = [ref.pmid for ref in refs if hasattr(ref, 'pmid')]
    pmids_str = ','.join(pmids)
    doc = _xmlget('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                     params={'db': 'pubmed', 'id': pmids_str, 'rettype': 'xml'})
    articles = doc.xpath('/PubmedArticleSet/PubmedArticle')
    for article in articles:
      pubmed_ref = PubMedRef(article)
      for ref in refs:
        if hasattr(ref, 'pmid') and ref.pmid == pubmed_ref.pmid:
          ref.pubmed = pubmed_ref


_pm_months = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec'
]

class PubMedRef(ref.Ref):
  def __init__(self, article):
    self.pmid = article.xpath('PubmedData/ArticleIdList/ArticleId[@IdType=\'pubmed\']/text()')[0]

    self.authors = []
    for author in article.xpath('MedlineCitation/Article/AuthorList/Author'):
      lastname = author.xpath('LastName/text()')
      initials = author.xpath('Initials/text()')
      if lastname and initials:
        name = unicode(lastname[0] + u' ' + initials[0])
      else:
        continue
      affiliation = author.xpath('Affiliation/text()')
      affiliation = unicode(affiliation[0]) if affiliation else None
      self.authors.append((name, affiliation))
    
    self.title = article.xpath('MedlineCitation/Article/ArticleTitle/text()')[0]

    pubdate_str = u''
    #pubdate_elem = article.xpath('MedlineCitation/Article/Journal/JournalIssue/PubDate')[0]
    pubdate_elem = article.xpath('PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]')[0]
    pubdate_yr = pubdate_elem.xpath('Year/text()')
    if pubdate_yr:
      pubdate_str += pubdate_yr[0]
      pubdate_mon = pubdate_elem.xpath('Month/text()')
      if pubdate_mon:
        pubdate_str += '%02d' % int(pubdate_mon[0])
        pubdate_day = pubdate_elem.xpath('Day/text()')
        if pubdate_day:
          pubdate_str += '%02d' % int(pubdate_day[0])
        else:
          pubdate_str += '00'
      else:
        pubdate_str += '0000'

    self.pubdate = int(pubdate_str) if pubdate_str else None
    self.year = pubdate_yr[0] if pubdate_yr else None

    journal = article.xpath('MedlineCitation/MedlineJournalInfo/MedlineTA/text()')
    self.journal = journal[0] if journal else None

    self.grantagencies = map(unicode, article.xpath('MedlineCitation/Article/GrantList[last()]/Grant/Agency/text()'))

    self.pubtypes = map(unicode, article.xpath('MedlineCitation/Article/PublicationTypeList/PublicationType/text()'))

    self.allterms = []
    for meshheading in article.xpath('MedlineCitation/MeshHeadingList/MeshHeading'):
      terms = meshheading.xpath('DescriptorName/text() | QualifierName/text()')
      self.allterms.append(terms)

    citreq = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi',
        params={'db': 'pubmed', 'linkname': 'pubmed_pubmed_citedin', 'id': self.pmid})
    citdoc = lxml.etree.fromstring(citreq.content)
    self.citcount = len(citdoc.xpath('/eLinkResult/LinkSet/LinkSetDb/Link'))

  def first_author(self):
    return self.authors[0][0]
