import re
import time
import suds
import ref
import lxml.etree
import os.path
import pickle

_date_re = re.compile(r'(?P<yr>\d{4})-(?P<mon>\d{2})-(?P<day>\d{2})')

class WoSRef(ref.Ref):
  def __init__(self, records):
    ns = {'ns': records.nsmap[None]}

    self.wosid = records.xpath("/ns:records/ns:REC/ns:UID/text()", namespaces=ns)[0]
    self.title = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:titles/ns:title[@type='item']/text()", namespaces=ns)[0]
    self.journal = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:titles/ns:title[@type='source']/text()", namespaces=ns)[0]
    pubinfo = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:pub_info", namespaces=ns)[0]
    (self.issue, self.volume, self.pubdate) = (pubinfo.attrib.get('issue'), pubinfo.attrib.get('vol'), pubinfo.attrib.get('sortdate'))
    if self.pubdate:
      m = _date_re.match(self.pubdate)
      self.pubdate = int(m.group('yr') + m.group('mon') + m.group('day'))

    self.institutions = {}
    num_institutions = int(records.xpath("/ns:records/ns:REC/ns:static_data/ns:fullrecord_metadata/ns:addresses", namespaces=ns)[0].attrib['count'])
    for i in range(1, num_institutions + 1):
      institution_tag = records.xpath("/ns:records/ns:REC/ns:static_data/ns:fullrecord_metadata/ns:addresses/ns:address_name/ns:address_spec[@addr_no='%d']" % i, namespaces=ns)[0]
      address = institution_tag.xpath("ns:full_address", namespaces=ns)[0].text
      organizations = map(unicode, institution_tag.xpath("ns:organizations/ns:organization/text()", namespaces=ns))

      self.institutions[i] = (address, organizations)

    self.authors = []
    num_authors = int(records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:names", namespaces=ns)[0].attrib['count'])
    for i in range(1, num_authors + 1):
      author_tag = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:names/ns:name[@seq_no='%d']" % i, namespaces=ns)[0]
      author_name = author_tag.xpath("ns:wos_standard/text()", namespaces=ns)[0]
      affiliation_indices = map(int, author_tag.attrib['addr_no'].split(' ')) if 'addr_no' in author_tag.attrib else None

      self.authors.append((author_name, affiliation_indices))

class WoSCitedRef(ref.Ref):
  def __init__(self, record_dict):
    record = ref.Ref()
    record.__dict__.update(record_dict)
    if hasattr(record, 'citedAuthor'):
      self.authors_str = record.citedAuthor
    if hasattr(record, 'timesCited'):
      self.citcount = int(record.timesCited)
    if hasattr(record, 'year'):
      self.year = record.year
    if hasattr(record, 'page'):
      self.firstpage = record.page
    if hasattr(record, 'volume'):
      self.volume = record.volume
    if hasattr(record, 'citedTitle'):
      self.title = record.citedTitle
    if hasattr(record, 'citedWork'):
      self.journal = record.citedWork

  def first_author(self):
    return self.authors_str

def _serializable(obj):
  return {k: v for (k, v) in obj.__dict__.items() if not k.startswith('__')}

_cache_path = '.wos-cache.pkl'

class Client:
  def __init__(self):
    self.authclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl')
    session = self.authclient.service.authenticate()
    header = {'Cookie': ('SID="%s"' % session)}
    self.searchclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl')
    self.searchclient.set_options(headers=header)
    
    self.cache = {}
    if os.path.isfile(_cache_path):
      with open(_cache_path, 'rb') as cache_file:
        try:
          self.cache = pickle.load(cache_file)
        except Exception as e:
          print 'Failed to load cache:', str(e)

  def close(self):
    self.authclient.service.closeSession()
    
  def _flush_cache(self):
    with open(_cache_path, 'wb') as cache_file:
      pickle.dump(self.cache, cache_file)

  def _cached_search(self, userQuery):
    cache_key = 'search:%s' % userQuery
    if cache_key in self.cache:
      return self.cache[cache_key]

    qp = self.searchclient.factory.create('queryParameters')
    qp.databaseId = 'WOS'
    qp.userQuery = userQuery
    qp.queryLanguage = 'en'

    rp = self.searchclient.factory.create('retrieveParameters')
    rp.firstRecord = 1
    rp.count = 100

    time.sleep(1) # throttle requests
    results_raw = self.searchclient.service.search(qp, rp)

    results = _serializable(results_raw)
    self.cache[cache_key] = results
    self._flush_cache()
    return results

  def search(self, author, title, journal=None, year=None):
    title_fixed = title.replace('(', ' ').replace(')', ' ')
    userQuery = 'TI=(%s) AND AU=(%s)' % (title_fixed, author)
    if journal:
      userQuery += ' AND SO=(%s) AND PY=(%s)' % (journal, year)

    results = self._cached_search(userQuery)
    if not results['recordsFound'] == 1:
      return None

    records = lxml.etree.fromstring(results['records'])
    wosref = WoSRef(records)
    wosref.citations = self.citations(wosref)

    #with open('%s.xml' % wosref.wosid, 'w') as f: f.write(results['records'])

    return wosref

  def _cached_citations(self, wosid):
    cache_key = 'citations:%s' % wosid
    if cache_key in self.cache:
      return self.cache[cache_key]

    rp = self.searchclient.factory.create('retrieveParameters')
    rp.firstRecord = 1
    rp.count = 100

    results_raw = self.searchclient.service.citedReferences('WOS', wosid, 'en', rp)
    results = map(_serializable, results_raw.references)

    self.cache[cache_key] = results
    self._flush_cache()

    return results

  def citations(self, ref):
    results = self._cached_citations(ref.wosid)
    citedrefs = []
    for record in results:
      citedref = WoSCitedRef(record)
      if hasattr(citedref, 'authors_str') and hasattr(citedref, 'title'):
        citedrefs.append(citedref)
    return citedrefs
