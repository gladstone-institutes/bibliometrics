from xml.etree.ElementTree import ElementTree
import lxml.etree
from lxml.builder import E
import codecs
import types

def _serialize_attrs(elem):
  xattrs = list()
  for k, v in elem.attributes().items():
    if k == 'label':
      k = 'name'
    if v == None:
      continue
    elif isinstance(v, basestring):
      xattr = E.att({'name': k, 'value': unicode(v), 'type': 'string'})
    elif type(v) == types.IntType:
      xattr = E.att({'name': k, 'value': str(v), 'type': 'integer'})
    elif type(v) == types.FloatType:
      xattr = E.att({'name': k, 'value': str(v), 'type': 'real'})
    elif type(v) == types.ListType:
      xattr = E.att({'name': k, 'type': 'list'})
      for val in v:
        if isinstance(val, basestring):
          xval = E.att({'name': k, 'value': unicode(val), 'type': 'string'})
        elif type(val) == types.IntType:
          xval = E.att({'name': k, 'value': str(val), 'type': 'integer'})
        else:
          raise Exception('Cannot serialize attribute of type %s of %s' % (type(val), elem))
        xattr.append(xval)
    else:
      raise Exception('Cannot serialize attribute of type %s of %s' % (type(v), elem))
    xattrs.append(xattr)
  return xattrs

def _graph_to_xml_tree(g, name):
  xg = E.graph({'label': name, 'directed': '1'}, namespace='http://www.cs.rpi.edu/XGMML')
  for v in g.vs:
    xv = E.node({'id': str(v.index)})
    xattrs = _serialize_attrs(v)
    xv.extend(xattrs)
    xg.append(xv)

  for e in g.es:
    (src, trg) = e.tuple
    xe = E.edge({'source': str(src), 'target': str(trg)})
    xattrs = _serialize_attrs(e)
    xe.extend(xattrs)
    xg.append(xe)

  return xg

def write(g, name, path):
  xg = _graph_to_xml_tree(g, name)
  t = ElementTree(xg)
  t.write(path, xml_declaration=True, encoding='UTF-8')
