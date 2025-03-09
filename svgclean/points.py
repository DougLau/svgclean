#
#   svgclean/points.py
#
#   This is a module to interpret SVG points attributes.
#   Copyright (C) 2008-2013  Douglas P. Lau
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   included COPYING file for more details.
#
import re
from . import format

SPLIT_RE = re.compile('[ \t\n,]+')

def transform_values(values, mtx):
	xv = [float(x) for x in values[::2]]
	yv = [float(y) for y in values[1::2]]
	v = []
	for x, y in zip(xv, yv):
		x, y = mtx.transform_point(x, y)
		v.append(x)
		v.append(y)
	return v

def split_tokens(pts, options, mtx):
	values = [v for v in SPLIT_RE.split(pts.strip())]
	if len(values) % 2:
		del values[-1]
	if options.transform:
		values = transform_values(values, mtx)
	first = True
	for v in values:
		if first:
			first = False
			yield format.from_number(v, options.digits)
		else:
			yield ' ' + format.from_number(v, options.digits)

def convert_to_path(pts, z):
	values = [v for v in SPLIT_RE.split(pts.strip())]
	if len(values) % 2:
		del values[-1]
	crds = []
	while values:
		x = values.pop(0)
		y = values.pop(0)
		if crds:
			crds.append('L' + x + ' ' + y)
		else:
			crds.append('M' + x + ' ' + y)
	if z:
		crds.append('Z')
	return ''.join(crds)
