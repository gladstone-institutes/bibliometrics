import nltk
import re
import requests

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

def split_by_sentences(lines):
  tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
  return map(tokenizer.tokenize, lines)

journal_re = re.compile(r'(?P<journal>[\w\s]+),?\s+(?P<year>\d{4}).*\;\s*(?P<volume>\d+).*\:\s*(?P<firstpage>\w+)')
def parse_ref(raw):
  (authors, title, journraw) = (raw[0], raw[1], raw[-1])
  d = {'authors': authors,
       'title': title}
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

def get_pmids(refs):
  req = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi',
          params={'db': 'pubmed',
                  'retmode': 'xml',
                  'bdata': refs_to_citmatch(refs)})
  return req.text

def main():
  with open('/home/samad/metrics/Kalydeco/Medical Review References.txt', 'r') as refsfile:
    raw = refsfile.read()
    refsraw = split_by_sentences(parse_multiline_numbered_list(raw))
    refs = map(parse_ref, refsraw)
    print get_pmids(refs)

main()
