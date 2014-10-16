import sys
import litnet
import wos
import pubmed

class BottomUp:
  def __init__(self):
    self.wos_client = wos.Client()
    self.pm_client = pubmed.Client()

  def close(self):
    self.wos_client.close()

  def _first_author(self, ref):
    authors = ref.get('authors')
    if not authors:
      return None
    else:
      return authors[0][0]

  def _add_wos_data(self, ref):
    wos_refs = self.wos_client.search(self._first_author(ref), ref.get('title'), ref.get('journal'), ref.get('year'))
    if len(wos_refs) == 1:
      ref.update(wos_refs[0])

  def run(self, author_name, output_file_name):
    self.net = litnet.LitNet(author_name)
    root_index = self.net._add_author(author_name)

    refs = self.pm_client.search_for_papers_by_author(author_name)
    self.pm_client.add_pubmed_data(refs)

    for ref in refs:
      self._add_wos_data(ref)

    for ref in refs:
      self.net.add_ref(ref, root_index)

    self.net.save(output_file_name)

if __name__ == '__main__':
  bu = BottomUp()
  try:
    bu.run(unicode(sys.argv[1]), sys.argv[2])
  finally:
    bu.close()

