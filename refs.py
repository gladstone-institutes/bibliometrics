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

def split_by_sentence(line):
  return filter(lambda p: p != '', [piece.strip() for piece in line.split('.')])

def split_by_sentences(lines):
  return map(split_by_sentence, lines)


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

def ref_to_citmatch(ref, reqid):
  d = dict(ref)
  d['key'] = reqid
  return '{journal}|{year}|{volume}|{firstpage}|{authors}|{key}'.format(**d)

def refs_to_citmatch(refs):
  citmatch_str = ''
  i = 0
  for ref in refs:
    if ref.has_key('journal'):
      citmatch_str += ref_to_citmatch(ref, i) + '|%0D\n'
    i += 1
  return citmatch_str

pmid_re = re.compile(r'\d+')
def pmids_by_citmatch(refs):
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi',
          params={'db': 'pubmed',
                  'retmode': 'xml',
                  'bdata': refs_to_citmatch(refs)})
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

def clean_authors(authors):
  return ' '.join(re.sub(r'[^\w\s]+', '', authors).split(' ')[0:2])

def pmid_by_author_title_search(ref):
  #print ref
  ref['authors'] = clean_authors(ref['authors'])
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
          params={'db': 'pubmed',
                  'term': '({title}) AND ({authors} [Author])'.format(**ref)})
  tree = lxml.etree.fromstring(req.text)
  ids = map(lambda x: x.text, tree.xpath('/eSearchResult/IdList/Id'))
  if ids:
    if len(ids) > 1:
      print 'Warning: multiple results for: ', ref['raw']
    ref['pmid'] = ids[0]
  else:
    print 'Error: no results for: '
    print '  ', ref['authors'], '-', ref['title']

def main():
  refs = {}
  with open('Kalydeco/Medical Review References.txt', 'r') as refsfile:
    raw = refsfile.read()
    refs_raw = split_by_sentences(parse_multiline_numbered_list(raw))
    refs = map(parse_ref, refs_raw)
  pmids_by_citmatch(refs)

  for ref in refs:
    if not 'pmid' in ref:
      pmid_by_author_title_search(ref)

  client = wos.Client()
  for ref in refs:
    if not 'pmid' in ref:
      continue
    ref['authors'] = clean_authors(ref['authors'])
    doc = client.search(ref['title'], ref['authors'])
    print ref['authors'], '-', ref['title'], ':', len(doc.cssselect('.search-results-item'))

main()
