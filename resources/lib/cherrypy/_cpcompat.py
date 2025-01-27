"""Compatibility code for using CherryPy with various versions of Python.

CherryPy 3.2 is compatible with Python versions 2.6+. This module provides a
useful abstraction over the differences between Python versions, sometimes by
preferring a newer idiom, sometimes an older one, and sometimes a custom one.

In particular, Python 2 uses str and '' for byte strings, while Python 3
uses str and '' for unicode strings. We will call each of these the 'native
string' type for each version. Because of this major difference, this module
provides
two functions: 'ntob', which translates native strings (of type 'str') into
byte strings regardless of Python version, and 'ntou', which translates native
strings to unicode strings. This also provides a 'BytesIO' name for dealing
specifically with bytes, and a 'StringIO' name for dealing with native strings.
It also provides a 'base64_decode' function with native strings as input and
output.
"""
import os
import re
import sys
import threading

import six

if six.PY3:
    def ntob(n, encoding='ISO-8859-1'):
        """Return the given native string as a byte string in the given
        encoding.
        """
        assert_native(n)
        # In Python 3, the native string type is unicode
        return n.encode(encoding)

    def ntou(n, encoding='ISO-8859-1'):
        """Return the given native string as a unicode string with the given
        encoding.
        """
        assert_native(n)
        # In Python 3, the native string type is unicode
        return n

    def tonative(n, encoding='ISO-8859-1'):
        """Return the given string as a native string in the given encoding."""
        # In Python 3, the native string type is unicode
        if isinstance(n, bytes):
            return n.decode(encoding)
        return n
else:
    # Python 2
    def ntob(n, encoding='ISO-8859-1'):
        """Return the given native string as a byte string in the given
        encoding.
        """
        assert_native(n)
        # In Python 2, the native string type is bytes. Assume it's already
        # in the given encoding, which for ISO-8859-1 is almost always what
        # was intended.
        return n

    def ntou(n, encoding='ISO-8859-1'):
        """Return the given native string as a unicode string with the given
        encoding.
        """
        assert_native(n)
        # In Python 2, the native string type is bytes.
        # First, check for the special encoding 'escape'. The test suite uses
        # this to signal that it wants to pass a string with embedded \uXXXX
        # escapes, but without having to prefix it with u'' for Python 2,
        # but no prefix for Python 3.
        if encoding == 'escape':
            return unicode(
                re.sub(r'\\u([0-9a-zA-Z]{4})',
                       lambda m: unichr(int(m.group(1), 16)),
                       n.decode('ISO-8859-1')))
        # Assume it's already in the given encoding, which for ISO-8859-1
        # is almost always what was intended.
        return n.decode(encoding)

    def tonative(n, encoding='ISO-8859-1'):
        """Return the given string as a native string in the given encoding."""
        # In Python 2, the native string type is bytes.
        if isinstance(n, unicode):
            return n.encode(encoding)
        return n


def assert_native(n):
    if not isinstance(n, str):
        raise TypeError("n must be a native str (got %s)" % type(n).__name__)

try:
    # Python 3.1+
    from base64 import decodebytes as _base64_decodebytes
except ImportError:
    # Python 3.0-
    # since CherryPy claims compability with Python 2.3, we must use
    # the legacy API of base64
    from base64 import decodestring as _base64_decodebytes


def base64_decode(n, encoding='ISO-8859-1'):
    """Return the native string base64-decoded (as a native string)."""
    if isinstance(n, six.text_type):
        b = n.encode(encoding)
    else:
        b = n
    b = _base64_decodebytes(b)
    if str is six.text_type:
        return b.decode(encoding)
    else:
        return b


try:
    sorted = sorted
except NameError:
    def sorted(i):
        i = i[:]
        i.sort()
        return i

try:
    reversed = reversed
except NameError:
    def reversed(x):
        i = len(x)
        while i > 0:
            i -= 1
            yield x[i]

try:
    # Python 3
    from urllib.parse import urljoin, urlencode
    from urllib.parse import quote, quote_plus
    from urllib.request import unquote, urlopen
    from urllib.request import parse_http_list, parse_keqv_list
except ImportError:
    # Python 2
    from urlparse import urljoin
    from urllib import urlencode, urlopen
    from urllib import quote, quote_plus
    from urllib import unquote
    from urllib2 import parse_http_list, parse_keqv_list

try:
    from threading import local as threadlocal
except ImportError:
    from cherrypy._cpthreadinglocal import local as threadlocal

iteritems = lambda d: d.items()
copyitems = lambda d: list(d.items())

iterkeys = lambda d: d.keys()
copykeys = lambda d: list(d.keys())

itervalues = lambda d: d.values()
copyvalues = lambda d: list(d.values())

import builtins

from http.cookies import SimpleCookie, CookieError
from http.client import BadStatusLine, HTTPConnection, IncompleteRead
from http.client import NotConnected
from http.server import BaseHTTPRequestHandler

# Some platforms don't expose HTTPSConnection, so handle it separately
if six.PY3:
    try:
        from http.client import HTTPSConnection
    except ImportError:
        # Some platforms which don't have SSL don't expose HTTPSConnection
        HTTPSConnection = None
else:
    try:
        from httplib import HTTPSConnection
    except ImportError:
        HTTPSConnection = None

try:
    # Python 2
    xrange = xrange
except NameError:
    # Python 3
    xrange = range

import threading
if hasattr(threading.Thread, "daemon"):
    # Python 2.6+
    def get_daemon(t):
        return t.daemon

    def set_daemon(t, val):
        t.daemon = val
else:
    def get_daemon(t):
        return t.isDaemon()

    def set_daemon(t, val):
        t.setDaemon(val)

try:
    # Python 3
    from urllib.parse import unquote as parse_unquote

    def unquote_qs(atom, encoding, errors='strict'):
        return parse_unquote(
            atom.replace('+', ' '),
            encoding=encoding,
            errors=errors)
except ImportError:
    # Python 2
    from urllib import unquote as parse_unquote

    def unquote_qs(atom, encoding, errors='strict'):
        return parse_unquote(atom.replace('+', ' ')).decode(encoding, errors)

try:
    # Prefer simplejson, which is usually more advanced than the builtin
    # module.
    import simplejson as json
    json_decode = json.JSONDecoder().decode
    _json_encode = json.JSONEncoder().iterencode
except ImportError:
    if sys.version_info >= (2, 6):
        # Python >=2.6 : json is part of the standard library
        import json
        json_decode = json.JSONDecoder().decode
        _json_encode = json.JSONEncoder().iterencode
    else:
        json = None

        def json_decode(s):
            raise ValueError('No JSON library is available')

        def _json_encode(s):
            raise ValueError('No JSON library is available')
finally:
    if json and six.PY3:
        # The two Python 3 implementations (simplejson/json)
        # outputs str. We need bytes.
        def json_encode(value):
            for chunk in _json_encode(value):
                yield chunk.encode('utf8')
    else:
        json_encode = _json_encode

text_or_bytes = six.text_type, six.binary_type

try:
    import cPickle as pickle
except ImportError:
    # In Python 2, pickle is a Python version.
    # In Python 3, pickle is the sped-up C version.
    import pickle

import binascii

def random20():
    return binascii.hexlify(os.urandom(20)).decode('ascii')

try:
    from _thread import get_ident as get_thread_ident
except ImportError:
    from thread import get_ident as get_thread_ident

try:
    # Python 3
    next = next
except NameError:
    # Python 2
    def next(i):
        return i.next()

if sys.version_info >= (3, 3):
    Timer = threading.Timer
    Event = threading.Event
else:
    # Python 3.2 and earlier
    Timer = threading._Timer
    Event = threading._Event

# Prior to Python 2.6, the Thread class did not have a .daemon property.
# This mix-in adds that property.


class SetDaemonProperty:

    def __get_daemon(self):
        return self.isDaemon()

    def __set_daemon(self, daemon):
        self.setDaemon(daemon)

    if sys.version_info < (2, 6):
        daemon = property(__get_daemon, __set_daemon)
