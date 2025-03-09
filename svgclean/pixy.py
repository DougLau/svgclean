#
#   svgclean/pixy.py
#
#   This is a module to convert SVG images to C pixy sources.
#   Copyright (C) 2006-2015  Douglas P. Lau
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

SCALE = 16
all_colors = set()
palette = []

class InvalidDocTypeError(Exception):
	pass

class InvalidPathError(Exception):
	pass

def encode_u8(ba, x, y):
	assert min(x, y) >= 0
	assert max(x, y) < 256
	ba.append(x)
	ba.append(y)

def encode_s8(ba, x, y):
	assert min(x, y) >= -128
	assert max(x, y) < 128
	ba.append(x & 0xFF)
	ba.append(y & 0xFF)

def encode_s12(ba, x, y):
	assert min(x, y) >= -2048
	assert max(x, y) < 2048
	ba.append((x >> 4) & 0xFF)
	ba.append(((x << 4) & 0xF0) | ((y >> 8) & 0x0F))
	ba.append(y & 0xFF)

def encode_s16(ba, x, y):
	assert min(x, y) >= -32768
	assert max(x, y) < 32768
	for v in x, y:
		ba.append((v >> 8) & 0xFF)
		ba.append(v & 0xFF)

def encode_func(vecs):
	mn = min(min(x, y) for x, y in vecs)
	mx = max(max(x, y) for x, y in vecs)
	if mn < -2048 or mx > 2047:
		return encode_s16
	elif mn < -128 or mx > 127:
		return encode_s12
	else:
		return encode_s8

class Operation(object):
	def combine(self, other):
		return self.opcode() == other.opcode()
	def replace(self, other):
		return False
	def as_bytes(self):
		return bytearray([self.opcode()])

class OpDetail(Operation):
	def combine(self, other):
		return False
	def replace(self, other):
		return isinstance(other, OpGroup)
	def opcode(self):
		return 0b00111000

class OpEnd(Operation):
	def replace(self, other):
		return isinstance(other, OpGroup)
	def opcode(self):
		return 0b00111001

class OpMagic(Operation):
	def opcode(self):
		return 0b00111010
	def as_bytes(self):
		ba = bytearray(':Pixy\0')
		ba.append(0)	# version major
		ba.append(1)	# version minor
		return ba

class OpCanvas(Operation):
	def __init__(self, w, h):
		self.width = w
		self.height = h
	def opcode(self):
		return 0b00111100
	def as_bytes(self):
		ba = bytearray()
		ba.append(self.opcode())
		encode_u16(ba, self.width)
		encode_u16(ba, self.height)
		return ba

class OpPalette(Operation):
	def opcode(self):
		return 0b00111101
	def as_bytes(self):
		ba = bytearray()
		ba.append(self.opcode())
		ba.append(len(palette))
		for rgb in palette:
			ba.extend(rgb)
		return ba

def encode_u16(ba, v):
	assert v >= 0
	assert v < 65536
	ba.append((v >> 8) & 0xFF)
	ba.append(v & 0xFF)

# Compose subcodes
OPAQUE_BLACK = 0b000
OPAQUE_WHITE = 0b001
PREVIOUS = 0b010
OPAQUE_GRAY = 0b011
OPAQUE_PALETTE = 0b100
ALPHA_PALETTE = 0b101
OPAQUE_RGB8 = 0b110
ALPHA_ARGB8 = 0b111

def is_gray(rgb):
	r, g, b = rgb
	return r == g and r == b

class OpCompose(Operation):
	def __init__(self, a, r, g, b, prev):
		assert a >= 0 and a < 256
		assert r >= 0 and r < 256
		assert g >= 0 and g < 256
		assert b >= 0 and b < 256
		rgb = (r, g, b)
		self.fill = (a, r, g, b)
		self.prev = prev
		if self.fill != prev and not is_gray(rgb):
			if rgb in all_colors:
				if rgb not in palette:
					palette.append(rgb)
			else:
				all_colors.add(rgb)
	def combine(self, other):
		return isinstance(other, OpCompose) and self.fill == other.fill
	def opcode(self):
		return 0b00100000
	def sub_color(self):
		if self.prev and self.fill == self.prev:
			return PREVIOUS
		rgb = self.fill[1:]
		if self.fill[0] == 255:
			if rgb == (0, 0, 0):
				return OPAQUE_BLACK
			elif rgb == (255, 255, 255):
				return OPAQUE_WHITE
			elif (self.fill[1] == self.fill[2] and
			      self.fill[1] == self.fill[3]):
				return OPAQUE_GRAY
			elif rgb in palette:
				return OPAQUE_PALETTE
			else:
				return OPAQUE_RGB8
		else:
			if rgb in palette:
				return ALPHA_PALETTE
			else:
				return ALPHA_ARGB8
	def subcode(self):
		# Set rasterize (fill and clear) flag
		return self.sub_color() | 0b00001000
	def as_bytes(self):
		ccode = self.subcode()
		ba = bytearray()
		ba.append(self.opcode() | ccode)
		if ccode == OPAQUE_GRAY:
			ba.append(self.fill[1])
		elif ccode == OPAQUE_PALETTE:
			ba.append(palette.index(self.fill[1:]))
		elif ccode == ALPHA_PALETTE:
			ba.append(self.fill[0])
			ba.append(palette.index(self.fill[1:]))
		elif ccode == OPAQUE_RGB8:
			ba.extend(self.fill[1:])
		elif ccode == ALPHA_ARGB8:
			ba.extend(self.fill)
		return ba

class OpPath(Operation):
	def __init__(self, vals, pen):
		px = pen[0]
		py = pen[1]
		svals = [int(round(v * SCALE)) for v in vals]
		pts = [(x, y) for x, y in zip(svals[::2], svals[1::2])]
		self.endpen = pts[-1]
		self.vecs = [(x - px, y - py) for x, y in pts]
	def combine(self, other):
		if self.opcode() == other.opcode():
			if self.count() < 16:
				self.vecs.extend(other.vecs)
				return True
		return False
	def oprep(self):
		reps = self.count() - 1
		assert reps >= 0 and reps < 16
		return self.opcode() + reps
	def as_bytes(self):
		ba = bytearray()
		ba.append(self.oprep())
		func = encode_func(self.vecs)
		for x, y in self.vecs:
			func(ba, x, y)
		return ba

class OpLine(OpPath):
	def count(self):
		return len(self.vecs)
	def opcode(self):
		func = encode_func(self.vecs)
		if func == encode_s8:
			return 0b01000000
		elif func == encode_s12:
			return 0b10000000
		else:
			return 0b11000000

class OpSplineQuadratic(OpPath):
	def count(self):
		return len(self.vecs) // 2
	def opcode(self):
		func = encode_func(self.vecs)
		if func == encode_s8:
			return 0b01010000
		elif func == encode_s12:
			return 0b10010000
		else:
			return 0b11010000

class OpSplineCubic(OpPath):
	def count(self):
		return len(self.vecs) // 3
	def opcode(self):
		func = encode_func(self.vecs)
		if func == encode_s8:
			return 0b01100000
		elif func == encode_s12:
			return 0b10100000
		else:
			return 0b11100000

class OpGroup(Operation):
	def __init__(self, group):
		self.group = group
		if self.group < 0 or self.group > 15:
			raise Exception('Invalid group ID')
	def combine(self, other):
		return False
	def replace(self, other):
		return isinstance(other, OpGroup)
	def opcode(self):
		return 0b00000000 | self.group

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
	first = True
	compose = False
	pen = (0, 0)
	d = path.split_values(attrs['d'])
	for l, v in d:
		if l not in 'CMLQZ':
			raise InvalidPathError(l, v)
		if not first:
			if l == 'M' or l == 'Z':
				yield create_compose(st, prev_color)
				compose = False
				pen = (0, 0)
		if l == 'C':
			if len(v) != 6:
				raise InvalidPathError(l, v)
			op = OpSplineCubic(v, pen)
			pen = op.endpen
			yield op
			compose = True
		elif l == 'Q':
			if len(v) != 4:
				raise InvalidPathError(l, v)
			op = OpSplineQuadratic(v, pen)
			pen = op.endpen
			yield op
			compose = True
		elif v:
			if len(v) != 2:
				raise InvalidPathError(l, v)
			op = OpLine(v, pen)
			pen = op.endpen
			yield op
			compose = True
		first = False
	if compose:
		yield create_compose(st, prev_color)

class Pixy(object):

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

	def add_op(self, op):
		lop = self.lop()
		if lop is None:
			self.ops.append(op)
		elif op.replace(lop):
			self.ops.pop()
			self.ops.append(op)
		elif not lop.combine(op):
			self.ops.append(op)

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
			self.width = attrs['width']
			self.height = attrs['height']
		elif name == 'rect':
			if int(attrs['x']) == 0 and \
			   int(attrs['y']) == 0 and \
			   attrs['width'] == self.width and \
			   attrs['height'] == self.height:
				self.add_op(create_compose(s, None))
		elif name == 'g':
			glabel = ''
			if 'inkscape:label' in attrs:
				glabel = attrs['inkscape:label']
			if glabel.startswith('detail_'):
				det = int(glabel[7:])
				if det:
					self.add_op(OpDetail())
			elif glabel.startswith('choice_'):
				choice = [int(v) for v in glabel[7:].split('_')]
				if len(choice) == 2:
					self.add_op(OpGroup(choice[0]))
					self.prev_color = None
			self.glabels.append(glabel)
		elif name == 'path':
			for op in create_operations(attrs, s, self.prev_color):
				self.add_op(op)
				if isinstance(op, OpCompose):
					self.prev_color = op.fill

	def end_element(self, name):
		self.styles.pop()
		if name == 'g':
			glabel = self.glabels.pop()
			if glabel.startswith('choice_'):
				self.add_op(OpGroup(0))
		self.spaces.exit()

	def parse(self, f):
		self.parser.ParseFile(f)
		self.add_op(OpEnd())

	def write(self, out):
		width = int(round(int(self.width) * SCALE))
		height = int(round(int(self.height) * SCALE))
		out.write(OpMagic().as_bytes())
		out.write(OpCanvas(width, height).as_bytes())
		if palette:
			out.write(OpPalette().as_bytes())
		for op in self.ops:
			out.write(op.as_bytes())

def make_pixy(infile, out):
	m = Pixy()
	m.parse(infile)
	m.write(out)
