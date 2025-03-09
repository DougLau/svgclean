#
#   svgclean/stroke.py
#
#   This is a module to interpret SVG stroke styles.
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
import re
from . import format

STYLES = (
	'stroke-dasharray',
	'stroke-dashoffset',
	'stroke-linecap',
	'stroke-linejoin',
	'stroke-miterlimit',
	'stroke-opacity',
	'stroke-width',
)

_DASHARRAY = re.compile(
	'((\d+\.\d*)|(\d*\.\d+)|(\d+))(\s*(em|ex|px|pt|pc|cm|mm|in|\%))?\s*,?\s*')

def validate_dasharray(value):
	if value != 'none' and not _DASHARRAY.match(value):
		raise ValueError(value)

_LENGTH = re.compile(
	'^([+-]?\d+\.\d*|\d*\.\d+|\d+)\s*(em|ex|px|pt|pc|cm|mm|in|%)*$')

def validate_length(value):
	if not _LENGTH.match(value):
		raise ValueError(value)

_LINECAPS = ('butt', 'round', 'square')

def validate_linecap(value):
	if value not in _LINECAPS:
		raise ValueError(value)

_LINEJOINS = ('miter', 'round', 'bevel')

def validate_linejoin(value):
	if value not in _LINEJOINS:
		raise ValueError(value)

_NUMBER = re.compile('^(\d+\.\d*|\d*\.\d+|\d+)$')

def validate_miterlimit(value):
	if not _NUMBER.match(value):
		raise ValueError(value)
	l = float(value)
	if l < 1:
		raise ValueError(value)

_VALIDATE = {
	'stroke-dasharray': validate_dasharray,
	'stroke-dashoffset': validate_length,
	'stroke-linecap': validate_linecap,
	'stroke-linejoin': validate_linejoin,
	'stroke-miterlimit': validate_miterlimit,
	'stroke-width': validate_length,
}

def validate(name, value):
	if name in _VALIDATE:
		_VALIDATE[name](value)

def normalize_length(value):
	m = _LENGTH.match(value)
	v = format.from_number(m.group(1), 3)
	if m.group(2) is None:
		return v
	else:
		return v + m.group(2)

def normalize_dasharray(value):
	if value == 'none':
		return value
	return ','.join(format.from_number(v[0], 3) + v[5]
		for v in _DASHARRAY.findall(value))

def normalize_number(value):
	return format.from_number(value, 3)

_NORMALIZE = {
	'stroke-dasharray': normalize_dasharray,
	'stroke-width': normalize_length,
	'stroke-miterlimit': normalize_number,
}

def normalize(name, value):
	if name in _NORMALIZE:
		return _NORMALIZE[name](value)
	else:
		return value

def compress(style, verbose):
	if style.get_prop('stroke') == 'none':
		for s in STYLES:
			style.del_prop(s, verbose)
	if style.get_prop('stroke-linejoin') != 'miter':
		style.del_prop('stroke-miterlimit', verbose)
	if style.get_prop('stroke-dasharray') == 'none':
		style.del_prop('stroke-dashoffset', verbose)
