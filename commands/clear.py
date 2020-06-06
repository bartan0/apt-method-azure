from glob import glob
from os import path
from setuptools import Command
from shutil import rmtree


class clear (Command):

	user_options = []

	def _rm (self, p):
		if path.exists(p):
			rmtree(p)

	def initialize_options (self):
		pass

	def finalize_options (self):
		pass

	def run (self):
		for pattern in [
			'**/__pycache__',
			'*.egg-info',
			'build',
			'dist'
		]:
			for p in glob(pattern):
				self._rm(p)
