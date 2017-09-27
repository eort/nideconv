#!/usr/bin/python

import sys

idmap = {
  'lf13': 1,
  'dn20': 2,
  'ol12': 3,
  'rw88': 4
}

def anon_id(orig_id):
    id = orig_id[:4]
    return 'sub-%.2i' % idmap[id.strip().lower()]

if __name__ == '__main__':
    orig_id = sys.argv[1]
    if orig_id == 'list':
        print ' '.join(sorted(idmap.keys()))
    else:
        print anon_id(orig_id)
