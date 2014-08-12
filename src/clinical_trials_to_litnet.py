import sys
import clinicaltrials
import pubmed
import litnet

def main(drugname):
  refg = litnet.RefG()
  root_node = drugname
  refg.G.add_node(root_node)

  ct_client = clinicaltrials.Client()
  trials = ct_client.search(drugname)

  pm_client = pubmed.Client()
  for trial in trials:
    pm_client.add_pubmed_data(trial.refs)
    trial_node = trial.nctid
    refg.G.add_node(trial_node, title=trial.title, type='clinicaltrial')
    refg.G.add_edge(root_node, trial_node)

    if trial.refs:
      litnet.add_refs_to_graph(trial.nctid, trial.refs, refg)

  refg.save(drugname, 'output.xml')

main(sys.argv[1])
