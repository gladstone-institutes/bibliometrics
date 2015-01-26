import re

_journal_re = re.compile(r'(?P<journal>[\w\s]+),?\s+(?P<year>\d{4}).*\;\s*(?P<volume>\d+).*\:\s*(?P<firstpage>\w+)')

def parse_cse_ref(citstr):
  '''Takes a bibliography reference in CSE format:
      Farrell PM. The prevalence of cystic fibrosis in the European Union. J Cystic Fibrosis 2008;7(5):450-453.
  and returns a ref dictionary containing the article' information:
  {
    "authors": a list of (string, integer) tuples -- the second value is always none
    "title": a string
    "journal": a string
    "volume": a string
    "firstpage" a string
  }
  '''
  pieces = [piece.strip() for piece in citstr.split(u'.') if len(piece) > 0]
  (authors_str, title, journraw) = (pieces[0], pieces[1], pieces[-1])

  authors = [(author.strip(), None) for author in authors_str.split(',')]
  r = {
    'authors': authors,
    'title': title
  }

  m = _journal_re.match(journraw.strip())
  if m:
    r['journal']   = m.group('journal')
    r['year']      = m.group('year')
    r['volume']    = m.group('volume')
    r['firstpage'] = m.group('firstpage')
  return r

_list_elem_re = re.compile(r'^\d+\.\s+')
def _parse_multiline_numbered_list(lines):
  elems = list()
  buf = u''
  for line in lines:
    line = line.strip()
    m = _list_elem_re.match(line)
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

def parse_cse_refs(lines):
  '''Takes a list of strings containing references in CSE format and
  returns a list of dictionaries containing the article information.
  The lines should be prefixed with a number followed by a dot.
  Lines can be broken up by newlines. Here's an example for how lines can look:
    ["2. Farrell PM. The prevalence of cystic fibrosis in the European Union. J Cystic",
     "Fibrosis 2008;7(5):450-453.",
     "3. Riordan JR, Rommens JM, Kerem B. Identification of the cystic fibrosis",
     "gene: cloning and characterization of complementary DNA. Science 1989, Sep",
     "8; 245(4922):1066-73."
    ]'''
  cit_strs = _parse_multiline_numbered_list(lines)
  return [parse_cse_ref(cit_str) for cit_str in cit_strs]
