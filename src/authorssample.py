import sys
import argparse
import random
import collections
import codecs

import pubmed
import wos

def _create_mesh_terms_query(mesh_terms):
  '''Creates a query string from a list of strings representing MeSH terms.
  Example: _create_mesh_terms_query(["thrombosis", "anticoagulant"]) => "thrombosis[MeSH Terms] AND anticoagument[MeSH Terms]'''
  return ' AND '.join(['%s[MeSH Terms]' % term for term in mesh_terms])

def _create_mesh_terms_by_author(mesh_terms, author):
  '''Creates a query string from a list of strings representing MeSH terms and an author name.
  Example: _create_mesh_terms_by_author(["cystic fibrosis"], "Boucher RC") => "cystic fibrosis[MeSH Terms] AND Boucher RC[au]'''
  return ' AND '.join(['%s[MeSH Terms]' % term for term in mesh_terms]) + ' AND (%s[au])' % author

def _most_common_institute(refs):
  '''For the given list of article dictionaries, return a list of the 5 most common institutions
  across the given article nodes. The list consists of tuples containing
  the institution name and its frequency.'''
  counter = collections.Counter()
  for ref in refs:
    for address, organizations in ref['institutions'].values():
      counter.update(organizations)
  return counter.most_common(5)

class AuthorsSample:
  def __init__(self):
    self.pmclient = pubmed.Client()
    self.wosclient = wos.Client()

  def close(self):
    self.wosclient.close()

  def _first_author(self, ref):
    authors = ref.get('authors')
    if not authors:
      return None
    else:
      return authors[0][0]

  def _add_wos_data(self, ref):
    '''Takes an article dictionary and adds article data from WoS.'''
    if not 'title' in ref or not ref['title'] or not 'authors' in ref or not self._first_author(ref):
      return
    wosrefs = self.wosclient.search(self._first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
    if len(wosrefs) == 1:
      ref.update(wosrefs[0])

  def run(self, output_path, num_samples, sample_size, mesh_terms):
    output_file = codecs.open(output_path, 'w', encoding = 'utf-8')
    query = _create_mesh_terms_query(mesh_terms)
    all_articles = self.pmclient.search_for_papers(query)

    for i in range(num_samples):
      output_file.write('# Sample %d\n' % i)
      article_sample = random.sample(all_articles, sample_size)
      self.pmclient.add_pubmed_data(article_sample)
      last_authors = [article['authors'][-1][0] for article in article_sample if ('authors' in article) and (len(article['authors']) > 0)]

      for author in last_authors:
        articles_by_author = self.pmclient.search_for_papers(_create_mesh_terms_by_author(mesh_terms, author))

        self.pmclient.add_pubmed_data(articles_by_author)
        for article in articles_by_author:
          self._add_wos_data(article)

        institutes = _most_common_institute(articles_by_author)
        if not institutes or institutes[0][1] < 2:
          continue

        output_file.write('%s\n' % author)
        for institute, count in institutes:
          output_file.write('%d %s\n' % (count, institute))
        output_file.write('\n')

def _parse_args(raw_args):
  p = argparse.ArgumentParser()
  p.add_argument('--output', required=True)
  p.add_argument('--num-samples', type=int, required=True)
  p.add_argument('--sample-size', type=int, required=True)
  p.add_argument('--mesh-terms', nargs='+', required=True)
  return p.parse_args(raw_args)

if __name__ == '__main__':
  p = _parse_args(sys.argv[1:])
  aus = AuthorsSample()
  try:
    aus.run(p.output, p.num_samples, p.sample_size, p.mesh_terms)
  finally:
    aus.close()

