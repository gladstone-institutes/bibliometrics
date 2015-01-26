import sys
import types
import igraph
from xml.etree.ElementTree import ElementTree
import lxml.etree
from lxml.builder import E

def _serialize_attrs(elem):
  xattrs = list()
  for k, v in elem.attributes().items():
    if k == 'label':
      k = 'name'
    if v == None:
      continue
    elif isinstance(v, basestring):
      xattr = E.att({'name': k, 'value': unicode(v), 'type': 'string'})
    elif isinstance(v, types.IntType):
      xattr = E.att({'name': k, 'value': str(v), 'type': 'integer'})
    elif isinstance(v, types.FloatType):
      xattr = E.att({'name': k, 'value': str(v), 'type': 'real'})
    elif isinstance(v, types.ListType):
      xattr = E.att({'name': k, 'type': 'list'})
      for val in v:
        if isinstance(val, basestring):
          xval = E.att({'name': k, 'value': unicode(val), 'type': 'string'})
        elif isinstance(val, types.IntType):
          xval = E.att({'name': k, 'value': str(val), 'type': 'integer'})
        else:
          raise Exception('Cannot serialize attribute "%s" of type %s for %s' % (k, type(val), elem))
        xattr.append(xval)
    elif isinstance(v, types.DictType):
      xattr = E(k, v)
    else:
      raise Exception('Cannot serialize attribute "%s" of type %s for %s' % (k, type(v), elem))
    xattrs.append(xattr)
  return xattrs

def _graph_to_xml_tree(g):
  xg = E.graph({'label': g['name'], 'directed': '1'}, namespace='http://www.cs.rpi.edu/XGMML')
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

def write(g, path):
  '''Builds an XGMML file from the given graph object.
  The topology of the network will be built as per the given graph.

  Node and edge attributes can be of the following types:
    string, int, float, list of strings, list of ints, dictionary of strings.

  Dictionary values are treated specially. The attribute name will become
  its own XML tag, and the dictionary's keys and values will become
  attributes for the XML tag. This is used in litnet.py for building
  the "graphics" tag, which sets visual properties for nodes and edges.

  The "label" attribute is renamed to "name".
  '''

  xg = _graph_to_xml_tree(g)
  t = ElementTree(xg)
  t.write(path, xml_declaration=True, encoding='UTF-8')

def main(input_file_path, output_file_path):
  with open(input_file_path, 'rb') as input_file:
    g = igraph.Graph.Read(input_file, format='picklez')
    write(g, output_file_path)

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
