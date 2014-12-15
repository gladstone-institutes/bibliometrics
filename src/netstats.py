import sys
import igraph

def main(input_paths):
  counts = []
  for input_path in input_paths:
    g = igraph.Graph.Read(input_path, format='picklez')
    count = len(g.vs(type='article'))
    counts.append(count)
  print counts

if __name__ == '__main__':
  main(sys.argv[1:])
