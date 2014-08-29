import igraph
import xgmml
from itertools import chain

class LitNet:
  def __init__(self):
    self.g = igraph.Graph()

    self.pmid_to_v = {}
    self.wosid_to_v = {}
    self.title_to_v = {}

    self.author_to_v = {}
    self.institution_to_v = {}

  def save(self, name, path):
    xgmml.write(self.g, name, path)

  def layout(self, alg='fr', scale=8.0):
    l = self.g.layout(alg)
    for v_index in range(self.g.vcount()):
      x, y = l[v_index]
      x *= scale
      y *= scale
      (self.g.vs[v_index]['x'], self.g.vs[v_index]['y']) = (x,y)

  def add_v(self, **attrs):
    index = self.g.vcount()
    self.g.add_vertex(**attrs)
    return index

  def _get_ref_index(self, ref):
    for (id_key, id_dict) in [('pmid', self.pmid_to_v), ('wosid', self.wosid_to_v), ('title', self.title_to_v)]:
      if id_key in ref:
        id_val = ref[id_key]
        if id_val in id_dict:
          return id_dict[id_val]
    return self.add_v()

  def _add_ref_data(self, ref, ref_index):
    ref_v = self.g.vs[ref_index]
    for attr in ('wosid', 'pmid', 'title', 'pubdate', 'pubtypes', 'meshterms'):
      if attr in ref:
        ref_v[attr] = ref[attr]
    ref_v['label'] = ref['title']

  def _update_ref_vertex_dicts(self, ref, ref_index):
    if 'wosid' in ref:
      wosid = ref['wosid']
      if not wosid in self.wosid_to_v:
        self.wosid_to_v[wosid] = ref_index
    if 'pmid' in ref:
      pmid = ref['pmid']
      if not pmid in self.pmid_to_v:
        self.pmid_to_v[pmid] = ref_index
    if not 'wosid' in ref and not 'pmid' in ref and 'title' in ref:
      self.title_to_v[ref['title']] = ref_index

  def _add_authors(self, ref, ref_index):
    authors = ref.get('authors')
    if not authors:
      return
    for (author, institution_index) in authors:
      author_index = self.author_to_v.get(author)
      if not author_index:
        author_index = self.add_v(type='author', label=author)
        self.author_to_v[author] = author_index
      self.g.add_edge(ref_index, author_index)

  def _add_institution(self, institution):
    institution_index = self.institution_to_v.get(institution)
    if not institution_index:
      institution_index = self.add_v(type='institution', label=institution)
    return institution_index

  def _add_institutions(self, ref, ref_index):
    institutions = ref.get('institutions')
    if not institutions:
      return
    for (key, (institution_address, parent_orgs)) in institutions.items():
      institution_index = self._add_institution(institution_address)
      self.g.add_edge(ref_index, institution_index)
      if parent_orgs:
        indices = map(self._add_institution, parent_orgs)
        self.g.add_edge(institution_index, indices[0])
        self.g.add_edges(zip(indices, indices[1:]))

  def add_ref(self, ref, parent_index):
    ref_index = self._get_ref_index(ref)
    self._update_ref_vertex_dicts(ref, ref_index)
    self.g.add_edge(parent_index, ref_index)

    self._add_ref_data(ref, ref_index)
    self._add_authors(ref, ref_index)
    self._add_institutions(ref, ref_index)

    return ref_index

