import codecs
import os
import os.path
import argparse
import sys
import unicodecsv
import ref
import pubmed
import wos
import litnet

def main(input_file_paths, output_file_path, no_match_file_path):
  pm_client = pubmed.Client()
  wos_client = wos.Client()
  with open(no_match_file_path, 'w') as no_match_file:
    no_match_writer = unicodecsv.writer(no_match_file, encoding='utf-8')
    no_match_writer.writerow(['Input File', 'Authors', 'Title', 'Journal', 'Year', 'Volume', 'First page', 'Raw'])
    refg = litnet.RefG()
    for input_file_path in input_file_paths:
      no_match_writer.writerow([input_file_path])

      with codecs.open(input_file_path, encoding='utf-8') as input_file:
        lines = input_file.readlines()
      root_name = lines[0]
      cse_refs = ref.parse_cse_refs(lines[1:])

      pm_client.add_pmids(cse_refs)
      pm_client.add_pubmed_data(cse_refs)

      for r in cse_refs:
        if hasattr(r, 'journal'):
          wos_ref = wos_client.search(r.first_author(), r.title, r.journal, r.year)
          if wos_ref:
            r.wos = wos_ref

      litnet.add_refs_to_graph(root_name, cse_refs, refg)

      for r in cse_refs:
        if hasattr(r, 'pmid'): continue
        refdata = r.aslist()
        refdata.insert(0, '')
        no_match_writer.writerow(refdata)
    refg.save(output_file_path)
  wos_client.close()

def unique_filename(name, extension):
  filename = '%s.%s' % (name, extension)
  i = 0
  while os.path.exists(filename):
    i += 1
    filename = '%s %d.%s' % (name, i, extension)
  return filename

def parse_args(args):
  p = argparse.ArgumentParser()
  p.add_argument('input', nargs='+', help='List of input reference files')
  p.add_argument('-o', '--output', nargs='?', help='Output XGMML file name', default='output.xml')
  p.add_argument('-n', '--no-match-output', nargs='?', help='Output CSV file of references without PMID matches', default=os.devnull)
  return p.parse_args(args)

args = parse_args(sys.argv[1:])
main(args.input, args.output, args.no_match_output)
