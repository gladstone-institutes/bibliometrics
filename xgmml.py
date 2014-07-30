import lxml.etree
from lxml.builder import E
import codecs
import types

def write(G, path):
  xG = E.graph({'label': 'Network', 'directed': '1'}, namespace='http://www.cs.rpi.edu/XGMML')
  nodes = G.nodes()
  for node_id in range(len(nodes)):
    node = nodes[node_id]
    xnode = E.node({'id': str(node_id), 'label': node})
    for k, v in G.node[node].items():
      if type(v) == types.UnicodeType or type(v) == types.StringType:
        xattr = E.att({'name': k, 'value': v, 'type': 'string'})
      elif type(v) == types.IntType:
        xattr = E.att({'name': k, 'value': str(v), 'type': 'integer'})
      elif type(v) == types.ListType:
        xattr = E.att({'name': k, 'type': 'list'})
        for val in v:
          if type(val) == types.UnicodeType or type(val) == types.StringType:
            xval = E.att({'name': k, 'value': val, 'type': 'string'})
          elif type(val) == types.IntType:
            xval = E.att({'name': k, 'value': str(val), 'type': 'integer'})
          else:
            raise Exception('Cannot serialize attribute of type %s of node %s' % (type(val), node))
          xattr.append(xval)
      else:
        raise Exception('Cannot serialize attribute of type %s of node %s' % (type(v), node))
      xnode.append(xattr)
    xG.append(xnode)

  for src in G.edge:
    src_id = nodes.index(src)
    for trg in G.edge[src]:
      trg_id = nodes.index(trg)
      xedge = E.edge({'source': str(src_id), 'target': str(trg_id)})
      xG.append(xedge)

  with codecs.open(path, 'w', 'UTF-8') as f:
    f.write(lxml.etree.tostring(xG, pretty_print=True, xml_declaration=True, standalone=True))
