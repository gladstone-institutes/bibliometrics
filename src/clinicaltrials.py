import tempfile
import urllib
import zipfile
import lxml.etree
import os
import dateutil.parser
import refparse
from util import xpath_str

def _parse_clinical_trial(doc):
  t = {}
  t['nctid'] = xpath_str(doc, '/clinical_study/id_info/nct_id/text()')
  t['title'] = xpath_str(doc, '/clinical_study/official_title/text() | /clinical_study/brief_title/text()')
  refs = []
  for reftag in doc.xpath('/clinical_study/reference | /clinical_study/results_reference'):
    cseref_str = xpath_str(reftag, 'citation/text()')
    ref = refparse.parse_cse_ref(cseref_str)
    pmid = xpath_str(reftag, 'PMID/text()')
    if pmid:
      ref['pmid'] = pmid
    refs.append(ref)
  t['biblio'] = refs

  completion_date_str = xpath_str(doc, '/clinical_study/completion_date/text()')
  #completion_date = dateutil.parser.parse(completion_date_str) if completion_date_str else None
  completion_date = completion_date_str
  t['completion_date'] = completion_date 
  
  return t

class Client:
  def __init__(self):
    pass
  
  def search(self, query):
    '''Takes a drug name and returns a list of dictionaries. Each dictionary
    contains information about the clinical trial:
    {
      "nctid": web service ID for this clinical trial
      "title": Name of the clinical trial
      "biblio": List of strings containing PMIDs
      "completion_date": A string representing when the clinical trial finished (if at all)
    }'''
    (_, tmppath) = tempfile.mkstemp(prefix=('%s-clinical-trials' % query), suffix='.zip', text='False')
    with open(tmppath, 'wb') as tmpfile:
      tmpfile.write(urllib.urlopen('http://clinicaltrials.gov/search?term=%s&studyxml=true' % query).read())
    trials = []
    with zipfile.ZipFile(tmppath, 'r') as archive:
      for name in archive.namelist():
        with archive.open(name, 'r') as docfile:
          doc = lxml.etree.parse(docfile)
          trial = _parse_clinical_trial(doc)
          trials.append(trial)
    os.remove(tmppath)
    return trials
