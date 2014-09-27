import sys
import datetime
import pandas
import igraph

_first_day = datetime.date(1900, 1, 1)

def _parse_pubdate(pubdate):
  year = pubdate/10000
  month = pubdate / 100 - year * 100
  day = pubdate - (year * 10000) - (month * 100)
  return datetime.date(year, month, day)

def _pubdate_to_days(pubdate):
  delta = _parse_pubdate(pubdate) - _first_day
  return delta.days

def main(input_file_path, output_file_path):
  g = igraph.Graph.Read(input_file_path, format='picklez')
  articles = g.vs.select(type='article', pmid_ne=None, pubdate_ne=None, score_ne=None)
  pmids = [v['pmid'] for v in articles]

  mat = pandas.DataFrame(index=pmids, columns=['pubdate', 'pubdays', 'score', 'citcount'])
  for v in articles:
    pmid = v['pmid']
    pubdate = v['pubdate']
    pubdays = _pubdate_to_days(pubdate)
    score = v['score']
    citcount = v['citcount']

    mat['pubdate'][pmid] = pubdate
    mat['pubdays'][pmid] = pubdays
    mat['score'][pmid] = score
    mat['citcount'][pmid] = citcount

  mat.to_csv(output_file_path, mode='w')

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
