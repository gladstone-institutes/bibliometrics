def xpath_str(doc, path, ns):
  result = doc.xpath(path, namespaces=ns)
  return unicode(result[0]) if result else None

def xpath_strs(doc, path, ns):
  results = doc.xpath(path, namespaces=ns)
  return map(unicode, results)
