import re

class Ref:
  def __init__(self):
    pass

_journal_re = re.compile(r'(?P<journal>[\w\s]+),?\s+(?P<year>\d{4}).*\;\s*(?P<volume>\d+).*\:\s*(?P<firstpage>\w+)')
class CseRef(Ref):
  def __init__(self, citstr):
    pieces = [piece.strip() for piece in citstr.split(u'.') if len(piece) > 0]
    (self.authors_str, self.title, journraw) = (pieces[0], pieces[1], pieces[-1])
    m = _journal_re.match(journraw.strip())
    if m:
      self.journal   = m.group('journal')
      self.year      = m.group('year')
      self.volume    = m.group('volume')
      self.firstpage = m.group('firstpage')

  def first_author(self):
    alphanum_only = re.sub(r'[^\w\s]+', '', self.authors_str)
    authors_pieces = alphanum_only.split(' ')
    first_author = authors_pieces[0:2]
    return ' '.join(first_author)

  def aslist(self):
    if hasattr(self, 'journal'):
      return [self.authors_str, self.title, self.journal, self.year, self.volume, self.firstpage]
    else:
      return [self.authors_str, self.title]

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
  return [CseRef(cit_str) for cit_str in cit_strs]