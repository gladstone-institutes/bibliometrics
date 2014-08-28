def xpath_str(doc, path, ns = None):
  result = doc.xpath(path, namespaces=ns)
  return unicode(result[0]) if result else None

def xpath_strs(doc, path, ns = None):
  results = doc.xpath(path, namespaces=ns)
  return map(unicode, results)

def has_keys(d, *keys):
  for key in keys:
    if not key in d:
      return False
  return True
