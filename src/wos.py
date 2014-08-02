import re
import time
import suds
import ref
import lxml.etree

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
      institution_address = institution_tag.xpath("ns:full_address", namespaces=ns)[0].text

      self.institutions[i] = institution_address 

    self.authors = []
    num_authors = int(records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:names", namespaces=ns)[0].attrib['count'])
    for i in range(1, num_authors + 1):
      author_tag = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:names/ns:name[@seq_no='%d']" % i, namespaces=ns)[0]
      author_name = author_tag.xpath("ns:wos_standard/text()", namespaces=ns)[0]
      affiliation_indices = map(int, author_tag.attrib['addr_no'].split(' ')) if 'addr_no' in author_tag.attrib else None

      self.authors.append((author_name, affiliation_indices))

class WoSCitedRef(ref.Ref):
  def __init__(self, record):
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

class Client:
  def __init__(self):
    self.authclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl')
    session = self.authclient.service.authenticate()
    header = {'Cookie': ('SID="%s"' % session)}
    self.searchclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl')
    self.searchclient.set_options(headers=header)

  def close(self):
    self.authclient.service.closeSession()

  def search(self, author, title, journal=None, year=None):
    qp = self.searchclient.factory.create('queryParameters')
    qp.databaseId = 'WOS'
    qp.userQuery = 'TI=(%s) AND AU=(%s)' % (title, author)
    if journal:
      qp.userQuery += ' AND SO=(%s) AND PY=(%s)' % (journal, year)
    qp.queryLanguage = 'en'

    rp = self.searchclient.factory.create('retrieveParameters')
    rp.firstRecord = 1
    rp.count = 100

    time.sleep(1) # throttle requests
    results = self.searchclient.service.search(qp, rp)

    if not results.recordsFound == 1:
      return None

    records = lxml.etree.fromstring(results.records)
    wosref = WoSRef(records)
    wosref.citations = self.citations(wosref)

    #with open('%s.xml' % wosref.wosid, 'w') as f: f.write(results.records)

    return wosref

  def citations(self, ref):
    rp = self.searchclient.factory.create('retrieveParameters')
    rp.firstRecord = 1
    rp.count = 100

    citedrefs = []
    results = self.searchclient.service.citedReferences('WOS', ref.wosid, 'en', rp)
    for record in results.references:
      citedref = WoSCitedRef(record)
      if hasattr(citedref, 'authors_str') and hasattr(citedref, 'title'):
        citedrefs.append(citedref)
    return citedrefs
