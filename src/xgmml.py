from xml.etree.ElementTree import ElementTree
import lxml.etree
from lxml.builder import E
import suds
import codecs
import types

def _serialize_attrs(d, node):
  xattrs = list()
  for k, v in d.items():
    if v == None:
      continue
    elif isinstance(v, basestring):
      xattr = E.att({'name': k, 'value': unicode(v), 'type': 'string'})
    elif type(v) == types.IntType:
      xattr = E.att({'name': k, 'value': str(v), 'type': 'integer'})
    elif type(v) == types.ListType:
      xattr = E.att({'name': k, 'type': 'list'})
      for val in v:
        if isinstance(val, basestring):
          xval = E.att({'name': k, 'value': unicode(val), 'type': 'string'})
        elif type(val) == types.IntType:
          xval = E.att({'name': k, 'value': str(val), 'type': 'integer'})
        else:
          raise Exception('Cannot serialize attribute of type %s of node %s' % (type(val), node))
        xattr.append(xval)
    else:
      raise Exception('Cannot serialize attribute of type %s of node %s' % (type(v), node))
    xattrs.append(xattr)
  return xattrs


def write(G, name, path):
  xG = E.graph({'label': name, 'directed': '1'}, namespace='http://www.cs.rpi.edu/XGMML')
  nodes = G.nodes()
  for node_id in range(len(nodes)):
    node = nodes[node_id]
    xnode = E.node({'id': str(node_id), 'label': node})
    xattrs = _serialize_attrs(G.node[node], node)
    xnode.extend(xattrs)
    xG.append(xnode)

  for src in G.edge:
    src_id = nodes.index(src)
    for trg in G.edge[src]:
      trg_id = nodes.index(trg)
      xedge = E.edge({'source': str(src_id), 'target': str(trg_id)})
      xG.append(xedge)

  t = ElementTree(xG)
  t.write(path, xml_declaration=True, encoding='UTF-8')
