import re

_journal_re = re.compile(r'(?P<journal>[\w\s]+),?\s+(?P<year>\d{4}).*\;\s*(?P<volume>\d+).*\:\s*(?P<firstpage>\w+)')

def _parse_cse_ref(citstr):
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
  cit_strs = _parse_multiline_numbered_list(lines)
  return [_parse_cse_ref(cit_str) for cit_str in cit_strs]
