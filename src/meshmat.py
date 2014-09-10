import sys
import itertools
import numpy
import pandas
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
  for v in g.vs(pmid_ne=None):
    s.update(term_func(v))
  return list(s)

def gen_mat(g, term_func):
  mesh_list = all_mesh_terms(g, term_func)
  pmid_list = [v['pmid'] for v in g.vs(pmid_ne=None)]

  mat = pandas.DataFrame(index = mesh_list, columns = pmid_list, dtype = numpy.bool)
  mat[:] = False

  for v in g.vs(pmid_ne = None):
    col = mat[v['pmid']]
    for mesh in term_func(v):
      col[mesh] = True

  return mat

def main(input_path):
  g = read_graph(input_path)
  mat = gen_mat(g, mesh_terms_semistructured)

  output_path = g['name'] + '-Mesh.csv'
  mat.to_csv(output_path, mode='w')

if __name__ == '__main__':
  main(sys.argv[1])
