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

def main(input_path, vtype):
  g = igraph.Graph.Read(input_path, format='picklez')
  sorted_list = degree_sort(g, vtype)

  output_path = g['name'] + '-Degree-' + vtype + '.csv'
  with open(output_path, 'w') as output_file:
    output_csv = unicodecsv.writer(output_file)
    output_csv.writerow(['Name', 'Degree'])
    for p in sorted_list:
      output_csv.writerow(p)

if __name__ == '__main__':
  main(sys.argv[2], sys.argv[1])
