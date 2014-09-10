import sys
import itertools
import numpy
import pandas
import igraph

def read_graph(path):
  return igraph.Graph.Read(path, format='picklez')

def all_mesh_terms(g):
  s = set()
  for v in g.vs(pmid_ne=None):
    s.update(v['meshterms'])
  return list(s)

def gen_mat(g):
  mesh_list = all_mesh_terms(g)
  pmid_list = [v['pmid'] for v in g.vs(pmid_ne=None)]

  mat = pandas.DataFrame(index = mesh_list, columns = pmid_list, dtype = numpy.bool)
  mat[:] = False

  for v in g.vs(pmid_ne = None):
    col = mat[v['pmid']]
    for mesh in v['meshterms']:
      col[mesh] = True

  return mat

def main(input_path):
  g = read_graph(input_path)
  mat = gen_mat(g)

  output_path = g['name'] + '-Mesh.csv'
  mat.to_csv(output_path, mode='w')

if __name__ == '__main__':
  main(sys.argv[1])
