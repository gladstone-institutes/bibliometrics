import logging
import sys
import lxml.etree
import re
import requests
import requests_cache
import networkx as nx
import xgmml
import codecs

def parse_multiline_numbered_list(lines):
  list_elem_re = re.compile(r'^\d+\.\s+')
  elems = list()
  buf = u''
  for line in lines:
    line = line.strip()
    m = list_elem_re.match(line)
    if m:
      if len(buf) > 0:
        elems.append(buf.strip())
      cleaned = line[m.end():]
      buf = cleaned
    else:
      buf += u' ' + line
  if len(buf) > 0:
    elems.append(buf.strip())
  return elems

def split_by_period(line):
  return [piece.strip() for piece in line.split(u'.') if len(piece) > 0]

journal_re = re.compile(r'(?P<journal>[\w\s]+),?\s+(?P<year>\d{4}).*\;\s*(?P<volume>\d+).*\:\s*(?P<firstpage>\w+)')
def parse_ref(raw):
  (authors, title, journraw) = (raw[0], raw[1], raw[-1])
  d = {'authors': authors,
       'title': title,
       'raw': raw}
  m = journal_re.match(journraw.strip())
  if m:
    d.update(m.groupdict())
  return d

def make_citmatch_str(refs, lo, hi):
  citmatch_str = u''
  for i in range(lo, hi):
    ref = refs[i]
    if 'journal' in ref:
      citmatch_str += u'{journal}|{year}|{volume}|{firstpage}|{authors}|'.format(**ref) + unicode(i) + u'|%0D\n'
  return citmatch_str

pmid_re = re.compile(r'\d+')
def pmids_by_citmatch(refs, lo, hi):
  citmatch_str = make_citmatch_str(refs, lo, hi)
  if not citmatch_str:
    return
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi',
          params={'db': 'pubmed', 'retmode': 'xml', 'bdata': citmatch_str})
  logging.debug('ecitmatch: %s', req.url)
  pmids_raw = req.text
  pmid_lines = pmids_raw.split('\n')
  for pmid_line in pmid_lines:
    pmid_line = pmid_line.strip()
    if not pmid_line: continue
    pieces = pmid_line.split('|')
    pmid = pieces[-1].encode('utf-8')
    index = pieces[-2]
    index = int(index)
    if pmid_re.match(pmid):
      refs[index]['pmid'] = pmid

def first_author_only(authors_str):
  alphanum_only = re.sub(r'[^\w\s]+', '', authors_str)
  authors_pieces = alphanum_only.split(' ')
  first_author = authors_pieces[0:2]
  return ' '.join(first_author)

def pmid_by_author_title_search(ref):
  author = first_author_only(ref['authors'])
  esearch_term = u'({title}) AND ({author} [Author - First])'.format(title=ref['title'], author=author)
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
          params={'db': 'pubmed',
                  'term': esearch_term})
  logging.debug('esearch: %s', req.url)
  tree = lxml.etree.fromstring(req.text)
  ids = tree.xpath('/eSearchResult/IdList/Id/text()')
  if ids:
    if len(ids) > 1:
      logging.warn('Multiple results for: %s', ref['raw'])
    ref['pmid'] = ids[0].encode('utf-8')

def parse_refs(lines):
  lines = parse_multiline_numbered_list(lines)
  refs = []
  for line in lines:
    pieces = split_by_period(line)
    refs.append(parse_ref(pieces))
  return refs

def split_range(n, m):
  low = 0
  for i in range(m / n + 1):
    high = min(low + m, n)
    yield (low, high)
    low = high

def populate_pmids(refs):
  for (lo, hi) in split_range(50, len(refs)):
    pmids_by_citmatch(refs, lo, hi)
  for ref in refs:
    if not 'pmid' in ref:
      pmid_by_author_title_search(ref)
    if not 'pmid' in ref:
      logging.warn('No PMID found: %s', ref['raw'])

pm_months = [
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

def add_pubmed_info(pmid_to_refs):
  pmids = ','.join(pmid_to_refs.keys())
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                     params={'db': 'pubmed', 'id': pmids, 'rettype': 'xml'})
  logging.debug('efetch: %s', req.url)
  doc = lxml.etree.fromstring(req.content)
  for article in doc.xpath('/PubmedArticleSet/PubmedArticle'):
    pmid = article.xpath('PubmedData/ArticleIdList/ArticleId[@IdType=\'pubmed\']/text()')[0]

    authors = []
    for author in article.xpath('MedlineCitation/Article/AuthorList/Author'):
      lastname = author.xpath('LastName/text()')
      initials = author.xpath('Initials/text()')
      if lastname and initials:
        name = unicode(lastname[0] + u' ' + initials[0])
      else:
        continue
      affiliation = author.xpath('Affiliation/text()')
      affiliation = unicode(affiliation[0]) if affiliation else None
      authors.append((name, affiliation))
    
    pubdate_str = u''
    pubdate_elem = article.xpath('MedlineCitation/Article/Journal/JournalIssue/PubDate')[0]
    pubdate_yr = pubdate_elem.xpath('Year/text()')
    if pubdate_yr:
      pubdate_str += pubdate_yr[0]
      pubdate_mon = pubdate_elem.xpath('Month/text()')
      if pubdate_mon:
        pubdate_str += '%02d' % (pm_months.index(pubdate_mon[0]) + 1)
        pubdate_day = pubdate_elem.xpath('Day/text()')
        if pubdate_day:
          pubdate_str += '%02d' % int(pubdate_day[0])
        else:
          pubdate_str += '00'
      else:
        pubdate_str += '0000'

    grantagencies = map(unicode, article.xpath('MedlineCitation/Article/GrantList[last()]/Grant/Agency/text()'))

    pubtypes = map(unicode, article.xpath('MedlineCitation/Article/PublicationTypeList/PublicationType/text()'))

    allterms = []
    for meshheading in article.xpath('MedlineCitation/MeshHeadingList/MeshHeading'):
      terms = meshheading.xpath('DescriptorName/text() | QualifierName/text()')
      terms = map(lambda s: ('MeSH ' + s), terms)
      allterms.append(terms)

    citreq = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi',
        params={'db': 'pubmed', 'linkname': 'pubmed_pubmed_citedin', 'id': pmid})
    citdoc = lxml.etree.fromstring(citreq.content)
    citcount = len(citdoc.xpath('/eLinkResult/LinkSet/LinkSetDb/Link'))

    ref = pmid_to_refs[pmid]
    ref['pmauthors'] = authors
    ref['pmgrantagencies'] = grantagencies
    ref['pmmeshterms'] = allterms
    ref['pmcitcount'] = citcount
    ref['pmpubtypes'] = pubtypes
    if pubdate_str:
      ref['pmpubdate'] = int(pubdate_str)

def pmid_map(refs):
  pmid_to_refs = {}
  for ref in refs:
    if 'pmid' in ref:
      pmid_to_refs[ref['pmid']] = ref
  return pmid_to_refs

class RefG:
  def __init__(self):
    self.G = nx.DiGraph()
    self.refs = {}

  def save(self, path):
    xgmml.write(self.G, path)

  def _encode_int(self, num):
    letters = 'abcdefghijklmnopqrstuvwxyz'
    nletters = len(letters)

    if 0 <= num and num < nletters:
      return letters[num]

    s = ''
    while num != 0:
      num, i = divmod(num, nletters)
      s = letters[i] + s
    return s

  def _ref_node_on_new_id(self, ref):
    refid = self._encode_int(len(self.refs))
    self.refs[refid] = ref
    self.G.add_node(refid, type='article', title=ref['title'])
    return refid
    
  def _ref_node_on_pmid(self, ref):
    pmid = ref['pmid']
    if not pmid in self.refs:
      self.refs[pmid] = ref
      self.G.add_node(pmid, type='article', title=ref['title'], pmid=pmid)
    return pmid

  def ref_node(self, ref):
    if 'pmid' in ref:
      return self._ref_node_on_pmid(ref)
    else:
      return self._ref_node_on_new_id(ref)

  def author_node(self, name):
    if not name in self.G.node:
      self.G.add_node(name, type='author')
    return name

  def affiliation_node(self, institute):
    if not institute in self.G.node:
      self.G.add_node(institute, type='institute')
    return institute

  def grant_agency_node(self, grantagency):
    if not grantagency in self.G.node:
      self.G.add_node(grantagency, type='grantagency')
    return grantagency

  def mesh_term_node(self, term):
    if not term in self.G.node:
      self.G.add_node(term, type='meshterm')
    return term

def add_refs_to_graph(root_name, refs, refg):
  refg.G.add_node(root_name)
  for ref in refs:
    ref_node = refg.ref_node(ref)
    refg.G.add_edge(ref_node, root_name)
    if 'pmcitcount' in ref:
      refg.G.node[ref_node]['citcount'] = ref['pmcitcount']
    pubdate = None
    if 'pmpubdate' in ref:
      refg.G.node[ref_node]['pubdate'] = ref['pmpubdate']
      pubdate = ref['pmpubdate']
    if 'pmpubtypes' in ref:
      refg.G.node[ref_node]['pubtypes'] = ref['pmpubtypes']
    if 'pmauthors' in ref:
      for (author, affiliation) in ref['pmauthors']:
        author_node = refg.author_node(author)
        refg.G.add_edge(ref_node, author_node)
        if pubdate:
          refg.G.node[author_node]['pubdate'] = min(pubdate, refg.G.node[author_node].get('pubdate', 30000000))
        if affiliation:
          affiliation_node = refg.affiliation_node(affiliation)
          refg.G.add_edge(author_node, affiliation_node)
          author_pubdate = refg.G.node[author_node].get('pubdate')
          if author_pubdate:
            refg.G.node[affiliation_node]['pubdate'] = min(author_pubdate, refg.G.node[affiliation_node].get('pubdate', 30000000))
    if 'pmgrantagencies' in ref:
      for grantagency in ref['pmgrantagencies']:
        grantagency_node = refg.grant_agency_node(grantagency)
        if grantagency_node in nx.all_neighbors(refg.G, ref_node):
          count = refg.G.edge[ref_node][grantagency_node]['count']
          refg.G.edge[ref_node][grantagency_node]['count'] = count + 1
        else:
          refg.G.add_edge(ref_node, grantagency_node, count=1)
    if False:
      if 'pmmeshterms' in ref:
        for terms in ref['pmmeshterms']:
          first = terms[0]
          first_node = refg.mesh_term_node(first)
          refg.G.add_edge(ref_node, first_node)
          for i in range(0, len(terms) - 1):
            term_node_src = refg.mesh_term_node(terms[i])
            term_node_trg = refg.mesh_term_node(terms[i + 1])
            refg.G.add_edge(term_node_src, term_node_trg)

def main(input_file_paths):
  refg = RefG()
  for input_file_path in input_file_paths:
    logging.info('Reading: %s', input_file_path)
    with codecs.open(input_file_path, encoding='utf-8') as input_file:
      lines = input_file.readlines()
      root_name = lines[0]
      refs = parse_refs(lines[1:])
      populate_pmids(refs)
      add_pubmed_info(pmid_map(refs))
      add_refs_to_graph(root_name, refs, refg)
  refg.save('output.xml')

logging.basicConfig(level=logging.WARNING, format='[%(levelname)s %(funcName)s] %(message)s')
requests_cache.install_cache('req-cache')
main(sys.argv[1:])
