#!/usr/bin/python

import sys

idmap = {
  'lf13':25,
  'ol12':26,
  'rw88':27,
  'bf68': 1,
  'bh27': 2,
  'dk76': 3,
  'cn61': 4,
  'xi27': 5,
  'ks38': 6,
  'yv98': 7,
  'dn20': 8,
  'ht02': 9,
  'nv60': 10,
  'eb04': 11,
  'xs62': 12,
  'kl93': 13,
  'zm36': 14,
  'dj41': 15,
  'lm28': 16,
  'ur54': 17,
  'kz65': 18,
  'ws81': 19,
  'ep13': 20,
  'sc83': 21,  
  'cw76': 24}

def anon_id(orig_id):
    id = orig_id[:4]
    return 'sub-%.2i' % idmap[id.strip().lower()]

if __name__ == '__main__':
    orig_id = sys.argv[1]
    if orig_id == 'list':
        print ' '.join(sorted(idmap.keys()))
    else:
        print anon_id(orig_id)
