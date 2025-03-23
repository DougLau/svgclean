#!/usr/bin/env python

from distutils.core import setup
from svgclean import VERSION

setup(
	name='svgclean',
	version=VERSION,
	author='Douglas Lau',
	author_email='doug.p.lau@gmail.com',
	description='Program to reformat SVG image files',
	packages=['svgclean'],
	data_files=[('/usr/share/svgclean',
		['ChangeLog', 'COPYING', 'TODO']
	)],
	scripts=['scripts/svgclean']
)
