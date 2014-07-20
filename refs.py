import sys
import nltk
import lxml.etree
import re
import requests
import networkx as nx

def parse_multiline_numbered_list(s):
  list_elem_re = re.compile(r'^\d+\.\s+')
  lines = nltk.tokenize.LineTokenizer().tokenize(s)
  elems = list()
  buf = ''
  for line in lines:
    m = list_elem_re.match(line)
    if m:
      if buf != '':
        elems.append(buf)
      cleaned = line[m.end():]
      buf = cleaned
    else:
      buf += ' ' + line
  if buf != '':
    elems.append(buf)
  return elems

def split_by_period(line):
  return [piece.strip() for piece in line.split('.') if piece != '']

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

def make_citmatch_str(refs):
  citmatch_str = ''
  i = 0
  for ref in refs:
    if 'journal' in ref:
      citmatch_str += '{journal}|{year}|{volume}|{firstpage}|{authors}|'.format(**ref) + str(i) + '|%0D\n'
    i += 1
  return citmatch_str

pmid_re = re.compile(r'\d+')
def pmids_by_citmatch(refs):
  citmatch_str = make_citmatch_str(refs)
  if not citmatch_str:
    return
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi',
          params={'db': 'pubmed', 'retmode': 'xml', 'bdata': citmatch_str})
  pmids_raw = req.text
  pmid_lines = pmids_raw.split('\n')
  for pmid_line in pmid_lines:
    pmid_line = pmid_line.strip()
    if not pmid_line: continue
    pieces = pmid_line.split('||')
    pmid_info = pieces[1]
    (index, pmid) = pmid_info.split('|')
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
  esearch_term = '({title}) AND ({author} [Author - First])'.format(title=ref['title'], author=author)
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
          params={'db': 'pubmed',
                  'term': esearch_term})
  tree = lxml.etree.fromstring(req.text)
  ids = tree.xpath('/eSearchResult/IdList/Id/text()')
  if ids:
    if len(ids) > 1:
      print 'Warning: multiple results for: ', ref['raw']
    ref['pmid'] = ids[0]

def parse_refs(raw):
  lines = parse_multiline_numbered_list(raw)
  refs = []
  for line in lines:
    pieces = split_by_period(line)
    refs.append(parse_ref(pieces))
  return refs

def populate_pmids(refs):
  pmids_by_citmatch(refs)
  for ref in refs:
    if not 'pmid' in ref:
      pmid_by_author_title_search(ref)
    if not 'pmid' in ref:
      print 'Warning: no PMID found:', ref['raw']

def add_pubmed_info(pmid_to_refs):
  pmids = ','.join(pmid_to_refs.keys())
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                     params={'db': 'pubmed', 'id': pmids, 'rettype': 'xml'})
  doc = lxml.etree.fromstring(req.content)
  for article in doc.xpath('/PubmedArticleSet/PubmedArticle'):
    pmid = article.xpath('PubmedData/ArticleIdList/ArticleId[@IdType=\'pubmed\']/text()')[0]

    authors = []
    for author in article.xpath('MedlineCitation/Article/AuthorList/Author'):
      lastname = author.xpath('LastName/text()')
      initials = author.xpath('Initials/text()')
      if lastname and initials:
        name = lastname[0] + ' ' + initials[0]
      else:
        continue
      affiliation = author.xpath('Affiliation/text()')
      affiliation = affiliation[0] if affiliation else None
      authors.append((name, affiliation))

    grantagencies = article.xpath('MedlineCitation/Article/GrantList[last()]/Grant/Agency/text()')

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

  def save_gml(self, path):
    nx.write_gml(self.G, path)

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
    self.G.add_node(refid, type='article', label=_ascii(ref['title']))
    return refid
    
  def _ref_node_on_pmid(self, ref):
    pmid = ref['pmid']
    if not pmid in self.refs:
      self.refs[pmid] = ref
      self.G.add_node(pmid, type='article', label=_ascii(ref['title']), pmid=pmid)
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

def _ascii(s):
  return unicode(s).encode('ascii', 'replace')

def add_refs_to_graph(root_name, refs, refg):
  refg.G.add_node(root_name)
  for ref in refs:
    ref_node = refg.ref_node(ref)
    refg.G.add_edge(ref_node, root_name)
    if 'pmcitcount' in ref:
      refg.G.node[ref_node]['citcount'] = ref['pmcitcount']
    if 'pmauthors' in ref:
      for (author, affiliation) in ref['pmauthors']:
        author = _ascii(author)
        author_node = refg.author_node(author)
        refg.G.add_edge(ref_node, author_node)
        if affiliation:
          affiliation = _ascii(affiliation)
          affiliation_node = refg.affiliation_node(affiliation)
          refg.G.add_edge(author_node, affiliation_node)
    if 'pmgrantagencies' in ref:
      for grantagency in ref['pmgrantagencies']:
        grantagency = _ascii(grantagency)
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
    with open(input_file_path, 'r') as input_file:
      root_name = input_file.readline()
      raw = input_file.read()
      refs = parse_refs(raw)
      populate_pmids(refs)
      add_pubmed_info(pmid_map(refs))
      add_refs_to_graph(root_name, refs, refg)
  refg.save_gml('output.gml')

main(sys.argv[1:])
