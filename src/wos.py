import suds
import ref
import lxml.etree

class WoSRef(ref.Ref):
  def __init__(self, records):
    ns = {'ns': records.nsmap[None]}

    self.wosid = records.xpath("/ns:records/ns:REC/ns:UID/text()", namespaces=ns)[0]
    self.title = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:titles/ns:title[@type='item']/text()", namespaces=ns)[0]
    self.journal = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:titles/ns:title[@type='source']/text()", namespaces=ns)[0]
    pubinfo = records.xpath("/ns:records/ns:REC/ns:static_data/ns:summary/ns:pub_info", namespaces=ns)[0]
    (self.issue, self.volume, self.pubdate) = (pubinfo.attrib['issue'], pubinfo.attrib['vol'], pubinfo.attrib['sortdate'])

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
      affiliation_indices = map(int, author_tag.attrib['addr_no'].split(' '))

      self.authors.append((author_name, affiliation_indices))

class Client:
  def __init__(self):
    self.authclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl')
    session = self.authclient.service.authenticate()
    header = {'Cookie': ('SID="%s"' % session)}
    self.searchclient = suds.client.Client('http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl')
    self.searchclient.set_options(headers=header)

  def close(self):
    self.authclient.service.closeSession()

  def search(self, author, title):
    qp = self.searchclient.factory.create('queryParameters')
    qp.databaseId = 'WOS'
    qp.userQuery = 'TI=(%s) AND AU=(%s)' % (title, author)
    qp.queryLanguage = 'en'

    rp = self.searchclient.factory.create('retrieveParameters')
    rp.firstRecord = 1
    rp.count = 100

    results = self.searchclient.service.search(qp, rp)

    if results.recordsFound == 0:
      print 'Nothing found'
      return None
    elif results.recordsFound > 1:
      print 'Ambiguous results'
      return None

    records = lxml.etree.fromstring(results.records)
    return WoSRef(records)
