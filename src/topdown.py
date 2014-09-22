import sys 
import time
import argparse
import litnet
import refparse
import clinicaltrials
import pubmed
import wos
import debug

class TopDown:
  def __init__(self):
    self.pm_client = pubmed.Client()
    self.ct_client = clinicaltrials.Client()
    self.wos_client = wos.Client()

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

  def _add_wos_data(self, ref):
    wos_refs = self.wos_client.search(self._first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
    if len(wos_refs) == 1:
      ref.update(wos_refs[0])

  def _add_layer_of_refs(self, refs, parent_index, max_levels, level = 1):
    # add level attribute
    for ref in refs:
      ref['level'] = level

    # add pubmed data
    self.pm_client.add_pubmed_data(refs)

    # add wos data
    for ref in refs:
      if not ref.get('title'):
        continue
      self._add_wos_data(ref)

    # update our counts about refs
    for ref in refs:
      self._update_ref_counts(ref)
    self._print_counts()

    # add each ref to the graph
    for ref in refs:
      ref_index = self.net.add_ref(ref, parent_index)

      # add the next level if needed and if we have a WoS ID for ref
      if 'wosid' in ref and level < max_levels:
        child_refs = self.wos_client.biblio(ref)
        self._add_layer_of_refs(child_refs, ref_index, max_levels, level + 1)

  def run(self, input_file_path, input_format, levels, search_trials, output_file_path):
    input_file = open(input_file_path, 'r')
    input_lines = input_file.readlines()
    input_file.close()

    drug_name = input_lines[0].strip()
    self.net = litnet.LitNet(drug_name)
    self.net.g['method'] = 'topdown'
    self.net.g['levels'] = levels

    drug_index = self.net.add_v(type='drug', label=drug_name)

    if search_trials:
      trials = self.ct_client.search(drug_name)

      for trial in trials:
        trial_index = self.net.add_v(type='clinicaltrial', title=trial['title'], label=trial['nctid'])
        self.net.g.add_edge(drug_index, trial_index)

        refs = trial['biblio']
        if refs:
          self._add_layer_of_refs(refs, trial_index, levels)

    if input_format == 'cse':
      fda_index = self.net.add_v(type='clinicaltrial', label='FDA')
      fda_refs = refparse.parse_cse_refs(input_lines[1:])
      self._add_layer_of_refs(fda_refs, fda_index, levels)
    elif input_format == 'pmid':
      refs = [{'pmid': pmid.strip()} for pmid in input_lines[1:]]
      self._add_layer_of_refs(refs, drug_index, levels)

    print self.net.ref_counts
    self.net.propagate_pubdates()
    self.net.save(output_file_path + '.pkl.gz')

def _parse_args(args):
  p = argparse.ArgumentParser()
  p.add_argument('--format', required=False, choices=['cse', 'pmid'], default='cse')
  p.add_argument('--levels', type=int, required=False, default=2)
  p.add_argument('--dont-search-trials', dest='search_trials', required=False, action='store_false')
  p.set_defaults(search_trials=True)
  p.add_argument('input')
  p.add_argument('output')
  return p.parse_args(args)

if __name__ == '__main__':
  args_raw = [arg for arg in sys.argv[1:] if len(arg) > 0]
  args = _parse_args(args_raw)
  td = TopDown()
  try:
    td.run(args.input, args.format, args.levels, args.search_trials, args.output)
  finally:
    td.close()
