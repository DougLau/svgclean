#
#   svgclean/opacity.py
#
#   This is a module to interpret SVG opacity styles.
#   Copyright (C) 2006-2013  Douglas P. Lau
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
import sys
from . import format

STYLES = (
	'opacity',
	'fill-opacity',
	'stroke-opacity',
	'flood-opacity',
	'stop-opacity',
)

def validate(value):
	'Check value is a valid opacity'
	float(value.rstrip('%'))

def _range_clamp(value, lo, hi, dp):
	v = max(lo, min(value, hi))
	return format.from_number(v, dp)

def normalize(value):
	'Normalize an opacity value'
	if value.endswith('%'):
		v = float(value.rstrip('%')) / 100
	else:
		v = float(value)
	return _range_clamp(v, 0, 1, 3)

def compress(name, value):
	return name in STYLES and value == 1
