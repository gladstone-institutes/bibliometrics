import tempfile
import urllib
import zipfile
import lxml.etree
import os
import dateutil.parser
import ref

class ClinicalTrial:
  def __init__(self, doc):
    self.nctid = doc.xpath('/clinical_study/id_info/nct_id/text()')[0]
    self.title = doc.xpath('/clinical_study/official_title/text() | /clinical_study/brief_title/text()')[0]
    self.refs = []
    for reftag in doc.xpath('/clinical_study/reference | /clinical_study/results_reference'):
      cseref = reftag.xpath('citation/text()')[0]
      pmid = reftag.xpath('PMID/text()')
      r = ref.CseRef(cseref)
      if pmid:
        r.pmid = pmid[0]
      self.refs.append(r)

    completion_date_str = doc.xpath('/clinical_study/completion_date/text()')
    self.completion_date = dateutil.parser.parse(completion_date_str[0]) if completion_date_str else None

class Client:
  def __init__(self):
    pass
  
  def search(self, query):
    (_, tmppath) = tempfile.mkstemp(prefix=('%s-clinical-trials' % query), suffix='.zip', text='False')
    with open(tmppath, 'wb') as tmpfile:
      tmpfile.write(urllib.urlopen('http://clinicaltrials.gov/search?term=%s&studyxml=true' % query).read())
    trials = []
    with zipfile.ZipFile(tmppath, 'r') as archive:
      for name in archive.namelist():
        with archive.open(name, 'r') as docfile:
          doc = lxml.etree.parse(docfile)
          trial = ClinicalTrial(doc)
          trials.append(trial)
    os.remove(tmppath)
    return trials
    

