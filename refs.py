import nltk
import lxml.etree
import re
import requests
import wos

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
  #print ref
  author = first_author_only(ref['authors'])
  esearch_term = '({title}) AND ({author} [Author])'.format(title=ref['title'], author=author)
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

def main():
  refs = {}
  with open('Kalydeco/Medical Review References.txt', 'r') as refsfile:
    raw = refsfile.read()
    refs = parse_refs(raw)
  populate_pmids(refs)
  for ref in refs:
    print ref['authors']
    print ref['title']
    if 'pmid' in ref:
      print ref['pmid']


main()
