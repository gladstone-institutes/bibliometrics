import sys 
import litnet
import refparse
import clinicaltrials
import pubmed
import wos

def main(input_file_path):
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
        net.add_ref(ref, trial_index)

  fda_refs = refparse.parse_cse_refs(input_lines[1:])

  wos_client.close()

  output_file_path = drug_name + '.xml'
  net.layout()
  net.save(drug_name, output_file_path)

main(sys.argv[1])
