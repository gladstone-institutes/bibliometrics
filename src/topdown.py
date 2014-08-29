import sys 
import litnet
import refparse
import clinicaltrials
import pubmed
import wos

class TopDown:
  def __init__(self):
    self.net = litnet.LitNet()
    self.pm_client = pubmed.Client()
    self.ct_client = clinicaltrials.Client()
    self.wos_client = wos.Client()

  def _first_author(self, ref):
    authors = ref.get('authors')
    if not authors:
      return None
    else:
      return authors[0][0]

  def run(self, input_file_path):
    input_file = open(input_file_path, 'r')
    input_lines = input_file.readlines()
    input_file.close()

    drug_name = input_lines[0].strip()
    drug_index = self.net.add_v(type='drug', label=drug_name)

    trials = self.ct_client.search(drug_name)
    for trial in trials:
      trial_index = self.net.add_v(type='clinicaltrial', title=trial['title'], label=trial['nctid'])
      self.net.g.add_edge(drug_index, trial_index)

      refs = trial['biblio']
      if refs:
        self.pm_client.add_pubmed_data(refs)

        for ref in refs:
          wos_refs = self.wos_client.search(self._first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
          if len(wos_refs) == 1:
            ref.update(wos_refs[0])

        for ref in refs:
          self.net.add_ref(ref, trial_index)

    fda_index = self.net.add_v(type='clinicaltrial', label='FDA')
    fda_refs = refparse.parse_cse_refs(input_lines[1:])

    self.pm_client.add_pubmed_data(fda_refs)
    for ref in refs:
      wos_refs = self.wos_client.search(self._first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
      if len(wos_refs) == 1:
        ref.update(wos_refs[0])

    for ref in fda_refs:
      self.net.add_ref(ref, fda_index)

    self.wos_client.close()

    output_file_path = drug_name + '.xml'
    self.net.layout()
    self.net.save(drug_name, output_file_path)

td = TopDown()
td.run(sys.argv[1])
