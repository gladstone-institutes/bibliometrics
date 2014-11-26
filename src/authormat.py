import sys
import pandas
import igraph
import numpy

def outgoing_counts_of_type(articles, node_type):
  return [len([neighbor for neighbor in article.neighbors(mode = igraph.OUT) if neighbor['type'] == node_type]) for article in articles]

def h_index(counts):
  n = len(counts)
  indexed_counts = [0] * (n + 1)
  for i in range(n):
    indexed_counts[min(counts[i], n)] += 1

  running_sum = 0
  for i in range(n, -1, -1):
    running_sum += indexed_counts[i]
    if running_sum >= i:
      return i
  return 0

def tg_score(articles):
  tg_count = 0
  total_count = 0

  visited = set()

  for article in articles:
    for citing_article in filter(lambda n: n['type'] == 'article' and n['pubtypes'] != None, article.neighbors(mode = igraph.OUT)):
      if citing_article.index in visited: continue
      visited.add(citing_article.index)
      total_count += 1
      for pubtype in map(lambda t: t.lower(), citing_article['pubtypes']):
        if not ('trial' in pubtype or 'guideline' in pubtype): continue
        tg_count += 1
        print citing_article['title']
        break
  print tg_count, total_count
  return tg_count / float(total_count)


def main(graph_file_path, output_file_path = None):
  g = igraph.Graph.Read(graph_file_path, format='picklez')
  author_name = g['name'].lower()

  author = g.vs.find(label = author_name, type='author')

  level_1_articles = author.neighbors(mode = igraph.OUT)
  coauthor_counts = outgoing_counts_of_type(level_1_articles, 'author')
  institution_counts = outgoing_counts_of_type(level_1_articles, 'institution')
  grantagency_counts = outgoing_counts_of_type(level_1_articles, 'grantagency')
  article_years = [article['pubdate'] / 10000 for article in level_1_articles if article['pubdate'] != None]
  citcounts = outgoing_counts_of_type(level_1_articles, 'article')
  
  mat = pandas.DataFrame(index = [author_name],
      columns = [
    'mean-co-authors', 'median-co-authors', 'sd-co-authors',
    'mean-institutions', 'median-institutions', 'sd-institutions',
    'mean-grant-agencies', 'median-grant-agencies', 'sd-grant-agencies',
    'years-delta',
    'h-index',
    'max-citations',
    'tg-score'])

  mat['mean-co-authors'][author_name] = numpy.mean(coauthor_counts)
  mat['median-co-authors'][author_name] = numpy.median(coauthor_counts)
  mat['sd-co-authors'][author_name] = numpy.std(coauthor_counts)

  mat['mean-institutions'][author_name] = numpy.mean(institution_counts)
  mat['median-institutions'][author_name] = numpy.median(institution_counts)
  mat['sd-institutions'][author_name] = numpy.std(institution_counts)

  mat['mean-grant-agencies'][author_name] = numpy.mean(grantagency_counts)
  mat['median-grant-agencies'][author_name] = numpy.median(grantagency_counts)
  mat['sd-grant-agencies'][author_name] = numpy.std(grantagency_counts)

  mat['years-delta'][author_name] = max(article_years) - min(article_years)
  mat['h-index'][author_name] = h_index(citcounts)
  mat['max-citations'][author_name] = max(citcounts)
  mat['tg-score'][author_name] = tg_score(level_1_articles)

  mat.to_csv(output_file_path, mode='w')

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
