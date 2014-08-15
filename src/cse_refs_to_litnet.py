import codecs
import os
import argparse
import sys

import ref
import pubmed
import wos
import litnet
import clinicaltrials

def main(input_file_path, output_file_path):
  pm_client = pubmed.Client()
  wos_client = wos.Client()
  ct_client = clinicaltrials.Client()

  with codecs.open(input_file_path, encoding='utf-8') as input_file:
    lines = input_file.readlines()

  drugname = lines[0].strip()
  cse_refs = ref.parse_cse_refs(lines[1:])

  pm_client.add_pmids(cse_refs)
  pm_client.add_pubmed_data(cse_refs)

  for r in cse_refs:
    if not hasattr(r, 'pmid'):
      print 'No PMID:', r.title
    if hasattr(r, 'journal'):
      wos_ref = wos_client.search(r.first_author(), r.title, r.journal, r.year)
      if wos_ref:
        r.wos = wos_ref

  refg = litnet.RefG()
  root_node = drugname
  refg.G.add_node(root_node)

  fda_node = 'FDA NDA'
  refg.G.add_node(fda_node)
  refg.G.add_edge(root_node, fda_node)
  litnet.add_refs_to_graph(fda_node, cse_refs, refg)

  trials = ct_client.search(drugname)
  for trial in trials:
    trial_node = trial.nctid
    refg.G.add_node(trial_node, title=trial.title, type='clinicaltrial')
    refg.G.add_edge(root_node, trial_node)

    if trial.refs:
      pm_client.add_pubmed_data(trial.refs)
      for trialref in trial.refs:
        if not hasattr(trialref, 'pubmed'):
          continue
        r = trialref.pubmed
        wos_ref = wos_client.search(r.first_author(), r.title, r.journal, r.year)
        if wos_ref:
          trialref.wos = wos_ref
      litnet.add_refs_to_graph(trial_node, trial.refs, refg)

  litnet.print_stats()
  if not output_file_path:
    output_file_path = drugname + '.xml'
  refg.save(drugname, output_file_path)

  wos_client.close()

def parse_args(args):
  p = argparse.ArgumentParser()
  p.add_argument('input', nargs=1, help='Input reference file')
  p.add_argument('-o', '--output', nargs='?', help='Output XGMML file name', default='')
  return p.parse_args(args)

args = parse_args(sys.argv[1:])
main(args.input[0], args.output)
