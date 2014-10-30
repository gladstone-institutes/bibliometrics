import sys
import igraph
import collections

def main(net_path, author_name):
  g = igraph.Graph.Read(net_path, format='picklez')

  try:
    author_node = g.vs.find(type='author', label=author_name)
  except:
    print 'No such author:', author_name
    return

  article_nodes = author_node.neighbors()
  
  institutions = []
  for article_node in article_nodes:
    for neighbor in article_node.neighbors():
      if neighbor['type'] != 'institution':
        continue
      institutions.append(neighbor['label'])

  c = collections.Counter(institutions)
  for name, count in c.most_common(5):
    print '(%d) %s' % (count, name)



if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
