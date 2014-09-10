import sys
import igraph
import pubmed
import litnet

class BottomUp:
  def __init__(self):
    self.pmclient = pubmed.Client()
    self.net = litnet.LitNet()

  def _read_input_file(self, input_path):
    with open(input_path, 'r') as input_file:
      lines = [line.strip() for line in input_file.readlines()] 
      institution = lines[0]
      pmids = lines[1:]
      return (institution, pmids)

  def save_graph(self):
    output_file_path = self.institution + '.pkl.gz'
    self.net.save(output_file_path)

  def run(self, input_path):
    self.institution, pmids = self._read_input_file(input_path)
    refs = [{'pmid': pmid} for pmid in pmids]
    self.pmclient.add_pubmed_data(refs)

    root_index = self.net.add_v(label=self.institution, type='institution')

    for ref in refs:
      self.net.add_ref(ref, root_index)


bu = BottomUp()
bu.run(sys.argv[1])
bu.save_graph()
