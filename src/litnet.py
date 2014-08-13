import networkx as nx
import xgmml
import pubmed
from itertools import izip, chain

class RefG:
  def __init__(self):
    self.G = nx.DiGraph()
    self.refs = {}

  def save(self, name, path):
    xgmml.write(self.G, name, path)

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
    #year = ('%s0000' % ref.year) if hasattr(ref, 'year') else None
    self.refs[refid] = ref
    #self.G.add_node(refid, type='article', title=ref.title, pubdate=year)
    self.G.add_node(refid, type='article', title=ref.title)
    if hasattr(ref, 'year'):
      self.G.node[refid]['pubdate'] = int('%s0000' % ref.year)
    return refid
    
  def _ref_node_on_wos(self, ref):
    wosid = ref.wos.wosid
    if not wosid in self.refs:
      self.refs[wosid] = ref
      self.G.add_node(wosid, type='article', title=ref.title, wosid=wosid)
    return wosid
    
  def _ref_node_on_pmid(self, ref):
    pmid = ref.pmid
    if not pmid in self.refs:
      self.refs[pmid] = ref
      self.G.add_node(pmid, type='article', title=ref.title, pmid=pmid)
    return pmid

  def ref_node(self, ref):
    if hasattr(ref, 'wos'):
      return self._ref_node_on_wos(ref)
    elif hasattr(ref, 'pmid'):
      return self._ref_node_on_pmid(ref)
    else:
      return self._ref_node_on_new_id(ref)

  def author_node(self, name):
    name = name.title().replace(',', '')
    if not name in self.G.node:
      self.G.add_node(name, type='author')
    return name

  def affiliation_node(self, institute):
    institute = institute.title()
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

def add_wos_data(refg, ref_node, ref, include_citations=True):
  refg.G.node[ref_node]['pubdate'] = ref.pubdate

  affiliations = {}
  for (affiliation_index, (address, organizations)) in ref.institutions.items():
    affiliation_node = refg.affiliation_node(address)
    refg.G.node[affiliation_node]['pubdate'] = min(ref.pubdate, refg.G.node[affiliation_node].get('pubdate', 30000000))
    affiliations[affiliation_index] = affiliation_node 

    for organization in organizations:
      organization_node = refg.affiliation_node(organization)
      refg.G.node[organization_node]['pubdate'] = min(ref.pubdate, refg.G.node[organization_node].get('pubdate', 30000000))

    for (src, trg) in izip(chain([address], organizations), organizations):
      src_node = refg.affiliation_node(src)
      trg_node = refg.affiliation_node(trg)
      refg.G.add_edge(src_node, trg_node)


  for (author, affiliation_indices) in ref.authors:
    author_node = refg.author_node(author)
    refg.G.add_edge(ref_node, author_node)

    refg.G.node[author_node]['pubdate'] = min(ref.pubdate, refg.G.node[author_node].get('pubdate', 30000000))

    if affiliation_indices:
      for affiliation_index in affiliation_indices:
        affiliation_node = affiliations[affiliation_index]
        refg.G.add_edge(author_node, affiliation_node)
    else:
      for affiliation_index in affiliations:
        affiliation_node = affiliations[affiliation_index]
        refg.G.add_edge(ref_node, affiliation_node)
  
  if include_citations:
    pm_client = pubmed.Client()
    pm_client.add_pmids(ref.citations)
    pm_client.add_pubmed_data(ref.citations)
    for cit_ref in ref.citations:
      if hasattr(cit_ref, 'pubmed'):
        pm_node = refg.ref_node(cit_ref.pubmed)
        add_pubmed_data(refg, pm_node, cit_ref.pubmed)
        refg.G.add_edge(ref_node, pm_node)
      else:
        cit_node = refg.ref_node(cit_ref)
        refg.G.add_edge(ref_node, cit_node)

def add_pubmed_data(refg, ref_node, ref, include_meshterms=False):
  refg.G.node[ref_node]['citcount'] = ref.citcount
  refg.G.node[ref_node]['pubdate'] = ref.pubdate
  refg.G.node[ref_node]['pubtypes'] = ref.pubtypes

  for (author, affiliation) in ref.authors:
    author_node = refg.author_node(author)
    refg.G.add_edge(ref_node, author_node)
    
    if ref.pubdate:
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

def add_refs_to_graph(root_name, refs, refg):
  refg.G.add_node(root_name)
  for ref in refs:
    ref_node = refg.ref_node(ref)
    refg.G.add_edge(ref_node, root_name)

    if hasattr(ref, 'wos'):
      add_wos_data(refg, ref_node, ref.wos)
    elif hasattr(ref, 'pubmed'):
      add_pubmed_data(refg, ref_node, ref.pubmed)
