from __future__ import print_function
import mimetypes
import os
import sys
import simplejson as json
import re
import boto
import gzip
import tempfile
from service_layer.settings import DESTINATION_PREFIX


class UnknowScheme(Exception):
  pass


class UnrecognizedUri(Exception):
  pass


def write(uri, data):
  scheme_handler = get_scheme_handler(uri)
  # decode this py3 object to string, however, py2 bytes is an alias for str
  if sys.version_info >= (3, 0) and isinstance(data, bytes):
    data = data.decode("utf-8")
  if not isinstance(data, str):
    data = json.dumps(data)
  scheme_handler(uri, data)


def get_scheme_handler(uri):
  try:
    scheme = parse_uri(uri)['scheme']
  except (IndexError,):
    raise UnknowScheme
  else:
    if scheme not in scheme_handlers.keys():
      raise UnknowScheme
    else:
      return scheme_handlers[scheme]


def parse_uri(uri):
  try:
    match = pattern_uri.match(uri)
    groupdict = match.groupdict()
    if groupdict['path'] == None:
      groupdict['path'] = ''
    groupdict.update({'subpath': groupdict['path'] + groupdict['basename']})
    return groupdict
  except (AttributeError,):
    raise UnrecognizedUri


def scheme_handler_s3(uri, data):
  parsed_uri = parse_uri(uri)
  content_type, encoding = mimetypes.guess_type(uri)
  content_type = content_type or 'application/json'
  headers = { 'Content-Type': content_type, 'x-amz-acl': 'public-read' }
  s3 = boto.connect_s3()
  bucket = s3.get_bucket(parsed_uri['authority'])
  key_name = parsed_uri['path'].lstrip('/') + parsed_uri['basename']
  key = bucket.new_key(key_name)
  key.content_type = content_type
  if key_name.endswith('gz'):
    headers['Content-Encoding'] = encoding
    gz_path = os.path.join(tempfile.gettempdir(), key_name)
    with gzip.open(gz_path, 'wb') as f:
      if sys.version_info >= (3, 0):
        data = data.encode()
      f.write(data)
    key.set_contents_from_filename(gz_path, headers=headers)
  else:
    key.set_contents_from_string(data, headers=headers)


def scheme_handler_file(uri, data):
  filepath = parse_uri(uri)['fullpath']
  filepath = os.path.join(DESTINATION_PREFIX, filepath)
  path = os.path.dirname(filepath)
  if not os.path.exists(path):
    os.makedirs(path)
  with open(filepath, 'w') as fh:
    fh.write(data)


pattern_uri = re.compile('^(?P<uri>(?P<scheme>\w+)://(?P<fullpath>(?P<dirname>(?P<authority>[^/]*)(?P<path>.*/))?(?P<basename>[^/]*)))')
scheme_handlers = {
  's3': scheme_handler_s3,
  'file': scheme_handler_file,
  'http': print, # this doesn't store anything at all. It just prints it to the console.
}
