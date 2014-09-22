import sys
import unicodecsv
import codecs
import igraph

def degree_sort(g, vtype):
  l = []
  for v in g.vs(type=vtype):
    l.append([v['label'], v.degree(mode = igraph.IN)])
  l.sort(key = lambda p: p[1], reverse=True)
  return l

def _add_rankings(l):
  maxval = float(l[0][1])
  for p in l:
    (name, degree) = (p[0], p[1])
    ranking = degree / maxval
    p.append(ranking)

def main(input_path, vtype, output_path):
  g = igraph.Graph.Read(input_path, format='picklez')
  sorted_list = degree_sort(g, vtype)
  _add_rankings(sorted_list)

  with open(output_path, 'w') as output_file:
    output_csv = unicodecsv.writer(output_file)
    output_csv.writerow(['Name', 'Degree'])
    for p in sorted_list:
      output_csv.writerow(p)

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2], sys.argv[3] + '.csv')
