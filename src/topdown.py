import sys 
import threading
import time
import litnet
import refparse
import clinicaltrials
import pubmed
import wos
import debug

class TopDown:
  def __init__(self):
    self.net = litnet.LitNet()
    self.pm_client = pubmed.Client()
    self.ct_client = clinicaltrials.Client()
    self.wos_client = wos.Client()

    self.counts = {'wos': 0, 'pm': 0, 'w+p': 0, 'all': 0, '?': 0}
    self.count_printer = threading.Thread(target=self._print_counts)
    self.count_printer.shouldBeRunning = True
    self.count_printer.daemon = True

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
    while self.count_printer.shouldBeRunning:
      time.sleep(5)
      for k, v in self.counts.items():
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
      self._add_layer_n_to_ref(ref, ref_index, 2, 3)

  def _add_layer_n_to_ref(self, parent_ref, parent_ref_index, layer, max_layers):
    if not 'wosid' in parent_ref:
      return

    refs = self.wos_client.biblio(parent_ref)
    self.pm_client.add_pubmed_data(refs)

    for ref in refs:
      self._add_wos_data(ref)
      self._update_ref_counts(ref)
      ref_index = self.net.add_ref(ref, parent_ref_index)
      if layer < max_layers:
        self._add_layer_n_to_ref(ref, ref_index, layer + 1, max_layers)

  def run(self, input_file_path):
    input_file = open(input_file_path, 'r')
    input_lines = input_file.readlines()
    input_file.close()

    self.count_printer.start()

    drug_name = input_lines[0].strip()
    drug_index = self.net.add_v(type='drug', label=drug_name)

    trials = self.ct_client.search(drug_name)
    for trial in trials:
      trial_index = self.net.add_v(type='clinicaltrial', title=trial['title'], label=trial['nctid'])
      self.net.g.add_edge(drug_index, trial_index)

      refs = trial['biblio']
      if refs:
        self._add_layer_1_ref_data(refs, trial_index)

    fda_index = self.net.add_v(type='clinicaltrial', label='FDA')
    fda_refs = refparse.parse_cse_refs(input_lines[1:])
    self._add_layer_1_ref_data(fda_refs, fda_index)

    self.wos_client.close()
    self.count_printer.shouldBeRunning = False

    output_file_path = drug_name + '.xml'
    #self.net.layout()
    #self.net.save(drug_name, output_file_path)

debug.setup_interrupt()
td = TopDown()
td.run(sys.argv[1])
