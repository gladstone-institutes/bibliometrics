from io import BytesIO
import re
from itertools import count
import requests
import requests_cache
import lxml.etree
import lxml.html
from util import has_keys, xpath_str, xpath_strs

def _split_range(n, m):
  low = 0
  for i in range(m / n + 1):
    high = min(low + m, n)
    yield (low, high)
    low = high

def _ref_to_citmatch_str(ref, refkey):
  journal = ref.get('journal')
  if journal == None: journal = ''

  year = ref.get('year')
  if year == None: year = ''

  volume = ref.get('volume')
  if volume == None: volume = ''

  firstpage = ref.get('firstpage')
  if firstpage == None: firstpage = ''

  firstauthor = ref.get('authors', [['']])[0][0]
  if firstauthor == None: firstauthor = ''

  return journal       + '|' + \
         year          + '|' + \
         volume        + '|' + \
         firstpage     + '|' + \
         firstauthor   + '|' + \
         refkey        + '|' + \
         '%0D'

_pmid_re = re.compile(r'\d+')

def _ref_to_esearch_term(ref):
  title = ref['title']
  if not 'authors' in ref or not ref['authors']:
    return u'({title}[Title])'.format(title=title)
  else:
    author = ref['authors'][0][0]
    return u'({title} [Title]) AND ({author} [Author - First])'.format(title=title, author=author)

class Client:
  def __init__(self):
    self.session = requests_cache.CachedSession('.req-cache')
    self.xml_parser = lxml.etree.XMLParser(recover=True, encoding='utf-8')
    self.html_parser = lxml.html.HTMLParser(recover=True, encoding='utf-8')

  def _add_pmids_by_citmatch(self, refs):
    searchable_refs = [ref for ref in refs if not 'pmid' in ref and has_keys(ref, 'journal', 'year', 'volume', 'firstpage', 'authors')]
    if not searchable_refs:
      return

    citmatch_str = '\n'.join([_ref_to_citmatch_str(ref, str(i)) for (ref, i) in zip(searchable_refs, count())])

    req = self.session.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi',
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
        searchable_refs[index]['pmid'] = pmid

  def _add_pmid_by_author_title_scrape(self, ref):
    esearch_term = _ref_to_esearch_term(ref)
    req = self.session.get('http://www.ncbi.nlm.nih.gov/pubmed/', params={'term': esearch_term})
    doc = lxml.html.document_fromstring(req.content, parser=self.html_parser)
    idtag = doc.cssselect('.abstract .aux .rprtid .highlight')
    if not idtag == []:
      ref['pmid'] = idtag[0].text.encode('utf-8')

  def _add_pmids(self, refs):
    for (lo, hi) in _split_range(50, len(refs)):
      self._add_pmids_by_citmatch(refs[lo:hi])

    for ref in refs:
      if not 'pmid' in ref:
        self._add_pmid_by_author_title_scrape(ref)

  def add_pubmed_data(self, refs, overwrite_keys = None):
    self._add_pmids(refs)

    refs_with_pmids = [ref['pmid'] for ref in refs if 'pmid' in ref]
    if not refs_with_pmids:
      return

    pmids_str = ','.join(refs_with_pmids)
    req = self.session.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
        params={'db': 'pubmed', 'id': pmids_str, 'rettype': 'xml'})

    doc = lxml.etree.parse(BytesIO(req.content), self.xml_parser)
    articles = doc.xpath('/PubmedArticleSet/PubmedArticle')
    for article in articles:
      pubmed_ref = _article_to_pubmed_ref(article)
      ref = _dict_with_value(refs, 'pmid', pubmed_ref['pmid'])
      if overwrite_keys:
        ref.update({k: pubmed_ref.get(k, None) for k in overwrite_keys})
      else:
        ref.update(pubmed_ref)

def _dict_with_value(ds, k, v):
  for d in ds:
    if k in d and d[k] == v:
      return d
  return None

def _article_to_pubmed_ref(article):
  r = {}
  r['pmid'] = xpath_str(article, 'PubmedData/ArticleIdList/ArticleId[@IdType=\'pubmed\']/text()')

  institutions = {}
  authors = []
  for author in article.xpath('MedlineCitation/Article/AuthorList/Author'):
    lastname = xpath_str(author, 'LastName/text()')
    initials = xpath_str(author, 'Initials/text()')
    if lastname and initials:
      name = lastname + u' ' + initials
    else:
      continue
    institution_address = xpath_str(author, 'Affiliation/text()')
    institution_index = len(institutions) + 1 if institution_address else None
    if institution_address:
      institutions[institution_index] = (institution_address, None)
    authors.append((name, institution_index))
  r['authors'] = authors
  r['institutions'] = institutions
  
  r['title'] = xpath_str(article, 'MedlineCitation/Article/ArticleTitle/text()')

  pubdate_str = u''
  pubdate_elem = article.xpath('PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]')[0]
  pubdate_yr = xpath_str(pubdate_elem, 'Year/text()')
  if pubdate_yr:
    pubdate_str += pubdate_yr
    pubdate_mon = xpath_str(pubdate_elem, 'Month/text()')
    if pubdate_mon:
      pubdate_str += '%02d' % int(pubdate_mon)
      pubdate_day = xpath_str(pubdate_elem, 'Day/text()')
      if pubdate_day:
        pubdate_str += '%02d' % int(pubdate_day)
      else:
        pubdate_str += '00'
    else:
      pubdate_str += '0000'

  r['pubdate'] = int(pubdate_str) if pubdate_str else None
  r['year'] = pubdate_yr
  r['journal'] = xpath_str(article, 'MedlineCitation/MedlineJournalInfo/MedlineTA/text()')
  r['grantagencies'] = xpath_strs(article, 'MedlineCitation/Article/GrantList[last()]/Grant/Agency/text()')
  r['pubtypes'] = xpath_strs(article, 'MedlineCitation/Article/PublicationTypeList/PublicationType/text()')

  allterms = []
  for meshheading in article.xpath('MedlineCitation/MeshHeadingList/MeshHeading'):
    terms = xpath_str(meshheading, 'DescriptorName/text() | QualifierName/text()')
    allterms.append(terms)
  r['meshterms'] = allterms
  return r
