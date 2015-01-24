import sys
import argparse
import datetime
import pandas
import igraph

_first_day = datetime.date(1900, 1, 1)

def _parse_pubdate(pubdate):
  '''Takes an integer (e.g. 19850726) and returns a proper date object (1985/07/26).'''
  year = pubdate/10000
  month = pubdate / 100 - year * 100
  day = pubdate - (year * 10000) - (month * 100)
  return datetime.date(year, month, day)

def _pubdate_to_days(pubdate):
  '''Takes a date object and returns the number of days since 1/1/1900.'''
  delta = _parse_pubdate(pubdate) - _first_day
  return delta.days

def _pubdate_to_year(pubdate):
  '''Takes an integer (e.g. 19850726) and returns the year (1985) as an integer.'''
  return pubdate / 10000

_computed_columns = {
  'pubdays': ('pubdate', _pubdate_to_days),
  'year':    ('pubdate', _pubdate_to_year),
}

def _get_column_value(articlev, column):
  '''Returns the value of a given article attribute. Passes the article
  attribute value to a function specified by _computed_columns if
  the column is a key in _computed_columns.'''
  if column in _computed_columns:
    (key, func) = _computed_columns[column]
    value = articlev[key]
    return func(value) if value != None else None
  else:
    return articlev[column]

def _article_is_clinical(articlev):
  '''Returns true if "Clinical" is in the article's pubtype'''
  pubtypes = articlev['pubtypes']
  if pubtypes == None:
    return False
  for pubtype in pubtypes:
    if 'Clinical' in pubtype:
      return True
  return False

def _article_is_non_clinical(articlev):
  '''Returns true if "Clinical" is not in the article's pubtype'''
  pubtypes = articlev['pubtypes']
  if pubtypes == None:
    return False
  for pubtype in pubtypes:
    if 'Clinical' in pubtype:
      return False
  return True

def _main(input_file_path, output_file_path, columns, filter_method):
  g = igraph.Graph.Read(input_file_path, format='picklez')

  mat = pandas.DataFrame(columns=columns)
  for (index, articlev) in enumerate(g.vs.select(type='article')):
    if filter_method == 'clinical-only':
      if not _article_is_clinical(articlev): continue
    elif filter_method == 'non-clinical-only':
      if not _article_is_non_clinical(articlev): continue
      
    row = map(lambda column: _get_column_value(articlev, column), columns)
    mat.loc[index] = row

  mat.to_csv(output_file_path, mode='w')

def _parse_args(rawargs):
  p = argparse.ArgumentParser()
  p.add_argument('--filter', choices=['clinical-only', 'non-clinical-only'])
  p.add_argument('input')
  p.add_argument('output')
  p.add_argument('columns', nargs='+', choices=['pmid', 'pubdate', 'pubdays', 'score', 'citcount', 'year'])
  p.set_defaults(columns=['pubdays'])
  return p.parse_args(rawargs)

if __name__ == '__main__':
  args = _parse_args(sys.argv[1:])
  _main(args.input, args.output, args.columns, args.filter)
