#
#   svgclean/transform.py
#
#   This is a module to interpret SVG coordinate transforms.
#   Copyright (C) 2008  Douglas P. Lau
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
from math import sin, cos, radians

class InvalidTransformError(Exception):
	pass

class Matrix(object):

	def __init__(self, m = (1, 0, 0, 1, 0, 0)):
		assert isinstance(m, tuple)
		assert len(m) == 6
		self.m = m

	def multiply(self, other):
		"""
			| a c e |   | t v x |   | at+bv ct+dv et+fv+x |
			| b d f | * | u w y | = | au+bw cu+dw eu+fw+y |
			| 0 0 1 |   | 0 0 1 |   |   0     0      1    |
		"""
		o = self.m
		m = other.m
		self.m = (
			m[0] * o[0] + m[1] * o[2],
			m[0] * o[1] + m[1] * o[3],
			m[2] * o[0] + m[3] * o[2],
			m[2] * o[1] + m[3] * o[3],
			m[4] * o[0] + m[5] * o[2] + o[4],
			m[4] * o[1] + m[5] * o[3] + o[5],
		)

	def translate(self, x, y):
		self.multiply(Matrix((1, 0, 0, 1, x, y)))

	def scale(self, x, y):
		self.multiply(Matrix((x, 0, 0, y, 0, 0)))

	def rotate(self, d):
		a = radians(d)
		s = sin(a)
		c = cos(a)
		self.multiply(Matrix((c, s, -s, c, 0, 0)))

	def transform_point(self, x, y):
		m = self.m
		return (
			m[0] * x + m[2] * y + m[4],
			m[1] * x + m[3] * y + m[5],
		)

_TRANSFORM = re.compile('(matrix|translate|scale|rotate)(\(.*?\))')
_NUMBERS = re.compile('([+-]?([0-9]+(\.[0-9]+)?)([eE][+-]?[0-9]+)?)')

def _parse_numbers(v):
	m = []
	for ma in _NUMBERS.finditer(v):
		m.append(float(ma.group(0)))
	return m

def _parse_translate(v):
	t = _parse_numbers(v)
	if len(t) != 2:
		raise InvalidTransformError
	x, y = t
	m = Matrix()
	m.translate(x, y)
	return m

def _parse_rotate(v):
	t = _parse_numbers(v)
	if len(t) != 1:
		raise InvalidTransformError
	d = t[0]
	m = Matrix()
	m.rotate(d)
	return m

def _parse_scale(v):
	t = _parse_numbers(v)
	if len(t) == 1:
		s = t[0]
		m = Matrix()
		m.scale(s, s)
		return m
	elif len(t) == 2:
		x, y = t
		m = Matrix()
		m.scale(x, y)
		return m
	else:
		raise InvalidTransformError

def _parse_matrix(v):
	m = _parse_numbers(v)
	if len(m) != 6:
		raise InvalidTransformError
	return Matrix(tuple(m))

def _parse(f, v):
	if f == 'translate':
		return _parse_translate(v)
	elif f == 'rotate':
		return _parse_rotate(v)
	elif f == 'scale':
		return _parse_scale(v)
	elif f == 'matrix':
		return _parse_matrix(v)
	else:
		raise InvalidTransformError

def parse(parent, attrs):
	import sys
	m = Matrix(parent.m)
	if 'transform' in attrs:
		t = attrs['transform']
		for ma in _TRANSFORM.finditer(t):
			f = ma.group(1)
			v = ma.group(2)
			m.multiply(_parse(f, v))
		del attrs['transform']
	return m
