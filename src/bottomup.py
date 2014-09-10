import sys
import igraph
import pubmed
import wos
import litnet

class BottomUp:
  def __init__(self):
    self.pmclient = pubmed.Client()
    self.wosclient = wos.Client()
    self.counts = {'wos': 0, 'wos-unknown': 0, 'wos-ambiguous': 0}

  def _read_input_file(self, input_path):
    with open(input_path, 'r') as input_file:
      lines = [line.strip() for line in input_file.readlines()] 
      institution = lines[0]
      pmids = lines[1:]
      return (institution, pmids)

  def save_graph(self):
    output_file_path = self.net.g['name'] + '.pkl.gz'
    self.net.save(output_file_path)

  def run(self, input_path):
    main_institution, pmids = self._read_input_file(input_path)
    self.net = litnet.LitNet(main_institution)

    refs = [{'pmid': pmid} for pmid in pmids]
    self.pmclient.add_pubmed_data(refs)

    for ref in refs:
      wosrefs = self.wosclient.search(ref['authors'][0][0], ref['title'], ref['journal'], ref['year'])
      if len(wosrefs) == 1:
        ref.update(wosrefs[0])
        self.counts['wos'] += 1
      elif len(wosrefs) == 0:
        self.counts['wos-unknown'] += 1
      else:
        self.counts['wos-ambiguous'] += 1

    root_index = self.net.add_v(label=main_institution, type='institution')

    for ref in refs:
      self.net.add_ref(ref, root_index)

  def close(self):
    self.wosclient.close()


bu = BottomUp()
try:
  bu.run(sys.argv[1])
finally:
  print bu.counts
  bu.save_graph()
  bu.close()
