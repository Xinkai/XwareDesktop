# -*- coding: utf-8 -*-

# The contents of this file are subject to the BitTorrent Open Source License
# Version 1.1 (the License).  You may not copy or use this file, in either
# source code or executable form, except in compliance with the License.  You
# may obtain a copy of the License at http://www.bittorrent.com/license/.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Originally written by Petru Paler


class BTFailure(Exception):
    pass


def decode_int(x, f):
    f += 1
    newf = x.index(b'e', f)
    n = int(x[f:newf])
    if x[f] == ord('-'):
        if x[f + 1] == ord('0'):
            raise ValueError
    elif x[f] == ord('0') and newf != f + 1:
        raise ValueError
    return n, newf + 1


def decode_string(x, f):
    colon = x.index(b':', f)
    n = int(x[f:colon])
    if x[f] == ord('0') and colon != f + 1:
        raise ValueError
    colon += 1
    return x[colon:colon + n], colon + n


def decode_list(x, f):
    r, f = [], f + 1
    while x[f] != ord('e'):
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return r, f + 1


def decode_dict(x, f):
    r, f = dict(), f + 1
    while x[f] != ord('e'):
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return r, f + 1


decode_func = dict()
decode_func[ord('l')] = decode_list
decode_func[ord('d')] = decode_dict
decode_func[ord('i')] = decode_int
decode_func[ord('0')] = decode_string
decode_func[ord('1')] = decode_string
decode_func[ord('2')] = decode_string
decode_func[ord('3')] = decode_string
decode_func[ord('4')] = decode_string
decode_func[ord('5')] = decode_string
decode_func[ord('6')] = decode_string
decode_func[ord('7')] = decode_string
decode_func[ord('8')] = decode_string
decode_func[ord('9')] = decode_string


def bdecode(x):
    try:
        r, l = decode_func[x[0]](x, 0)
    except (IndexError, KeyError, ValueError):
        raise BTFailure("not a valid bencoded string")
    if l != len(x):
        raise BTFailure("invalid bencoded value (data after valid prefix)")
    return r
