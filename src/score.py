import sys
import igraph
from collections import Counter

def _read_graph(input_file_path):
  return igraph.Graph.Read(input_file_path, format='picklez')

def _write_graph(g, output_file_path):
  with open(output_file_path, 'wb') as output_file:
    g.write(output_file, format='picklez')

def _article_score(articlev):
  return len(filter(lambda v: v['type'] == 'article', articlev.neighbors(mode = igraph.IN)))

def _main(input_file_path, output_file_path, factor):
  g = _read_graph(input_file_path)

  rootv = g.vs.find(type='drug')
  for (v, depth, parentv) in g.bfsiter(rootv.index, advanced = True):
    if not v['type'] == 'article': continue
    parent_score = parentv['score'] if parentv['type'] == 'article' else 0.0
    v['score'] = parent_score + _article_score(v)

  for neighbor_type in ['author', 'institution', 'grantagency']:
    for neighborv in g.vs(type=neighbor_type):
      sum_scores = 0.0
      for articlev in filter(lambda v: v['type'] == 'article', neighborv.neighbors(mode = igraph.IN)):
        score = articlev['score']
        if score == None:
          continue
        sum_scores += (score ** factor)
      neighborv['score'] = sum_scores ** (1.0 / factor)


  _write_graph(g, output_file_path)


if __name__ == '__main__':
  _main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
