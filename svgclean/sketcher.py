#
#   svgclean/sketcher.py
#
#   This is a module to convert SVG images to C sketch sources.
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

from xml.parsers.expat import ParserCreate
from . import color
from . import style
from . import path
from . import namespace

class InvalidDocTypeError(Exception):
	pass

class InvalidPathError(Exception):
	pass

def fixed_hex(fval):
	return '0x%02X' % fval

def fixed_4_4(vals):
	assert min(vals) >= 0
	assert max(vals) < 16
	return ', '.join(fixed_hex(int(round(val * 16))) for val in vals)

def fixed_8_4(vals):
	assert min(vals) >= 0
	assert max(vals) < 256
	# convert to 8.4 fixed-point
	fvals = [int(round(v * 16)) for v in vals]
	bvals = []
	for x, y in zip(fvals[::2], fvals[1::2]):
		bvals.append(x & 0xFF)
		bvals.append(((x >> 8) & 0x0F) | ((y & 0x0F) << 4))
		bvals.append((y >> 4) & 0xFF)
	return ', '.join(fixed_hex(b) for b in bvals)

def fixed_12_4(vals):
	assert min(vals) >= 0
	assert max(vals) < 4096
	# convert to 12.4 fixed-point
	fvals = [int(round(v * 16)) for v in vals]
	bvals = []
	for v in fvals:
		bvals.append(v & 0xFF)
		bvals.append(v >> 8 & 0xFF)
	return ', '.join(fixed_hex(b) for b in bvals)

def fixed_s12_4(vals):
	assert min(vals) >= -2048
	assert max(vals) <= 2047
	# convert to s12.4 fixed-point
	fvals = [int(round(v * 16)) for v in vals]
	bvals = []
	for v in fvals:
		bvals.append(v & 0xFF)
		bvals.append(v >> 8 & 0xFF)
	return ', '.join(fixed_hex(b) for b in bvals)

def int_12_0(vals):
	assert min(vals) > 0
	assert max(vals) < 4096
	bvals = []
	for x, y in zip(vals[::2], vals[1::2]):
		bvals.append(x & 0xFF)
		bvals.append(((x >> 8) & 0x0F) | ((y & 0x0F) << 4))
		bvals.append((y >> 4) & 0xFF)
	return ', '.join(fixed_hex(b) for b in bvals)

def format_line(opcode=None, line=None, comment=None):
	parts = ['']
	if opcode:
		parts.append(opcode + ',')
	else:
		parts.append('')
	if line:
		tabs = (30 - len(line)) / 8
		parts.append(line + ',' + ('\t' * tabs))
	else:
		parts.append('\t\t\t')
	if comment:
		parts.append('/* ' + comment + ' */')
	return '\t'.join(parts)

class Operation(object):
	def combine(self, other):
		return self.opcode() == other.opcode()

class OpDetail(Operation):
	def __init__(self, detail):
		self.detail = detail
	def opcode(self):
		return '0x0%x' % self.detail
	def __str__(self):
		return format_line(self.opcode(), comment='detail')

class OpClose(Operation):
	def opcode(self):
		return '0x20'
	def __str__(self):
		return format_line(self.opcode(), comment='close')

# Compose subcodes
OPAQUE_BLACK = 0
OPAQUE_WHITE = 1
OPAQUE_RGB8 = 2
OPAQUE_PREVIOUS = 3
OPAQUE_GRAY = 4
ALPHA_BLACK = 8
ALPHA_WHITE = 9
ALPHA_ARGB8 = 10
ALPHA_PREVIOUS = 11
ALPHA_GRAY = 12

class OpCompose(Operation):
	def __init__(self, a, r, g, b, prev):
		self.fill = (a, r, g, b)
		self.prev = prev
	def combine(self, other):
		return isinstance(other, OpClose)
	def opcode(self):
		return '0x30'
	def subcode(self):
		if self.fill[0] == 255:
			if self.fill[1:] == (0, 0, 0):
				return OPAQUE_BLACK
			elif self.fill[1:] == (255, 255, 255):
				return OPAQUE_WHITE
			elif self.prev and self.fill[1:] == self.prev[1:]:
				return OPAQUE_PREVIOUS
			elif (self.fill[1] == self.fill[2] and
			      self.fill[1] == self.fill[3]):
				return OPAQUE_GRAY
			else:
				return OPAQUE_RGB8
		else:
			if self.fill[1:] == (0, 0, 0):
				return ALPHA_BLACK
			elif self.fill[1:] == (255, 255, 255):
				return ALPHA_WHITE
			elif self.prev and self.fill[1:] == self.prev[1:]:
				return ALPHA_PREVIOUS
			elif (self.fill[1] == self.fill[2] and
			      self.fill[1] == self.fill[3]):
				return ALPHA_GRAY
			else:
				return ALPHA_ARGB8
	def fopcode(self):
		opcode = self.opcode()[:-1]
		return opcode + '%1X' % self.subcode()
	def str_fill(self):
		ccode = self.subcode()
		if (ccode == OPAQUE_BLACK or ccode == OPAQUE_WHITE or
		    ccode == OPAQUE_PREVIOUS):
			return ''
		elif ccode == OPAQUE_RGB8:
			return ', '.join(fixed_hex(c) for c in self.fill[1:])
		elif ccode == OPAQUE_GRAY:
			return fixed_hex(self.fill[1])
		elif (ccode == ALPHA_BLACK or ccode == ALPHA_WHITE or
		      ccode == ALPHA_PREVIOUS):
			return fixed_hex(self.fill[0])
		elif ccode == ALPHA_ARGB8:
			return ', '.join(fixed_hex(c) for c in self.fill)
		else:
			raise Exception('Invalid subcode')
	def str_comment(self):
		ccode = self.subcode()
		if ccode == OPAQUE_BLACK:
			return 'opaque black'
		elif ccode == OPAQUE_WHITE:
			return 'opaque white'
		elif ccode == OPAQUE_RGB8:
			return 'RGB8'
		elif ccode == OPAQUE_PREVIOUS:
			return 'opaque previous'
		elif ccode == OPAQUE_GRAY:
			return 'opaque gray'
		elif ccode == ALPHA_BLACK:
			return 'alpha black'
		elif ccode == ALPHA_WHITE:
			return 'alpha white'
		elif ccode == ALPHA_ARGB8:
			return 'ARGB8'
		elif ccode == ALPHA_PREVIOUS:
			return 'alpha previous'
		elif ccode == ALPHA_GRAY:
			return 'alpha gray'
		else:
			raise Exception('Invalid subcode')
	def __str__(self):
		return format_line(self.fopcode(), self.str_fill(), 'compose ' +
			self.str_comment())

def fixed_func(vals):
	fvals = [(int(round(v * 16))) for v in vals]
	if min(fvals) < 0:
		return fixed_s12_4
	mv = max(fvals) >> 4
	if mv >= 256:
		return fixed_12_4
	if mv >= 16:
		return fixed_8_4
	else:
		return fixed_4_4

class OpLine(Operation):
	def __init__(self, vals):
		self.vals = vals
	def combine(self, other):
		if self.opcode() == other.opcode():
			if len(self.vals) < 16 * 2:
				self.vals.extend(other.vals)
				return True
		return False
	def opcode(self):
		func = fixed_func(self.vals)
		if func == fixed_s12_4:
			return '0x70'
		if func == fixed_12_4:
			return '0x60'
		if func == fixed_8_4:
			return '0x50'
		else:
			return '0x40'
	def oprep(self):
		opcode = self.opcode()[:-1]
		reps = len(self.vals) // 2
		return opcode + '%1X' % (reps - 1)
	def points(self):
		assert len(self.vals) > 0
		assert len(self.vals) % 2 == 0
		assert len(self.vals) <= 16 * 2
		func = fixed_func(self.vals)
		points = []
		for pt in zip(self.vals[::2], self.vals[1::2]):
			x = round(pt[0] * 16) / 16.0
			y = round(pt[1] * 16) / 16.0
			points.append((func(pt), '%s, %s' % (x, y)))
		return points
	def __str__(self):
		lines = []
		points = self.points()
		line, com = points.pop(0)
		lines.append(format_line(self.oprep(), line, 'line ' + com))
		for line, com in points:
			comment = '     ' + com
			lines.append(format_line(line=line,comment=comment))
		return '\n'.join(lines)

class OpSpline(Operation):
	def __init__(self, vals):
		self.vals = vals
	def combine(self, other):
		if self.opcode() == other.opcode():
			if len(self.vals) < 16 * 6:
				self.vals.extend(other.vals)
				return True
		return False
	def opcode(self):
		func = fixed_func(self.vals)
		if func == fixed_s12_4:
			return '0xB0'
		if func == fixed_12_4:
			return '0xA0'
		if func == fixed_8_4:
			return '0x90'
		else:
			return '0x80'
	def oprep(self):
		opcode = self.opcode()[:-1]
		reps = len(self.vals) // 6
		return opcode + '%1X' % (reps - 1)
	def points(self):
		assert len(self.vals) > 0
		assert len(self.vals) % 6 == 0
		assert len(self.vals) <= 16 * 6
		func = fixed_func(self.vals)
		points = []
		for pt in zip(self.vals[::2], self.vals[1::2]):
			x = round(pt[0] * 16) / 16.0
			y = round(pt[1] * 16) / 16.0
			points.append((func(pt), '%s, %s' % (x, y)))
		return points
	def __str__(self):
		lines = []
		points = self.points()
		line, com = points.pop(0)
		lines.append(format_line(self.oprep(), line, 'spline ' + com))
		for line, com in points:
			comment = '       ' + com
			lines.append(format_line(line=line,comment=comment))
		return '\n'.join(lines)

class OpChoice(Operation):
	def __init__(self, choice):
		self.choice_id = choice[0]
		if self.choice_id < 0 or self.choice_id > 15:
			raise Exception('Invalid choice ID')
		self.value = 0
		if len(choice) == 2:
			self.value = choice[1]
	def combine(self, other):
		if self.opcode() == other.opcode():
			if self.choice_id == other.choice_id:
				self.value = other.value
				return True
		return False
	def opcode(self):
		return '0xF%x' % self.choice_id
	def __str__(self):
		return format_line(self.opcode(), fixed_hex(self.value),
		       comment='choice %d (%d)' % (self.choice_id, self.value))

def create_compose(st, prev_color):
	fill = color.normalize_to_int(st.get_prop('fill'))
	opacity = (float(st.get_prop('opacity')) *
		float(st.get_prop('fill-opacity')))
	alpha = int(round(255 * opacity))
	red = fill >> 16 & 0xFF
	green = fill >> 8 & 0xFF
	blue = fill & 0xFF
	return OpCompose(alpha, red, green, blue, prev_color)

def create_operations(attrs, st, prev_color):
	d = path.split_values(attrs['d'])
	for l, v in d:
		if l not in 'CMLZ':
			raise InvalidPathError(l, v)
		if l == 'M':
			yield OpClose()
		if l == 'Z':
			yield OpClose()
		if l == 'C':
			if len(v) != 6:
				raise InvalidPathError(l, v)
			yield OpSpline(v)
		elif v:
			if len(v) != 2:
				raise InvalidPathError(l, v)
			yield OpLine(v)
	yield create_compose(st, prev_color)

class Sketcher(object):

	def __init__(self):
		self.parser = ParserCreate()
		self.parser.StartDoctypeDeclHandler = self.start_doctype_decl
		self.parser.StartElementHandler = self.start_element
		self.parser.EndElementHandler = self.end_element
		self.spaces = namespace.DeclaredNamespaces()
		self.glabels = []
		self.styles = [style.ROOT]
		self.ops = []
		self.prev_color = None

	def lop(self):
		if self.ops:
			return self.ops[-1]
		else:
			return None

	def start_doctype_decl(self, doctype, system_id, public_id,
	    has_internal_subset):
		if doctype != 'svg':
			raise InvalidDocTypeError(doctype)

	def process_style(self, attrs):
		s = style.Style(self.styles[-1], attrs)
		self.styles.append(s)
		return s

	def start_element(self, name, attrs):
		self.spaces.enter(attrs)
		name = self.spaces.get_customary_name(name)
		s = self.process_style(attrs)
		if name == 'svg':
			self.name = attrs['id']
			self.width = attrs['width']
			self.height = attrs['height']
		elif name == 'rect':
			if int(attrs['x']) == 0 and \
			   int(attrs['y']) == 0 and \
			   attrs['width'] == self.width and \
			   attrs['height'] == self.height:
				self.ops.append(create_compose(s, None))
		elif name == 'g':
			glabel = ''
			if 'inkscape:label' in attrs:
				glabel = attrs['inkscape:label']
			if glabel.startswith('detail_'):
				det = int(glabel[7:])
				if det:
					self.ops.append(OpDetail(det))
			elif glabel.startswith('choice_'):
				choice = [int(v) for v in glabel[7:].split('_')]
				if len(choice) == 2:
					op = OpChoice(choice)
					lop = self.lop()
					if lop is None or not lop.combine(op):
						self.ops.append(op)
			self.glabels.append(glabel)
		elif name == 'path':
			lop = self.lop()
			if isinstance(lop,OpDetail) or isinstance(lop,OpChoice):
				lop = None
			for op in create_operations(attrs, s, self.prev_color):
				if lop:
					if lop.combine(op):
						continue
					if isinstance(lop, OpClose):
						if isinstance(op, OpCompose):
							del self.ops[-1]
				else:
					if isinstance(op, OpClose):
						continue
				self.ops.append(op)
				lop = op
				if isinstance(op, OpCompose):
					self.prev_color = op.fill

	def end_element(self, name):
		self.styles.pop()
		if name == 'g':
			glabel = self.glabels.pop()
			if glabel.startswith('choice_'):
				choice = [int(v) for v in glabel[7:].split('_')]
				self.ops.append(OpChoice(choice[:1]))
		self.spaces.exit()

	def parse(self, f):
		self.parser.ParseFile(f)
		self.ops.append(OpDetail(0))

FILE_HEADER = "/* generated by mksketch */\n"
SKETCH_INTRO = "static const unsigned char sketch_%s_ops[] = {"
FILE_TAIL = "};"

def make_sketch(f):
	m = Sketcher()
	m.parse(open(f))
	print(FILE_HEADER)
	print(SKETCH_INTRO % m.name)
	size = tuple(int(v) for v in (m.width, m.height))
	print(format_line('0x10', int_12_0(size), 'canvas %dx%d' % size))
	for op in m.ops:
		print(str(op))
	print(FILE_TAIL)
