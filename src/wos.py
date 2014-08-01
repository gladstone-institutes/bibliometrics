import requests
import lxml.html

class Client:
  def __init__(self):
    self.headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'
      }
    self.session = requests.Session()
    self.session.get('http://isiknowledge.com', headers=self.headers)
    self.sid = self.session.cookies['SID']

  def search(self, title, author):
    data = self._search_form(title, author)
    resp = self.session.post('http://apps.webofknowledge.com/UA_GeneralSearch.do', headers=self.headers, data=data)
    doc = lxml.html.document_fromstring(resp.content)
    return doc

  def _search_form(self, title, author):
    return { 
        'SID': self.sid,
        'sa_params': 'UA||' + self.sid + '|http://apps.webofknowledge.com|\'',
        'value(input1)': title,
        'value(input2)': author,

        'fieldCount': '2',
        'value(select1)': 'TI',
        'value(hidInput1)': '', 
        'value(bool_1_2)': 'AND',
        'value(select2)': 'AU',
        'value(hidInput2)': '', 

        'action': 'search',
        'product': 'UA',
        'search_mode': 'GeneralSearch',
        'max_field_count': '25',
        'max_field_notice': 'Notice',
        'input_invalid_notice': 'Invalid',
        'exp_notice': 'Search Error',
        'input_invalid_notice_limits': 'Note: Fields',
        'formUpdated': 'true',
        'x': '64',
        'y': '30',
        'limitStatus': 'expanded',
        'ss_lemmatization': 'On',
        'ss_spellchecking': 'Suggest',
        'SinceLastVisit_UTC': '', 
        'SinceLastVisit_DATE': '', 
        'period': 'Range Selection',
        'range': 'ALL',
        'startYear': '1898',
        'endYear': '2014',
        'ssStatus': 'display:none',
        'ss_showsuggestions': 'ON',
        'ss_query_language': 'auto',
        'ss_numDefaultGeneralSearchFields': '1',
        'rs_sort_by': 'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A'
      }
