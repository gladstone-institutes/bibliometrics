import re
import time
import suds
import lxml.etree
import os.path
import pickle
import datetime
import string
from util import xpath_str, xpath_strs

_date_re = re.compile(r'(?P<yr>\d{4})-(?P<mon>\d{2})-(?P<day>\d{2})')
_non_alphanum_re = re.compile(r'[^\w\s]+')
def _convert_wos_record(record, ns):
  """
  Takes an XML tree of a single WoS record and returns a dictionary
  representing the record's information.

  Args:
    record: An XML tree, where the root is the 'REC' tag
    ns: A dictionary that contains the key 'ns' whose value is the null XML namespace.

  Returns:
    A dictionary representing the record's information
    with the following keys and value types:
      wosid:        unicode
      title:        unicode
      journal:      unicode
      issue:        unicode
      volume:       unicode
      pubdate:      int
      institutions: {int: (unicode, [unicode])}
      authors:      [(unicode, [int])]
  """

  r = dict()
  r['wosid'] = xpath_str(record, "ns:UID/text()", ns)
  r['title'] = xpath_str(record, "ns:static_data/ns:summary/ns:titles/ns:title[@type='item']/text()",ns)
  r['journal'] = xpath_str(record, "ns:static_data/ns:summary/ns:titles/ns:title[@type='source']/text()", ns)
  pubinfo = record.xpath("ns:static_data/ns:summary/ns:pub_info", namespaces=ns)[0]
  (r['issue'], r['volume'], pubdate) = (pubinfo.attrib.get('issue'), pubinfo.attrib.get('vol'), pubinfo.attrib.get('sortdate'))
  if pubdate:
    m = _date_re.match(pubdate)
    r['pubdate'] = int(m.group('yr') + m.group('mon') + m.group('day'))

  r['institutions'] = {}
  num_institutions = int(record.xpath("ns:static_data/ns:fullrecord_metadata/ns:addresses", namespaces=ns)[0].attrib['count'])
  for i in range(1, num_institutions + 1):
    institution_tag = record.xpath("ns:static_data/ns:fullrecord_metadata/ns:addresses/ns:address_name/ns:address_spec[@addr_no='%d']" % i, namespaces=ns)[0]
    address = xpath_str(institution_tag, "ns:full_address/text()", ns)
    organizations = xpath_strs(institution_tag, "ns:organizations/ns:organization/text()", ns)

    r['institutions'][i] = (address, organizations)

  r['authors'] = []
  num_authors = int(record.xpath("ns:static_data/ns:summary/ns:names", namespaces=ns)[0].attrib['count'])
  for i in range(1, num_authors + 1):
    author_tag = record.xpath("ns:static_data/ns:summary/ns:names/ns:name[@seq_no='%d']" % i, namespaces=ns)[0]
    author_name = xpath_str(author_tag, "ns:wos_standard/text()", ns)
    if author_name == None: continue
    affiliation_indices = map(int, author_tag.attrib['addr_no'].split(' ')) if 'addr_no' in author_tag.attrib else None

    r['authors'].append((author_name, affiliation_indices))

  return r

def _convert_wos_biblio_record(record):
  r = {}
  if 'citedAuthor' in record:
    r['authors'] = [(unicode(record['citedAuthor']), None)]
  if 'timesCited' in record:
    r['citcount'] = int(record['timesCited'])
  if 'year' in record:
    r['year'] = unicode(record['year'])
  if 'page' in record:
    r['firstpage'] = unicode(record['page'])
  if 'volume' in record:
    r['volume'] = unicode(record['volume'])
  if 'citedTitle' in record:
    r['title'] = unicode(record['citedTitle'])
  if 'citedWork' in r:
    r['journal'] = unicode(record['citedWork'])
  return r

_cache_path = '.wos-cache.pkl'
_wos_title_bad_chars_re = re.compile(r'[\"\'\(\)\[\]\?\*\!\<\>\=\$\-\.]')

class Client:
  def __init__(self):
    self._sign_in()
    self.cache = {}
    if os.path.isfile(_cache_path):
      with open(_cache_path, 'rb') as cache_file:
        try:
          self.cache = pickle.load(cache_file)
        except Exception as e:
          print 'Failed to load cache:', str(e)

  def _sign_in(self):
    self.authclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl')
    session = self.authclient.service.authenticate()
    header = {'Cookie': ('SID="%s"' % session)}
    self.searchclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl')
    self.searchclient.set_options(headers=header)

    self.last_query_time = datetime.datetime.now()

  def _sign_out(self):
    try:
      self.authclient.service.closeSession()
    except suds.WebFault:
      pass

  def close(self):
    self._flush_cache()
    self._sign_out()
    
  def _flush_cache(self):
    with open(_cache_path, 'wb') as cache_file:
      pickle.dump(self.cache, cache_file)

  def _throttled_query(self, query_func):
    time_now = datetime.datetime.now()
    delta_sec = (time_now - self.last_query_time).total_seconds()
    if delta_sec < 1.0:
      time.sleep(1.0 - delta_sec)
    self.last_query_time = datetime.datetime.now()
    return query_func()

  def _paged_query(self, query_func, max_pages = None, records_per_page = 100):
    rp = self.searchclient.factory.create('retrieveParameters')
    rp.firstRecord = 1
    rp.count = records_per_page

    results = []
    first_page = self._throttled_query(lambda: query_func(rp))
    results.append(first_page)

    num_possible_pages = (first_page.recordsFound / records_per_page) + 1
    effective_num_pages = min(num_possible_pages, max_pages) if max_pages else num_possible_pages
    for i in range(effective_num_pages - 1):
      rp.firstRecord += records_per_page
      page = self._throttled_query(lambda: query_func(rp))
      results.append(page)

    return results

  def _cache(func):
    def inner(self, arg):
      cache_key = func.__name__ + ':' + arg
      if cache_key in self.cache:
        return self.cache[cache_key]
      result = func(self, arg)
      self.cache[cache_key] = result
      return result
    return inner

  @_cache
  def _search(self, userQuery):
    print userQuery
    qp = self.searchclient.factory.create('queryParameters')
    qp.databaseId = 'WOS'
    qp.userQuery = userQuery
    qp.queryLanguage = 'en'

    query_func = lambda rp: self.searchclient.service.search(qp, rp)
    pages = self._paged_query(query_func, 1)

    record = pages[0].records
    doc = lxml.etree.fromstring(record)
    ns = {'ns': doc.nsmap[None]}
    results = []
    for record in doc.xpath('/ns:records/ns:REC', namespaces=ns):
      results.append(_convert_wos_record(record, ns))
    return results

  def _fix_title_pir(self, title):
    title_lower = title.lower()
    title_alphanum_only = _non_alphanum_re.sub('', title_lower)
    if title_alphanum_only == 'notavailable':
      return []
    if '"' in title:
      title = title.replace('"', '')
    if 'near ' in title_lower or ' near' in title_lower or 'same ' in title_lower or ' same' in title_lower or '=' in title or '>' in title or '<' in title or ' not ' in title_lower:
      title = '"' + title + '"'
    title_fixed = title.replace('(', ' ').replace(')', ' ').replace('?', ' ').replace('[', ' ').replace(']', ' ')
    return title_fixed
  
  def _fix_title(self, title):
    return '"' + _wos_title_bad_chars_re.sub(' ', title) + '"'

  def _fix_author(self, author):
    if not author:
      return author
    author_lower = author.lower()
    author_alphanum_only = _non_alphanum_re.sub('', author_lower)
    if ' or' in author_alphanum_only or 'or ' in author_alphanum_only:
      return '"' + author_alphanum_only + '"'
    else:
      return author

  def search(self, author, title, journal=None, year=None):
    title_fixed = self._fix_title(title)
    author_fixed = self._fix_author(author)
    userQuery = 'TI=(%s) AND AU=(%s)' % (title_fixed, author_fixed)
    if journal:
      userQuery += ' AND SO=(%s)' % journal
    if year:
      userQuery += ' AND PY=(%s)' % year

    results = self._search(userQuery)
    return results

  @_cache
  def _biblio(self, wosid):
    query_func = lambda rp: self.searchclient.service.citedReferences('WOS', wosid, 'en', rp)
    pages = self._paged_query(query_func)
    results = []
    for page in pages:
      if not hasattr(page, 'references'): continue
      for record in page.references:
        results.append(_convert_wos_biblio_record(record))
    return results

  def biblio(self, wosref):
    results = self._biblio(wosref['wosid'])
    records = [record for record in results if 'authors' in record and 'title' in record]
    return records

  @_cache
  def _citations(self, wosid):
    timespan = self.searchclient.factory.create('timeSpan')
    timespan.begin = datetime.date(1900, 1, 1)
    timespan.end = datetime.date.today()

    edition = self.searchclient.factory.create('editionDesc')
    edition.collection = 'WOS'
    edition.edition = 'SCI'

    query_func = lambda rp: self.searchclient.service.citingArticles('WOS', wosid, [edition], timespan, 'en', rp)
    pages = self._paged_query(query_func)
    citations = []
    for page in pages:
      doc = lxml.etree.fromstring(page.records)
      ns = {'ns': doc.nsmap[None]}
      for record in doc.xpath('/ns:records/ns:REC', namespaces=ns):
        citations.append(_convert_wos_record(record, ns))

    return citations

  def citations(self, wosref):
    results = self._citations(wosref['wosid'])
    return results
