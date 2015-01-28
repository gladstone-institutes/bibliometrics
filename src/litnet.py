#!/usr/bin/env python
# -*- coding: utf-8 -*-

import igraph
from itertools import repeat 
from collections import Counter
import unicodedata

class LitNet:
  def __init__(self, name):
    self.g = igraph.Graph(directed=True)
    self.g['name'] = name

    self.ref_counts = {'all': 0, 'new': 0, 'pmid': 0, 'wosid': 0, 'title': 0}

    self.pmid_to_v = {}
    self.wosid_to_v = {}
    self.title_to_v = {}

    self.author_to_v = {}
    self.institution_to_v = {}
    self.grant_agency_to_v = {}

  def save(self, path):
    '''Save the litnet to a pklz format'''
    with open(path, 'wb') as output_file:
      self.g.write(output_file, format='picklez')

  def layout(self, alg='fr', scale=4.0):
    '''Apply a force-directed layout on the litnet'''
    l = self.g.layout(alg)
    for v_index in range(self.g.vcount()):
      x, y = l[v_index]
      x *= scale
      y *= scale
      self.g.vs[v_index]['graphics'] = {'x': str(x), 'y': str(y)}

  def add_v(self, **attrs):
    '''Wrapper around igraph.Graph.add_vertex method so that it returns the node index.'''
    index = self.g.vcount()
    self.g.add_vertex(**attrs)
    return index

  def _add_unique_edge(self, src, trg, **attrs):
    '''Only adds an edge between src and trg if no edge exists.
    If one exists, this will augment the existing edge's attributes.'''
    eid = self.g.get_eid(src, trg, error = False)
    if eid < 0:
      self.g.add_edge(src, trg, **attrs)
    else:
      e = self.g.es[eid]
      for k, v in attrs.items():
        e[k] = v

  def _get_ref_index(self, ref):
    '''Returns the article node index that matches the given ref (article data stored in a dictionary).
    If the ref specifies article information that isn't in the network,
    this will return the index to a new article node.'''
    self.ref_counts['all'] += 1
    for (id_key, id_dict) in [('pmid', self.pmid_to_v), ('wosid', self.wosid_to_v), ('title', self.title_to_v)]:
      if id_key in ref:
        id_val = ref[id_key]
        if id_val in id_dict:
          self.ref_counts[id_key] += 1
          return id_dict[id_val]
    self.ref_counts['new'] += 1
    return self.add_v(type='article')

  def _mesh_terms_as_semistructured(self, mesh_terms):
    '''Given a list of MeSH terms as strings, returns a list of strings
    representing the MeSH terms as semistructured.
    Example: _mesh_terms_as_semistructured([["A", "B", "C"], ["X"], ["Y"]]) => ["A/B", "A/C", "X", "Y"]'''
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
    '''Adds a ref (a dictionary containing article data) to the litnet.'''
    ref_v = self.g.vs[ref_index]
    for attr in ('wosid', 'pmid', 'title', 'pubdate', 'pubtypes', 'level', 'citcount'):
      if attr in ref:
        ref_v[attr] = ref[attr]
    if 'meshterms' in ref:
      ref_v['meshterms'] = self._mesh_terms_as_semistructured(ref['meshterms'])
    if 'title' in ref:
      ref_v['label'] = ref['title']

  def _update_ref_vertex_dicts(self, ref, ref_index):
    '''Adds the ref to the wosid_to_v, pmid_to_v, and title_to_v dictionaries.'''
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

  def _normalize_author(self, author):
    '''Takes an author and strips accent marks and punctuation.
    Example: _normalize_author("L’Hôtilla, Çammade") => "Lhotilla Cammade"'''
    lower = author.lower()
    no_accent_letters = unicodedata.normalize('NFKD', lower).encode('ascii', 'ignore').decode()
    no_punctuation = no_accent_letters.replace(',', '').replace('.', '')
    return no_punctuation 

  def _add_author(self, author):
    '''Add a given author name to the litnet if the author doesn't already exist
    in the litnet. Returns its node index.'''
    author_fixed = self._normalize_author(author)
    author_index = self.author_to_v.get(author_fixed)
    if author_index == None:
      author_index = self.add_v(type='author', label=author_fixed)
      self.author_to_v[author_fixed] = author_index
    return author_index

  def _add_authors(self, ref, ref_index):
    '''Adds all authors specified by the given ref (dictionary containing article data).'''
    authors = ref.get('authors')
    if not authors:
      return
    for (author, institution_index) in authors:
      author_index = self._add_author(author)
      self._add_unique_edge(ref_index, author_index)

  def _add_institution(self, institution):
    '''Add a given institution name to the litnet if the institution doesn't already exist
    in the litnet. Returns its node index.'''
    institution_index = self.institution_to_v.get(institution)
    if institution_index == None:
      institution_index = self.add_v(type='institution', label=institution)
      self.institution_to_v[institution] = institution_index
    return institution_index

  def _add_institutions(self, ref, ref_index):
    '''Adds all institutions specified by the given ref (dictionary containing article data).'''
    institutions = ref.get('institutions')
    if not institutions:
      return
    for (key, (institution_address, parent_orgs)) in institutions.items():
      institution_list = ([institution_address] + parent_orgs) if parent_orgs else [institution_address]
      institution_indices = map(self._add_institution, institution_list)
      for (institution_index, count) in Counter(institution_indices).items():
        self._add_unique_edge(ref_index, institution_index, count = count)

  def _add_grant_agency(self, grant_agency):
    '''Add a given grant agency name to the litnet if the grant agency doesn't already exist
    in the litnet. Returns its node index.'''
    grant_agency_index = self.grant_agency_to_v.get(grant_agency)
    if grant_agency_index == None:
      grant_agency_index = self.add_v(type='grantagency', label=grant_agency)
      self.grant_agency_to_v[grant_agency] = grant_agency_index
    return grant_agency_index

  def _add_grant_agencies(self, ref, ref_index):
    '''Adds all grant agencies specified by the given ref (dictionary containing article data).'''
    grant_agencies = ref.get('grantagencies')
    if not grant_agencies:
      return
    grant_agency_indices = map(self._add_grant_agency, grant_agencies)
    for (grant_agency_index, count) in Counter(grant_agency_indices).items():
      self._add_unique_edge(ref_index, grant_agency_index, count = count)

  def add_ref(self, ref, parent_index):
    '''Adds a ref (dictionary containing article data) to the litnet.
    Returns the corresponding article node index.'''
    ref_index = self._get_ref_index(ref)
    self._update_ref_vertex_dicts(ref, ref_index)
    self._add_unique_edge(parent_index, ref_index)

    self._add_ref_data(ref, ref_index)
    self._add_authors(ref, ref_index)
    self._add_institutions(ref, ref_index)
    self._add_grant_agencies(ref, ref_index)

    return ref_index

  def propagate_pubdates(self):
    '''Add the min pubdate from article nodes out to author, institution, and grantagency nodes.'''
    for refv in self.g.vs(type='article'):
      ref_pubdate = refv['pubdate']
      if ref_pubdate == None: continue
      for adj in refv.neighbors(mode = igraph.OUT):
        if adj['type'] in ['author', 'institution', 'grantagency']:
          adj_pubdate = adj['pubdate']
          if adj_pubdate == None or ref_pubdate < adj_pubdate:
            adj['pubdate'] = ref_pubdate

  def _replace_node_with(self, replacee, replacer):
    '''Redirects all edges going to replacee and points them
    to replacer. Removes replacee.'''
    replacee_idx = replacee.index
    replacer_idx = replacer.index
    for src_idx in self.g.neighbors(replacee_idx, mode = igraph.IN):
      self.g.add_edge(src_idx, replacer_idx)
      self.g.delete_edges(self.g.get_eid(src_idx, replacee_idx))
    for trg_idx in self.g.neighbors(replacee_idx, mode = igraph.OUT):
      self.g.add_edge(replacer_idx, trg_idx)
      self.g.delete_edges(self.g.get_eid(replacee_idx, trg_idx))

  def remove_dup_authors(self):
    '''Remove duplicate author nodes from the litnet.
    E.g. "pico a" and "pico ar" would be merged into the single node "pico ar".'''
    for authv in self.g.vs(type='author'):
      name_raw = authv['label']
      name_pieces = name_raw.split(' ')
      if len(name_pieces) != 2:
        continue
      last_name, first_initials = (name_pieces[0], name_pieces[1])
      n_initials = len(first_initials)
      if n_initials <= 1:
        continue
      first_initials_alts = map(lambda l: first_initials[:l], range(1, n_initials))
      for first_initial_alt in first_initials_alts:
        name_alt = ' '.join([last_name, first_initial_alt])
        dupvs = self.g.vs(type='author', label=name_alt)
        if len(dupvs) == 0:
          continue
        for dupv in dupvs:
          self._replace_node_with(dupv, authv)
