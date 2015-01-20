import sys
import argparse
import datetime
import litnet
import wos
import pubmed

class BottomUp:
  def __init__(self, verbose):
    self.verbose = verbose

    self.wos_client = wos.Client()
    self.pm_client = pubmed.Client()

    self.counts = {'wos': 0, 'pm': 0, 'w+p': 0, 'all': 0, '?': 0}

  def close(self):
    self.wos_client.close()

  def _first_author(self, ref):
    authors = ref.get('authors')
    if not authors:
      return None
    else:
      return authors[0][0]

  def _update_ref_counts(self, ref):
    self.counts['all'] += 1
    if 'wosid' in ref:
      self.counts['wos'] += 1
    if 'pmid' in ref:
      self.counts['pm'] += 1
    if 'wosid' in ref and 'pmid' in ref:
      self.counts['w+p'] += 1
    if not 'pmid' in ref and not 'wosid' in ref:
      self.counts['?'] += 1

  def _print_counts(self):
    print 'Total: %d' % self.counts['all']
    for k, v in self.counts.items():
      if k == 'all': continue
      print '%4s: %5d, %6.2f%%' % (k, v, (100. * float(v) / self.counts['all']))
    print

  def _time_str(self):
    return datetime.datetime.now().strftime('[%H:%M:%S]')

  def _add_wos_data(self, ref):
    if not 'title' in ref or not ref['title'] or not 'authors' in ref:
      return
    wos_refs = self.wos_client.search(self._first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
    if len(wos_refs) == 1:
      ref.update(wos_refs[0])

  def _ref_has_institution(self, ref, institution_name):
    institutions = ref.get('institutions', {})
    for (address, organizations) in institutions.values():
      if institution_name in address.lower():
        return True
      if organizations:
        for organization in organizations:
          if institution_name in organization.lower():
            return True
    return False

  def _add_layer_of_refs(self, refs, parent_index, max_levels, level, filter_func = None):
    # add level attribute
    for ref in refs:
      if ref.get('level') == None:
        ref['level'] = level

    # add pubmed data
    self.pm_client.add_pubmed_data(refs)

    # add wos data
    for ref in refs:
      self._add_wos_data(ref)

    if filter_func:
      refs = filter(filter_func, refs)

    # update ref counts
    for ref in refs:
      self._update_ref_counts(ref)
    #if self.verbose:
    #  print self._time_str(), self.counts['all'], 'articles'

    # add each ref to the graph
    for ref in refs:
      ref_index = self.net.add_ref(ref, parent_index)

      # add the next level if needed and if we have a WoS ID for ref
      if 'wosid' in ref and level < max_levels:
        child_refs = self.wos_client.citations(ref)
        self._add_layer_of_refs(child_refs, ref_index, max_levels, level + 1)

  def run(self, author_name, institution_name, output_file_name, max_levels):
    start_time = datetime.datetime.now()

    self.net = litnet.LitNet(author_name)
    root_index = self.net._add_author(author_name)

    refs = self.pm_client.search_for_papers_by_author(author_name)
    institution_name = institution_name.lower()
    self._add_layer_of_refs(refs, root_index, max_levels, 1, lambda ref: self._ref_has_institution(ref, institution_name))

    end_time = datetime.datetime.now()

    if self.verbose:
      time_delta = (end_time - start_time)
      num_articles = len(self.net.g.vs(type='article'))
      if num_articles > 0:
        print '%d articles in %s, %.1f s/article' % (num_articles, str(time_delta), float(time_delta.total_seconds() / num_articles))
      else:
        print 'No articles found.'

    #if self.verbose:
    #  self._print_counts()
    #  print self.net.ref_counts

    #if self.verbose:
    #  print 'Postprocessing...',
    #  sys.stdout.flush()
    self.net.remove_dup_authors()
    self.net.propagate_pubdates()
    #if self.verbose:
    #  print 'done.'

    #if self.verbose:
    #  print 'Saving...',
    #  sys.stdout.flush()
    self.net.save(output_file_name)
    #if self.verbose:
    #  print 'done.'

def _parse_args(args):
  p = argparse.ArgumentParser()
  p.add_argument('--levels', type=int, required=False, default=2)
  p.add_argument('-v', required=False, dest='verbose', action='store_true')
  p.set_defaults(verbose=False)
  p.add_argument('author_name')
  p.add_argument('institution_name')
  p.add_argument('output')
  return p.parse_args(args)

if __name__ == '__main__':
  args = _parse_args(sys.argv[1:])
  bu = BottomUp(args.verbose)
  try:
    bu.run(unicode(args.author_name), unicode(args.institution_name), unicode(args.output), args.levels)
  finally:
    bu.close()

