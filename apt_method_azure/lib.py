import sys

from base64 import b64encode
from hashlib import md5
from http.client import HTTPSConnection
from urllib.parse import urlparse

from .state import state


def auth_conf_path ():
	conf = state.apt_config

	return '%s/%s/%s' % (
		conf['Dir'] or '/',
		conf['Dir::Etc'] or 'etc/apt',
		conf['Dir::Etc::netrcparts'] or 'auth.conf.d'
	)

def log (*args):
	print(*args, file = sys.stderr)

def send (code, status, **headers):
	# log('>', code, status)

	state.outstream.write(
		'%d %s\n' % (code, status) +
		'\n'.join( '%s: %s' % (field.title().replace('_', '-'), value) for field, value in headers.items() ) +
		'\n\n'
	)

def read_msg ():
	line = state.instream.readline()

	if not line:
		raise EOFError()

	code, status = line.split(maxsplit = 1)
	headers = {}

	while True:
		line = state.instream.readline()

		if not line:
			raise EOFError()

		if line == '\n':
			break

		field, value = line.split(':', 1)
		field = field.strip()

		if field in headers:
			headers[field].append(value.strip())
		else:
			headers[field] = [ value.strip() ]

	# log('<', code, status)

	return (
		int(code),
		status.strip(),
		headers
	)

def getblob (headers, auth):
	uri = headers['URI'][0]
	uri_parts = urlparse(uri)
	auth_type = uri_parts.username

	conn = HTTPSConnection(uri_parts.hostname)

	if not auth_type:
		conn.request('GET', uri_parts.path)
	elif auth_type == 'sas':
		conn.request('GET', uri_parts.path + auth['sas'])
	else:
		return

	res = conn.getresponse()

	if res.status == 403:
		return send(401, 'General Failure',
			message = 'Authorization failed'
		)

	if res.status == 404:
		return send(400, 'URI Failure',
			URI = uri,
			message = 'Blob not found'
		)

	if res.status != 200:
		return send(401, 'General Failure',
			message = '%d %s: Unexpected response' % (res.status, res.reason)
		)

	filename = headers['Filename'][0]
	last_modified = res.getheader('Last-Modified')
	size = int(res.getheader('Content-Length'))

	send(200, 'URI Start',
		URI = uri,
		size = size,
		last_modified = last_modified
	)

	with open(filename, 'wb') as f:
		d = size
		h = md5()

		while True:
			if not d:
				return send(201, 'URI Done',
					URI = uri,
					filename = filename,
					size = size,
					last_modified = last_modified,
					MD5_hash = str(b64encode(h.digest()), 'ascii')
				)

			data = res.read(min(d, 4096))

			if not data:
				return send(400, 'URI Failure',
					URI = uri,
					message = 'Unexpected end of stream'
				)

			h.update(data)
			f.write(data)
			d -= len(data)
