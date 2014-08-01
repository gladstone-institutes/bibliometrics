import networkx as nx
import xgmml

class RefG:
  def __init__(self):
    self.G = nx.DiGraph()
    self.refs = {}

  def save(self, path):
    xgmml.write(self.G, path)

  def _encode_int(self, num):
    letters = 'abcdefghijklmnopqrstuvwxyz'
    nletters = len(letters)

    if 0 <= num and num < nletters:
      return letters[num]

    s = ''
    while num != 0:
      num, i = divmod(num, nletters)
      s = letters[i] + s
    return s

  def _ref_node_on_new_id(self, ref):
    refid = self._encode_int(len(self.refs))
    self.refs[refid] = ref
    self.G.add_node(refid, type='article', title=ref.title)
    return refid
    
  def _ref_node_on_pmid(self, ref):
    pmid = ref.pmid
    if not pmid in self.refs:
      self.refs[pmid] = ref
      self.G.add_node(pmid, type='article', title=ref.title, pmid=pmid)
    return pmid

  def ref_node(self, ref):
    if hasattr(ref, 'pmid'):
      return self._ref_node_on_pmid(ref)
    else:
      return self._ref_node_on_new_id(ref)

  def author_node(self, name):
    if not name in self.G.node:
      self.G.add_node(name, type='author')
    return name

  def affiliation_node(self, institute):
    if not institute in self.G.node:
      self.G.add_node(institute, type='institute')
    return institute

  def grant_agency_node(self, grantagency):
    if not grantagency in self.G.node:
      self.G.add_node(grantagency, type='grantagency')
    return grantagency

  def mesh_term_node(self, term):
    if not term in self.G.node:
      self.G.add_node(term, type='meshterm')
    return term


def add_non_pubmed_refs_to_graph(root_name, refs, refg):
  refg.G.add_node(root_name)
  for ref in refs:
    ref_node = refg.ref_node(ref)
    refg.G.add_edge(ref_node, root_name)

def add_refs_to_graph(root_name, refs, refg, include_meshterms=False):
  refg.G.add_node(root_name)
  for ref in refs:
    ref_node = refg.ref_node(ref)
    refg.G.add_edge(ref_node, root_name)

    refg.G.node[ref_node]['citcount'] = ref.citcount
    refg.G.node[ref_node]['pubdate'] = ref.pubdate
    refg.G.node[ref_node]['pubtypes'] = ref.pubtypes

    for (author, affiliation) in ref.authors:
      author_node = refg.author_node(author)
      refg.G.add_edge(ref_node, author_node)
      refg.G.node[author_node]['pubdate'] = min(ref.pubdate, refg.G.node[author_node].get('pubdate', 30000000))
      if affiliation:
        affiliation_node = refg.affiliation_node(affiliation)
        refg.G.add_edge(author_node, affiliation_node)
        author_pubdate = refg.G.node[author_node].get('pubdate')
        if author_pubdate:
          refg.G.node[affiliation_node]['pubdate'] = min(author_pubdate, refg.G.node[affiliation_node].get('pubdate', 30000000))

    for grantagency in ref.grantagencies:
      grantagency_node = refg.grant_agency_node(grantagency)
      if grantagency_node in nx.all_neighbors(refg.G, ref_node):
        count = refg.G.edge[ref_node][grantagency_node]['count']
        refg.G.edge[ref_node][grantagency_node]['count'] = count + 1
      else:
        refg.G.add_edge(ref_node, grantagency_node, count=1)

    if include_meshterms:
      for terms in ref.meshterms:
        first = terms[0]
        first_node = refg.mesh_term_node(first)
        refg.G.add_edge(ref_node, first_node)
        for i in range(0, len(terms) - 1):
          term_node_src = refg.mesh_term_node(terms[i])
          term_node_trg = refg.mesh_term_node(terms[i + 1])
          refg.G.add_edge(term_node_src, term_node_trg)
