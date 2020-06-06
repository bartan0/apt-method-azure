import sys

from threading import Thread
from urllib.parse import urlparse

from . import (
	__version__,
	auth_conf_path,
	getblob,
	log,
	read_msg,
	send,
	state
)


if __name__ == '__main__':
	state.instream = open(sys.stdin.fileno(), 'r', 1)
	state.outstream = open(sys.stdout.fileno(), 'w', 1)
	state.auth = {}
	state.apt_config = dict(( k, None ) for k in [
		'Dir',
		'Dir::Etc',
		'Dir::Etc::netrcparts'
	])

	try:
		send(100, 'Capabilities',
			version = __version__,
			send_config = True
		)

		while True:
			code, status, headers = read_msg()

			# URI Acquire
			if code == 600:
				uri = urlparse(headers['URI'][0])
				container = uri.path.split('/')[1]

				auth_id = '%s/%s' % (uri.hostname, container)

				if auth_id not in state.auth:
					with open('%s/azure_%s_%s' % (auth_conf_path(), uri.hostname, container)) as f:
						state.auth[auth_id] = {}

						for line in f:
							auth_type, token = line.split()
							state.auth[auth_id][auth_type] = token

				Thread(target = getblob,
					args = (headers, state.auth[auth_id])
				).start()

			# Configuration
			elif code == 601:
				for item in headers['Config-Item']:
					k, v = item.split('=', 1)

					if k in state.apt_config:
						state.apt_config[k] = v

			else:
				log('%d %s: Unknown message' % (code, status))

	except (EOFError, KeyboardInterrupt):
		pass
