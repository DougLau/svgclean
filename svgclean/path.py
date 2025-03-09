#
#   svgclean/path.py
#
#   This is a module to interpret SVG path elements.
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
import sys
from . import format

PATH_RE = re.compile('([MmLlHhVvAaQqTtCcSsZz])([^MmLlHhVvAaQqTtCcSsZz]*)')
SPLIT_RE = re.compile('([+-]?(\d+\.\d*|\d*\.\d+|\d+)([eE][+-]?\d+)?)')

def space_str(value):
	if value.startswith('-'):
		return value
	else:
		return ' ' + value

def space_number(value, digits):
	s = format.from_number(value, digits)
	return space_str(s)

def calculate_epsilon(digits):
	if digits is None:
		return 1.0e-08
	else:
		return 1.0 / (10 ** digits)

def points_equal(p0, p1, epsilon):
	xd = abs(p0[0] - p1[0])
	yd = abs(p0[1] - p1[1])
	return xd < epsilon and yd < epsilon

class InvalidPathError(Exception):
	pass

class PathCommand(object):

	ORIGIN = (0, 0)

	CMNDS = {
		'M': 2,	# Move (x, y)
		'L': 2, # Line (x, y)
		'H': 1, # Horizontal-line (x)
		'V': 1, # Vertical-line (y)
		'A': 7, # Arc (rx, ry, x-axis-rot, large-arc, sweep, x, y)
		'Q': 4, # Quadratic curve (x1, y1, x, y)
		'T': 2, # Reflected quadratic curve (x, y)
		'C': 6, # Cubic curve (x1, y1, x2, y2, x, y)
		'S': 4, # Reflected cubic curve (x2, y2, x, y)
		'Z': 0, # Close path
	}

	def parameter_count(letter):
		l = letter.upper()
		if l in PathCommand.CMNDS:
			return PathCommand.CMNDS[l]
		else:
			raise InvalidPathError(letter)
	parameter_count = staticmethod(parameter_count)

	def __init__(self, letter, values):
		self.letter = letter
		self.values = values
		self.pen = None

	def set_pen(self, pen):
		self.pen = pen

	def fvalue(self, index):
		return float(self.values[index])

	def _get_pen_absolute(self):
		if self.letter == 'H':
			x = self.fvalue(-1)
			y = self.pen[1]
			return (x, y)
		if self.letter == 'V':
			x = self.pen[0]
			y = self.fvalue(-1)
			return (x, y)
		return (self.fvalue(-2), self.fvalue(-1))

	def _get_pen_relative(self):
		if self.letter == 'a':
			x = self.pen[0] + self.fvalue(-2)
			y = self.pen[1] + self.fvalue(-1)
			return (x, y)
		elif self.letter == 'h':
			x = self.pen[0] + self.fvalue(-1)
			y = self.pen[1]
			return (x, y)
		elif self.letter == 'v':
			x = self.pen[0]
			y = self.pen[1] + self.fvalue(-1)
			return (x, y)
		else:
			x = self.pen[0] + self.fvalue(-2)
			y = self.pen[1] + self.fvalue(-1)
			return (x, y)

	def get_pen_done(self):
		if self.letter.upper() == 'Z':
			return self.pen
		if self.is_absolute():
			return self._get_pen_absolute()
		else:
			return self._get_pen_relative()

	def get_reflected_point(self):
		if self.letter.upper() in 'CSQ':
			xd = self.fvalue(-2) - self.fvalue(-4)
			yd = self.fvalue(-1) - self.fvalue(-3)
			pen = self.get_pen_done()
			x = pen[0] + xd
			y = pen[1] + yd
			return (x, y)
		else:
			return None

	def test_reflected(self, reflected, epsilon):
		if reflected is None or self.letter.upper() not in 'CQ':
			return
		if self.letter.islower():
			x = self.pen[0] + self.fvalue(0)
			y = self.pen[1] + self.fvalue(1)
			p1 = (x, y)
		else:
			p1 = (self.fvalue(0), self.fvalue(1))
		if points_equal(reflected, p1, epsilon):
			if self.letter == 'C':
				self.letter = 'S'
			if self.letter == 'c':
				self.letter = 's'
			if self.letter == 'Q':
				self.letter = 'T'
			if self.letter == 'q':
				self.letter = 't'
			del self.values[:2]

	def _to_absolute_pairs(self):
		xv = [self.pen[0] + float(x) for x in self.values[::2]]
		yv = [self.pen[1] + float(y) for y in self.values[1::2]]
		values = []
		for x, y in zip(xv, yv):
			values.append(x)
			values.append(y)
		self.values = values

	def _to_absolute_horiz(self):
		assert self.letter == 'h'
		self.values = [self.pen[0] + float(x) for x in self.values]

	def _to_absolute_vert(self):
		assert self.letter == 'v'
		self.values = [self.pen[1] + float(y) for y in self.values]

	def _to_absolute(self):
		if self.is_command_pairs():
			self._to_absolute_pairs()
		elif self.letter == 'h':
			self._to_absolute_horiz()
		elif self.letter == 'v':
			self._to_absolute_vert()
		elif self.letter == 'a':
			self._to_absolute_arc()
		self.letter = self.letter.upper()

	def _to_relative_pairs(self):
		xv = [float(x) - self.pen[0] for x in self.values[::2]]
		yv = [float(y) - self.pen[1] for y in self.values[1::2]]
		values = []
		for x, y in zip(xv, yv):
			values.append(x)
			values.append(y)
		self.values = values

	def _to_relative_horiz(self):
		assert self.letter == 'H'
		self.values = [float(x) - self.pen[0] for x in self.values]

	def _to_relative_vert(self):
		assert self.letter == 'V'
		self.values = [float(y) - self.pen[1] for y in self.values]

	def _to_relative_arc(self):
		assert self.letter == 'A'
		x, y = self.values[-2:]
		x = float(x) - self.pen[0]
		y = float(y) - self.pen[1]
		self.values[-2:] = [x, y]

	def _to_relative(self):
		if self.is_command_pairs():
			self._to_relative_pairs()
		elif self.letter == 'H':
			self._to_relative_horiz()
		elif self.letter == 'V':
			self._to_relative_vert()
		elif self.letter == 'A':
			self._to_relative_arc()
		self.letter = self.letter.lower()

	def is_absolute(self):
		return self.letter.isupper()

	def is_relative(self):
		return self.letter.islower()

	def is_command_pairs(self):
		return self.letter.upper() in 'MLQTCS'

	def set_absolute(self, absolute):
		if absolute:
			if self.is_relative():
				self._to_absolute()
		else:
			if self.is_absolute():
				self._to_relative()

	def _to_horiz_line(self):
		assert self.letter == 'H'
		values = []
		for x in self.values:
			values.append(float(x))
			values.append(self.pen[1])
		self.values = values
		self.letter = 'L'

	def _to_vert_line(self):
		assert self.letter == 'V'
		values = []
		for y in self.values:
			values.append(self.pen[0])
			values.append(float(y))
		self.values = values
		self.letter = 'L'

	def transform(self, mtx):
		self.set_absolute(True)
		if self.letter == 'H':
			self._to_horiz_line()
		if self.letter == 'V':
			self._to_vert_line()
		if self.letter == 'A':
			raise InvalidPathError(
			    'FIXME: transforming arcs not implemented')
		if self.pen is not PathCommand.ORIGIN:
			self.pen = mtx.transform_point(*self.pen)
		xv = [float(x) for x in self.values[::2]]
		yv = [float(y) for y in self.values[1::2]]
		values = []
		for x, y in zip(xv, yv):
			x, y = mtx.transform_point(x, y)
			values.append(x)
			values.append(y)
		self.values = values

	def get_values(self):
		return [float(v) for v in self.values]

	def get_command(self, digits):
		return self.letter + ''.join(space_number(v, digits)
			for v in self.values).strip()

	def __str__(self):
		return self.letter + ' '.join(str(v)
			for v in self.values).strip()

def split_commands(geometry):
	for c in re.finditer(PATH_RE, geometry):
		letter = c.group(1)
		pcount = PathCommand.parameter_count(letter)
		value = c.group(2)
		values = [v[0] for v in SPLIT_RE.findall(value)]
		if pcount:
			if len(values) % pcount:
				raise InvalidPathError(c.group(0))
			for i in range(0, len(values), pcount):
				yield PathCommand(letter, values[i:i+pcount])
				if letter == 'M':
					letter = 'L'
				if letter == 'm':
					letter = 'l'
		elif values:
			raise InvalidPathError(c.group(0))
		else:
			yield PathCommand(letter, [])

def split_tokens(geometry, options, mtx):
	epsilon = calculate_epsilon(options.digits)
	pen = PathCommand.ORIGIN
	reflected = None
	prev_letter = '~'	# Tilde character never used
	for command in split_commands(geometry):
		command.set_pen(pen)
		if options.bezier:
			command.test_reflected(reflected, epsilon)
		reflected = command.get_reflected_point()
		pen = command.get_pen_done()
		if options.transform:
			command.transform(mtx)
		command.set_absolute(options.absolute)
		c = command.get_command(options.digits)
		if options.letter and c.startswith(prev_letter):
			c = c.lstrip(prev_letter)
			yield space_str(c)
		else:
			prev_letter = c[0]
			yield c

def split_values(geometry):
	pen = PathCommand.ORIGIN
	reflected = None
	for command in split_commands(geometry):
		command.set_pen(pen)
		pen = command.get_pen_done()
		l = command.letter.upper()
		command.set_absolute(True)
		pts = command.get_values()
		if l == 'S':
			yield ('C', list(reflected) + pts)
		elif l == 'T':
			yield ('Q', list(reflected) + pts)
		else:
			yield (l, pts)
		reflected = command.get_reflected_point()
