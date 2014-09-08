import sys
import re
import igraph

def read_graph(path):
  with open(path, 'rb') as f:
    return igraph.Graph.Read(f, format='picklez')

def get_root(g):
  return g.vs(type='drug')[0]

alphanum_re = re.compile(r'\W+')
def children_dict(n):
  d = dict()
  adj_vs = n.neighbors(mode=igraph.OUT)
  for c in adj_vs:
    ctype = c['type']
    if not ctype in ['article', 'clinicaltrial', 'drug']:
      continue
    label = c['label']
    if ctype == 'article':
      if c['pmid']:
        label = c['pmid']
      elif c['wosid']:
        label = c['wosid']
      else:
        label = alphanum_re.sub('', label.lower())
    d[label] = c
  return d

def compare(n1, n2, n1_seen = set(), n2_seen = set(), level = 0):
  print (' ' * level), n1['label']
  print (' ' * level), n2['label']

  n1_seen.add(n1.index)
  n2_seen.add(n2.index)

  children1 = children_dict(n1)
  children2 = children_dict(n2)

  titles1 = set(children1.keys())
  titles2 = set(children2.keys())

  if not titles1 == titles2:
    n1_only = titles1 - titles2
    n2_only = titles2 - titles1

    print (' ' * level), 'Comparison failed!'
    print 'Only in', n1['label']
    for title in n1_only:
      c = children1[title]
      print ' *', c['label'], c['pmid'], c['wosid']

    print 'Only in', n2['label']
    for title in n2_only:
      c = children2[title]
      print ' *', c['label'], c['pmid'], c['wosid']

  both_n1_n2 = titles1 & titles2;
  for title in both_n1_n2:
    child1 = children1[title]
    if child1.index in n1_seen: continue
    child2 = children2[title]
    if child2.index in n2_seen: continue
    compare(child1, child2, n1_seen, n2_seen, level + 1)
  
def main(path1, path2):
  g1 = read_graph(path1)
  g2 = read_graph(path2)

  r1 = get_root(g1)
  r2 = get_root(g2)

  compare(r1, r2)

file1_path = sys.argv[1]
file2_path = sys.argv[2]
main(file1_path, file2_path)
