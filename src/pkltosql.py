import sqlite3
import cPickle as pickle

cache_file = open('.wos-cache.pkl', 'rb')
srcdict = pickle.load(cache_file)
cache_file.close()
print '{:,} items in dictionary.'.format(len(srcdict))

srckvs = ([unicode(k), sqlite3.Binary(pickle.dumps(v, pickle.HIGHEST_PROTOCOL))] for (k, v) in srcdict.iteritems())

dbcon = sqlite3.connect('.wos-cache.sqlite')
dbcon.execute('create table cache(ckey text, cval blob)')
dbcon.executemany('insert into cache values(?, ?)', srckvs)
dbcon.commit()
dbcon.close()
