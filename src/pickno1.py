import sys
import re

prefix_path = sys.argv[1]

def print_combo(author, institution):
  print author
  print institution
  print prefix_path + '/' + author + '/' + institution + '/1/net.pklz'

institution_re = re.compile(ur'(\d+)\s(.+)')

author = None
institution = None
for line in sys.stdin.readlines():
  line = line.strip()
  if line:
    if author == None:
      author = line
    elif institution == None:
      m = institution_re.match(line)
      if not m:
        print 'Fail:', line
        break
      institution = m.group(2)
    else:
      pass
  else:
    print_combo(author, institution)
    author = None
    institution = None

if author != None:
  print_combo(author, institution)
  

