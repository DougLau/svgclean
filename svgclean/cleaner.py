#
#   svgclean/cleaner.py
#
#   This is a module to clean SVG documents.
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

from xml.parsers.expat import ParserCreate, ExpatError
from .format import Formatter
import sys
from . import style
from . import transform
from . import path
from . import points
from . import namespace

UTF8_ENCODING = 'UTF-8'
NAMESPACE = 'http://www.w3.org/2000/svg'
PUBLIC_ID_10 = '-//W3C//DTD SVG 1.0//EN'
SYSTEM_ID_10 = 'http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd'
PUBLIC_ID_11 = '-//W3C//DTD SVG 1.1//EN'
SYSTEM_ID_11 = 'http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd'

class InvalidDocTypeError(Exception):
	pass

class UnknownNamespaceError(Exception):
	pass

class SvgCleaner(object):

	def __init__(self, options):
		self.parser = ParserCreate()
		self.parser.XmlDeclHandler = self.xml_decl
		self.parser.StartDoctypeDeclHandler = self.start_doctype_decl
		self.parser.CommentHandler = self.comment
		self.parser.StartElementHandler = self.start_element
		self.parser.EndElementHandler = self.end_element
		self.parser.CharacterDataHandler = self.character_data
		self.parser.StartCdataSectionHandler = self.start_cdata_section
		self.parser.EndCdataSectionHandler = self.end_cdata_section
		self.options = options
		self.xml = None
		self.doctype = None
		self.open_tag = False
		self.format = Formatter(self.options.indent)
		self.discard = []
		self.spaces = namespace.DeclaredNamespaces()
		self.styles = [style.ROOT]
		self.matrices = [transform.Matrix()]

	def warn(self, msg):
		if self.options.verbose:
			print(msg.encode('utf_8'), file=sys.stderr)

	def error(self, msg):
		print(msg.encode('utf_8'), file=sys.stderr)

	def add_token(self, token):
		if self.open_tag:
			self.format.end_block('>')
			self.open_tag = False
		self.format.begin_block('', '')
		self.format.write(token)
		self.format.end_block(None)

	def write_attribute(self, elem, attr, value):
		token = "%s='" % attr
		if attr == 'id' and elem != 'svg':
			if not self.options.attrib:
				self.format.begin_block(token, '')
				self.format.write(value)
				self.format.end_block("'")
		elif attr == 'd':
			self.format.begin_block(token, '')
			for v in path.split_tokens(value, self.options,
			    self.matrices[-1]):
				self.format.write(v)
			self.format.end_block("'")
		elif attr == 'points':
			self.format.begin_block(token, '')
			for v in points.split_tokens(value, self.options,
			    self.matrices[-1]):
				self.format.write(v)
			self.format.end_block("'")
		elif attr == 'style':
			self.format.begin_block(token, ';')
			for s in value.split(';'):
				self.format.write(s)
			self.format.end_block("'")
		else:
			self.format.begin_block(token, '')
			self.format.write(value)
			self.format.end_block("'")

	def write_attributes(self, elem, attrs):
		for level in self.spaces.stack:
			for ns in list(level.values()):
				for ca in ns.customary_attribs():
					if ca in attrs:
						self.write_attribute(elem, ca,
							attrs[ca])
						del attrs[ca]
		for a in attrs:
			self.warn('Discarding attribute: %s="%s"' % (a,
				attrs[a]))

	def xml_decl(self, version, encoding, standalone):
		if encoding is None:
			encoding = UTF8_ENCODING
		self.format.create(self.options.out_file, encoding)
		self.format.begin_block('<?xml ', ' ')
		self.write_attribute('xml', 'version', version)
		self.write_attribute('xml', 'encoding', encoding)
		if standalone:
			standalone = 'yes'
		else:
			standalone = 'no'
		self.write_attribute('xml', 'standalone', standalone)
		self.format.end_block('?>')
		self.xml = True

	def check_xml_decl(self):
		if self.xml is None:
			self.xml_decl('1.0', UTF8_ENCODING, 'no')

	def start_doctype_decl(self, doctype, system_id, public_id,
	    has_internal_subset):
		self.check_xml_decl()
		if doctype != 'svg':
			raise InvalidDocTypeError(doctype)
		self.doctype = doctype
		self.format.begin_block('<!DOCTYPE ', ' ')
		self.format.write(doctype)
		if public_id is not None:
			self.format.write('PUBLIC')
			self.format.write("'%s'" % public_id)
		if system_id is not None:
			self.format.write("'%s'" % system_id)
		self.format.end_block('>')

	def check_doctype_defined(self):
		if self.doctype is None:
			self.start_doctype_decl('svg', SYSTEM_ID_11,
				PUBLIC_ID_11, False)

	def check_namespace(self, attrs):
		if 'xmlns' in attrs:
			if attrs['xmlns'].lower() != NAMESPACE:
				raise UnknownNamespaceError(attrs['xmlns'])

	def comment(self, data):
		if not self.options.comments:
			self.add_token('<!--%s-->' % data)

	def start_cdata_section(self):
		self.add_token('<![CDATA[')

	def end_cdata_section(self):
		self.format.write(']]>')

	def character_data(self, data):
		data = data.strip()
		if data:
			self.add_token(data)

	def process_style(self, attrs):
		s = style.Style(self.styles[-1], attrs)
		self.styles.append(s)
		if self.options.style:
			s.normalize()
			s.compress(self.options.verbose)
		if self.options.presentation:
			s.set_presentation_attributes(attrs)
		else:
			s.set_inline_style(attrs)

	def process_transform(self, attrs):
		m = transform.parse(self.matrices[-1], attrs)
		self.matrices.append(m)

	def push_discard(self, name):
		self.warn('Discarding element: %s' % name)
		self.discard.append(name)
		self.format.set_discard(True)

	def pop_discard(self, name):
		d = self.discard.pop(-1)
		if d != name:
			self.error('Discard problem: %s != %s' % (name, d))
			sys.exit(1)
		if not self.discard:
			self.format.set_discard(False)

	def adjust_name(self, name, attrs):
		if self.options.prefix:
			name = self.spaces.get_customary_name(name)
		if self.options.poly and name == 'polygon':
			if attrs:
				pts = attrs.pop('points')
				attrs['d'] = points.convert_to_path(pts, True)
			return 'path'
		elif self.options.poly and name == 'polyline':
			if attrs:
				pts = attrs.pop('points')
				attrs['d'] = points.convert_to_path(pts, False)
			return 'path'
		elif self.options.basic and name == 'line':
			if attrs:
				pts = ' '.join([attrs.pop('x1'),
					attrs.pop('y1'), attrs.pop('x2'),
					attrs.pop('y2')])
				attrs['d'] = points.convert_to_path(pts, False)
			return 'path'
		elif self.options.basic and name == 'rect':
			# FIXME: does not work with rx, ry attributes
			if attrs:
				x = attrs.pop('x', '0')
				y = attrs.pop('y', '0')
				width = attrs.pop('width')
				height = attrs.pop('height')
				xw = str(float(x) + float(width))
				yh = str(float(y) + float(height))
				pts = ' '.join([x, y, x, yh, xw, yh, xw, y])
				attrs['d'] = points.convert_to_path(pts, True)
			return 'path'
		else:
			return name

	def _should_discard(self, name):
		return (self.options.namespace and not
		        self.spaces.is_element_valid(name)) or \
		       (self.options.foreign and name == 'foreignObject')

	def start_element(self, name, attrs):
		self.check_doctype_defined()
		self.spaces.enter(attrs)
		if self.open_tag:
			self.format.end_block('>')
			if len(self.styles) > 2:
				self.format.begin_block('\t', '\n')
		if self._should_discard(name):
			self.push_discard(name)
		name = self.adjust_name(name, attrs)
		if name == 'style' and self.options.style:
			self.warn('Stylesheet declared: '
			          'Style compression disabled')
			self.options.style = False
		self.format.begin_block('<%s ' % name, '\n')
		if name == 'svg':
			self.check_namespace(attrs)
		self.process_style(attrs)
		if self.options.transform:
			self.process_transform(attrs)
		self.write_attributes(name, attrs)
		self.open_tag = True

	def end_element(self, name):
		self.styles.pop()
		if self.options.transform:
			self.matrices.pop()
		n = self.adjust_name(name, None)
		if self.open_tag:
			self.format.end_block('/>')
			self.open_tag = False
		else:
			if name != 'svg':
				self.format.end_block(None)
			self.format.write('</%s>' % n)
		if self._should_discard(name):
			self.pop_discard(name)
		self.spaces.exit()

	def _parse_file(self, f):
		try:
			self.parser.ParseFile(f)
		except ExpatError:
			self.error('XML Parsing error: %s' %
			           self.options.in_file)

	def clean_file(self):
		self.warn('Processing file: %s' % self.options.in_file)
		f = open(self.options.in_file)
		try:
			self._parse_file(f)
		finally:
			self.format.close()
			f.close()
