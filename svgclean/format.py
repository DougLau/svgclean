#
#   svgclean/format.py
#
#   This is a module to format SVG documents.
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
import codecs
import string
import sys

class NullIO:
	def write(self, args):
		pass
	def close(self):
		pass

def _from_number(value, digits):
	if digits is None:
		if isinstance(value, str):
			return value
		else:
			digits = 8
	assert digits >= 0
	v = float(value)
	fmt = '%%.%df' % digits
	return fmt % v

def from_number(value, digits):
	s = _from_number(value, digits)
	if '.' in s:
		return s.rstrip('0').rstrip('.')
	else:
		return s

class Formatter(object):

	def __init__(self, indent):
		self.out = sys.stdout
		self.tabs = True
		self.indent = indent
		self.block = [(0, '\n')]
		self.width = 77
		self.line = ''
		self.sticky = True

	def create(self, out, encoding):
		if out:
			self.out = codecs.open(out, 'w', encoding)
			self._out = self.out
		else:
			if sys.stdout.encoding == encoding:
				self.out = sys.stdout
			else:
				# FIXME: replace invalid characters with
				# numeric entity references?
				c = codecs.getwriter(encoding)
				self.out = c(sys.stdout)
			self._out = self.out

	def _flush(self):
		self._flush_line()

	def _get_indent(self):
		b = self.block[-1]
		return b[0]

	def _indent_to(self, column):
		if self.tabs:
			return '\t' * (column / 8) + ' ' * (column % 8)
		else:
			return ' ' * column

	def _flush_line(self):
		if self.line:
			self.out.write(self.line)
			self.out.write('\n')
			self.line = ''

	def _check_line_width(self, line):
		return len(line.replace('\t', ' ' * 8)) > self.width

	def _get_sep(self):
		b = self.block[-1]
		return b[1]

	def begin_block(self, tag, sep):
		if tag == '\t':
			columns = self.indent
		else:
			self.write(tag)
			columns = len(tag)
		if self.indent:
			i = self._get_indent() + columns
		else:
			i = 0
		self.block.append((i, sep))
		self.sticky = True
		if tag == '\t':
			self.write('')

	def end_block(self, tag):
		assert self.block
		self.block[-1] = (0, '')
		if tag is not None:
			self.line = self.line.rstrip()
			self.sticky = True
			self.write(tag)
		self.block.pop()

	def write(self, data):
		sep = self._get_sep()
		if self.sticky:
			self.line = self.line + data
			self.sticky = False
			return
		line = self.line + sep + data
		if sep == '\n' or self._check_line_width(line):
			if sep not in string.whitespace:
				self.line = self.line + sep
			self._flush_line()
			self.line = self._indent_to(self._get_indent()) + \
				data.lstrip()
		else:
			self.line = line

	def set_discard(self, d):
		self._flush()
		if d:
			self.out = NullIO()
		else:
			self.out = self._out

	def close(self):
		self._flush()
		if self.out != sys.stdout:
			self.out.close()
