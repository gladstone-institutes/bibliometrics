import sys
import csv
import itertools
import igraph

def read_graph(path):
  return igraph.Graph.Read(path, format='picklez')

def mesh_terms_semistructured(v):
  terms = v['meshterms']
  for term in terms:
    header = term[0]
    subheaders = term[1:]
    if subheaders:
      for subheader in subheaders:
        yield header + '/' + subheader
    else:
      yield header

def mesh_terms_flat(v):
  terms = v['meshterms']
  for term in terms:
    for header in term:
      yield header

def all_mesh_terms(g, term_func):
  s = set()
  for v in g.vs(type='article'):
    if not v['pmid']: continue
    s.update(term_func(v))
  return list(s)

def write_mat(g, writer, term_func):
  mesh_list = all_mesh_terms(g, term_func)
  mesh_indices = dict(zip(mesh_list, itertools.count(0)))
  n_mesh = len(mesh_list)

  writer.writerow(['PMID'] + mesh_list)

  for v in g.vs(type='article'):
    pmid = v['pmid']
    if not pmid: continue
    row = [0] * n_mesh
    for mesh in term_func(v):
      row[mesh_indices[mesh]] = 1
    writer.writerow([pmid] + row)

def main(input_path, output_path):
  g = read_graph(input_path)
  with open(output_path, 'w') as output:
    writer = csv.writer(output)
    write_mat(g, writer, mesh_terms_semistructured)

main(sys.argv[1], 'meshmat.csv')
