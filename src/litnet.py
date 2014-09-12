import igraph
from itertools import repeat

class LitNet:
  def __init__(self, name):
    self.g = igraph.Graph(directed=True)
    self.g['name'] = name

    self.pmid_to_v = {}
    self.wosid_to_v = {}
    self.title_to_v = {}

    self.author_to_v = {}
    self.institution_to_v = {}
    self.grant_agency_to_v = {}

  def save(self, path):
    with open(path, 'wb') as output_file:
      self.g.write(output_file, format='picklez')

  def layout(self, alg='fr', scale=4.0):
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
    return self.add_v(type='article')

  def _mesh_terms_as_semistructured(self, mesh_terms):
    l = []
    for term in mesh_terms:
      if len(term) > 1:
        header = term[0]
        subheaders = term[1:]
        for subheader in subheaders:
          l.append(header + '/' + subheader)
      else:
        l.append(term[0])
    return l

  def _add_ref_data(self, ref, ref_index):
    ref_v = self.g.vs[ref_index]
    for attr in ('wosid', 'pmid', 'title', 'pubdate', 'pubtypes'):
      if attr in ref:
        ref_v[attr] = ref[attr]
    if 'meshterms' in ref:
      ref_v['meshterms'] = self._mesh_terms_as_semistructured(ref['meshterms'])
    if 'title' in ref:
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

  def _author_key(self, author):
    return author.replace(',', '').lower()

  def _add_authors(self, ref, ref_index):
    authors = ref.get('authors')
    if not authors:
      return
    for (author, institution_index) in authors:
      author_key = self._author_key(author)
      author_index = self.author_to_v.get(author_key)
      if not author_index:
        author_index = self.add_v(type='author', label=author)
        self.author_to_v[author_key] = author_index
      self.g.add_edge(ref_index, author_index)

  def _add_institution(self, institution):
    institution_index = self.institution_to_v.get(institution)
    if institution_index == None:
      institution_index = self.add_v(type='institution', label=institution)
      self.institution_to_v[institution] = institution_index
    return institution_index

  def _add_institutions(self, ref, ref_index):
    institutions = ref.get('institutions')
    if not institutions:
      return
    for (key, (institution_address, parent_orgs)) in institutions.items():
      institution_list = ([institution_address] + parent_orgs) if parent_orgs else [institution_address]
      institution_indices = map(self._add_institution, institution_list)
      for institution_index in institution_indices:
        edge_index = self.g.get_eid(ref_index, institution_index, error = False)
        if edge_index < 0:
          self.g.add_edge(ref_index, institution_index, count = 1)
        else:
          self.g.es[edge_index]['count'] += 1

  def _add_grant_agency(self, grant_agency):
    grant_agency_index = self.grant_agency_to_v.get(grant_agency)
    if grant_agency_index == None:
      grant_agency_index = self.add_v(type='grantagency', label=grant_agency)
      self.grant_agency_to_v[grant_agency] = grant_agency_index
    return grant_agency_index

  def _add_grant_agencies(self, ref, ref_index):
    grant_agencies = ref.get('grantagencies')
    if not grant_agencies:
      return
    grant_agency_indices = map(self._add_grant_agency, grant_agencies)
    for grant_agency_index in grant_agency_indices:
      edge_index = self.g.get_eid(ref_index, grant_agency_index, error = False)
      if edge_index < 0:
        self.g.add_edge(ref_index, grant_agency_index, count = 1)
      else:
        self.g.es[edge_index]['count'] += 1

  def add_ref(self, ref, parent_index):
    ref_index = self._get_ref_index(ref)
    self._update_ref_vertex_dicts(ref, ref_index)
    self.g.add_edge(parent_index, ref_index)

    self._add_ref_data(ref, ref_index)
    self._add_authors(ref, ref_index)
    self._add_institutions(ref, ref_index)
    self._add_grant_agencies(ref, ref_index)

    return ref_index

