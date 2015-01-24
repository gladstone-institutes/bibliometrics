from io import BytesIO
import re
from itertools import count
import requests
import requests_cache
import lxml.etree
import lxml.html
from util import has_keys, xpath_str, xpath_strs

def _split_range(n, m):
  '''Given a range [0,m], return
  an iterator of ranges ([0,n], [n,2n], [2n, 3n], ..., [in, m]).
  Example: _split_range(15, 40) => ([0,15], [15, 30], [30, 40])'''
  low = 0
  for i in range(m / n + 1):
    high = min(low + n, m)
    yield (low, high)
    low = high

def _ref_to_citmatch_str(ref, refkey):
  '''Takes a ref (article data in a dictionary) and builds a citmatch string
  (a PubMed query format). refkey is an arbitrary identifier for the given ref.'''
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
  '''Takes a ref (article data in a dictionary) and builds an esearch term
  (a PubMed query format).'''
  title = ref['title']
  if not 'authors' in ref or not ref['authors']:
    return u'({title}[Title])'.format(title=title)
  else:
    author = ref['authors'][0][0]
    return u'({title} [Title]) AND ({author} [Author - First])'.format(title=title, author=author)

class Client:
  def __init__(self):
    self.session = requests_cache.CachedSession('.req-cache')
    self.session.mount('http://eutils.ncbi.nlm.nih.gov', requests.adapters.HTTPAdapter(max_retries=10))
    self.session.mount('http://www.ncbi.nlm.nih.gov', requests.adapters.HTTPAdapter(max_retries=10))
    self.xml_parser = lxml.etree.XMLParser(recover=True, encoding='utf-8')
    self.html_parser = lxml.html.HTMLParser(recover=True, encoding='utf-8')

  def _add_pmids_by_citmatch(self, refs):
    '''Try to match the list of refs (dictionaries of article data) using the citmatch service.
    If the ref is successfully matched, it will acquire a PMID attribute.'''
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
    '''Try to match the given ref (a dictionary of article data) by doing a standard
    PubMed article search. If the match succeeds, the ref will acquire a PMID attribute.'''
    esearch_term = _ref_to_esearch_term(ref)
    req = self.session.get('http://www.ncbi.nlm.nih.gov/pubmed/', params={'term': esearch_term})
    doc = lxml.html.document_fromstring(req.content, parser=self.html_parser)
    idtag = doc.cssselect('.abstract .aux .rprtid .highlight')
    if not idtag == []:
      ref['pmid'] = idtag[0].text.encode('utf-8')

  def _add_pmids(self, refs):
    '''Takes a list of refs (dictionaries containing article data) and tries to
    match their PMIDs. First it will use the citmatch method. If that fails, it will
    try using the scraping method.'''
    #print 'add pmids for %d refs' % len(refs)
    for (lo, hi) in _split_range(50, len(refs)):
      #print 'add pmids: %d to %d of %d' % (lo, hi, len(refs))
      self._add_pmids_by_citmatch(refs[lo:hi])

    for ref in refs:
      if not 'pmid' in ref:
        self._add_pmid_by_author_title_scrape(ref)

  def add_pubmed_data(self, refs):
    '''Takes a list of refs (dictionaries containing article data) and tries to add
    as much information about them stored in PubMed.'''
    self._add_pmids(refs)

    refs_with_pmids = [ref['pmid'] for ref in refs if 'pmid' in ref]
    if not refs_with_pmids: return #print '%d pmids found of %d refs' % (len(refs_with_pmids), len(refs))

    for (lo, hi) in _split_range(100, len(refs_with_pmids)):
      #print 'pubmed data: %d to %d of %d' % (lo, hi, len(refs_with_pmids))
      pmids_str = ','.join(refs_with_pmids[lo:hi])
      req = self.session.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
          params={'db': 'pubmed', 'id': pmids_str, 'rettype': 'xml'})

      doc = lxml.etree.parse(BytesIO(req.content), self.xml_parser)
      articles = doc.xpath('/PubmedArticleSet/PubmedArticle')
      for article in articles:
        pubmed_ref = _article_to_pubmed_ref(article)
        ref = _dict_with_value(refs, 'pmid', pubmed_ref['pmid'])
        ref.update(pubmed_ref)

  def search_for_papers_by_author(self, author_name):
    '''Return a list of refs (article data in dictionaries) written by the given author.'''
    term = '"%s"[Author]' % author_name
    req = self.session.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
        params={'db': 'pubmed', 'term': term, 'retmax': 100000})
    doc = lxml.etree.parse(BytesIO(req.content), self.xml_parser)
    pmids = doc.xpath('/eSearchResult/IdList/Id/text()')
    refs = [{'pmid': unicode(pmid)} for pmid in pmids]
    return refs
  
  def num_papers_by_author(self, author_name):
    '''Return the number of papers written by the given author.'''
    term = '"%s"[Author]' % author_name
    req = self.session.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
        params={'db': 'pubmed', 'term': term, 'retmax': 100000})
    doc = lxml.etree.parse(BytesIO(req.content), self.xml_parser)
    count = doc.xpath('/eSearchResult/Count/text()')
    return int(count[0])

  def search_for_papers(self, term):
    '''Return a list of refs (article data in dictionaries) that match the given
    PubMed query term.'''
    req = self.session.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
        params={'db': 'pubmed', 'term': term, 'retmax': 100000})
    doc = lxml.etree.parse(BytesIO(req.content), self.xml_parser)
    pmids = doc.xpath('/eSearchResult/IdList/Id/text()')
    refs = [{'pmid': unicode(pmid)} for pmid in pmids]
    return refs

def _dict_with_value(ds, k, v):
  '''Given a list of dictionaries (ds),
  return the dictionary d such that d[k] == v.'''
  for d in ds:
    if k in d and d[k] == v:
      return d
  return None

def _article_to_pubmed_ref(article):
  '''Convert PubMed XML data about an article into a ref (dictionary containing the article data).'''
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
    terms = xpath_strs(meshheading, 'DescriptorName/text() | QualifierName/text()')
    allterms.append(terms)
  r['meshterms'] = allterms
  return r
