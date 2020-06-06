from os import chmod, path
from setuptools import Command
from shutil import rmtree

FILE_CONTROL = \
'''Package: {name}
Version: {version}
Architecture: all
'''

FILE_POSTINST = \
'''#!/bin/sh

py3compile --package {name}
'''

FILE_AZURE = \
'''#!/bin/sh

exec python3 -m{package}
'''


class deb (Command):

	user_options = []

	def __init__ (self, dist, **kw):
		super().__init__(dist, **kw)

		self.distinfo = dict(
			name = dist.metadata.name,
			version = dist.metadata.version,
			package = dist.packages[0]
		)

	def _file (self, filepath, content, mode = 0o644):
		self.mkpath(path.dirname(filepath), 0o755)

		self.announce('Creating file %s' % filepath)
		open(filepath, 'w').write(content.format(**self.distinfo))
		chmod(filepath, mode)

	def initialize_options (self):
		pass

	def finalize_options (self):
		pass

	def run (self):
		if path.exists('build'):
			self.announce('Removing existing build directory')
			rmtree('build')

		if path.exists('dist'):
			self.announce('Removing existing distribution directory')
			rmtree('dist')

		self._file('dist/DEBIAN/control', FILE_CONTROL)
		self._file('dist/DEBIAN/postinst', FILE_POSTINST, 0o755)
		self._file('dist/usr/lib/apt/methods/azure', FILE_AZURE, 0o755)

		packages = 'dist/usr/lib/python3/dist-packages'
		eggname = self.distinfo['package'] + '.egg-info'

		self.run_command('egg_info')
		self.copy_tree(eggname, path.join(packages, eggname))

		self.run_command('build')
		self.copy_tree('build/lib', packages)

		self.spawn([ 'dpkg-deb', '--build', 'dist', '.' ])
