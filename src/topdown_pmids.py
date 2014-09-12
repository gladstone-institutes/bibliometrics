import sys 
import time
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

  def _add_layer_1_ref_data(self, refs, parent_index):
    self.pm_client.add_pubmed_data(refs)

    for ref in refs:
      self._add_wos_data(ref)

    for ref in refs:
      self._update_ref_counts(ref)
      ref_index = self.net.add_ref(ref, parent_index)
      self._add_layer_n_to_ref(ref, ref_index, 2, 2)

  def _add_layer_n_to_ref(self, parent_ref, parent_ref_index, layer, max_layers):
    if not 'wosid' in parent_ref:
      return

    self._print_counts()
    print 'PARENT: ', parent_ref['wosid']

    refs = self.wos_client.biblio(parent_ref)
    self.pm_client.add_pubmed_data(refs)

    for ref in refs:
      self._add_wos_data(ref)
      ref_index = self.net.add_ref(ref, parent_ref_index)
      self._update_ref_counts(ref)
      if layer < max_layers:
        self._add_layer_n_to_ref(ref, ref_index, layer + 1, max_layers)

  def run(self, input_file_path):
    input_file = open(input_file_path, 'r')
    input_lines = input_file.readlines()
    input_file.close()

    root_name = input_lines[0].strip()
    self.net = litnet.LitNet(root_name)
    root_index = self.net.add_v(label=root_name)

    pmids = [line.strip() for line in input_lines[1:]]
    refs = [{'pmid': pmid} for pmid in pmids]

    self._add_layer_1_ref_data(refs, root_index)


  def save_graph(self):
    output_file_path = self.net.g['name'] + '.pkl.gz'
    self.net.save(output_file_path)


debug.setup_interrupt()
td = TopDown()
try:
  td.run(sys.argv[1])
  td.save_graph()
finally:
  td.close()
