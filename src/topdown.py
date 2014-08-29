import sys 
import litnet
import refparse
import clinicaltrials
import pubmed
import wos

def _first_author(ref):
  authors = ref.get('authors')
  if not authors:
    return None
  else:
    return authors[0][0]

def _main(input_file_path):
  net = litnet.LitNet()
  pm_client = pubmed.Client()
  ct_client = clinicaltrials.Client()
  wos_client = wos.Client()

  input_file = open(input_file_path, 'r')
  input_lines = input_file.readlines()
  input_file.close()

  drug_name = input_lines[0].strip()
  drug_index = net.add_v(type='drug', label=drug_name)

  trials = ct_client.search(drug_name)
  for trial in trials:
    trial_index = net.add_v(type='clinicaltrial', title=trial['title'], label=trial['nctid'])
    net.g.add_edge(drug_index, trial_index)

    refs = trial['biblio']
    if refs:
      pm_client.add_pubmed_data(refs)

      for ref in refs:
        wos_refs = wos_client.search(_first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
        if len(wos_refs) == 1:
          ref.update(wos_refs[0])

      for ref in refs:
        net.add_ref(ref, trial_index)

  fda_index = net.add_v(type='clinicaltrial', label='FDA')
  fda_refs = refparse.parse_cse_refs(input_lines[1:])

  pm_client.add_pubmed_data(fda_refs)
  for ref in refs:
    wos_refs = wos_client.search(_first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
    if len(wos_refs) == 1:
      ref.update(wos_refs[0])

  for ref in fda_refs:
    net.add_ref(ref, fda_index)

  wos_client.close()

  output_file_path = drug_name + '.xml'
  net.layout()
  net.save(drug_name, output_file_path)

_main(sys.argv[1])
