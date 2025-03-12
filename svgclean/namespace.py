#
#   svgclean/namespace.py
#
#   This is a module to represent XML namespace definitions.
#   Copyright (C) 2006-2025  Douglas P. Lau
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
from .style import Style

class Namespace(object):

	def __init__(self, uri, prefix, elements, attrib):
		self.uri = uri
		self.prefix = prefix		# customary prefix
		self.elements = elements
		self.attrib = attrib

	def has_element(self, element):
		return element in self.elements

	def customary_attribs(self):
		if self.prefix == 'svg':
			return self.attrib
		else:
			return (':'.join((self.prefix, a)) for a in self.attrib)

# FIXME: should have version 1.0 vs 1.1 namespaces?
SVG = Namespace('http://www.w3.org/2000/svg', 'svg',
(	# Elements
	'a', 'altGlyph', 'altGlyphDef', 'altGlyphItem', 'animate',
	'animateColor', 'animateMotion', 'animateTransform', 'circle',
	'clipPath', 'color-profile', 'cursor', 'definition-src', 'defs',
	'desc', 'ellipse', 'feBlend', 'feColorMatrix', 'feComponentTransfer',
	'feComposite', 'feConvolveMatrix', 'feDiffuseLighting',
	'feDisplacementMap', 'feDistantLight', 'feFlood', 'feFuncA', 'feFuncB',
	'feFuncG', 'feFuncR', 'feGaussianBlur', 'feImage', 'feMerge',
	'feMergeNode', 'feMorphology', 'feOffset', 'fePointLight',
	'feSpecularLighting', 'feSpotLight', 'feTile', 'feTurbulence',
	'filter', 'font', 'font-face', 'font-face-format', 'font-face-name',
	'font-face-src', 'font-face-uri', 'foreignObject', 'g', 'glyph',
	'glyphRef', 'hkern', 'image', 'line', 'linearGradient', 'marker',
	'mask', 'metadata', 'missing-glyph', 'mpath', 'path', 'pattern',
	'polygon', 'polyline', 'radialGradient', 'rect', 'script', 'set',
	'stop', 'style', 'svg', 'switch', 'symbol', 'text', 'textPath',
	'title', 'tref', 'tspan', 'use', 'view', 'vkern'
), (	# Attributes
	'id', 'href', 'type', 'class', 'style', 'offset',
	'values',
	'x', 'y', 'width', 'height', 'viewBox',
	'x1', 'y1', 'x2', 'y2',
	'cx', 'cy', 'r', 'rx', 'ry',
	'transform', 'd', 'points',
	'markerWidth', 'markerHeight', 'orient', 'refX', 'refY',
	'patternUnits', 'patternTransform',
	'fx', 'fy', 'gradientUnits', 'gradientTransform',
	'spreadMethod',
	'startOffset',
	'version', 'xmlns',
	# Namespace attributes -- is there a better way to handle these?
	'xmlns:svg', 'xmlns:ns', 'xmlns:xlink', 'xmlns:rdf', 'xmlns:cc',
	'xmlns:dc', 'xmlns:inkscape',
) + Style.ALL)

XLINK = Namespace('http://www.w3.org/1999/xlink', 'xlink',
(	# Elements
), (	# Attributes
	'href',
	'type',
))

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf',
(	# Elements
	'Bag',
	'li',
	'RDF',
), (	# Attributes
	'about',
	'resource',
))

CC = Namespace('http://web.resource.org/cc', 'cc',
(	# Elements
	'Work',
	'Agent',
	'license',
	'License',
	'permits',
), (	# Attributes
))

DC = Namespace('http://purl.org/dc/elements/1.1', 'dc',
(	# Elements
	'creator',
	'date',
	'description',
	'format',
	'language',
	'publisher',
	'rights',
	'subject',
	'title',
	'type',
), (	# Attributes
))

INKSCAPE = Namespace('http://www.inkscape.org/namespaces/inkscape', 'inkscape',
(	# Elements
), (	# Attributes
	'groupmode',
	'label',
	'version',
))

_KNOWN = {
	SVG.uri: SVG,
	XLINK.uri: XLINK,
	RDF.uri: RDF,
	CC.uri: CC,
	DC.uri: DC,
	INKSCAPE.uri: INKSCAPE,
}

def lookup_xmlns(attrs):
	decl = {}
	for a in attrs:
		if a.startswith('xmlns'):
			if ':' in a:
				prefix = a.split(':').pop()
			else:
				prefix = ''
			decl[prefix] = attrs[a]
	return decl

def lookup_namespace(uri):
	uri = uri.strip('/').lower()
	if uri in _KNOWN:
		return _KNOWN[uri]

def split_name(n):
	names = n.split(':')
	name = names.pop()
	if names:
		prefix = names.pop()
	else:
		prefix = ''
	return prefix, name

class DeclaredNamespaces(object):
	def __init__(self):
		root = { '': SVG }
		self.stack = [root]
	def enter(self, attrs):
		decl = lookup_xmlns(attrs)
		spaces = {}
		for prefix in decl:
			uri = decl[prefix]
			ns = lookup_namespace(uri)
			if ns:
				spaces[prefix] = ns
		self.stack.append(spaces)
	def exit(self):
		self.stack.pop()
	def lookup_namespace(self, prefix):
		for spaces in reversed(self.stack):
			if prefix in spaces:
				return spaces[prefix]
	def is_element_valid(self, element):
		prefix, name = split_name(element)
		ns = self.lookup_namespace(prefix)
		if ns:
			return ns.has_element(name)
		else:
			return False
	def get_customary_name(self, element):
		prefix, name = split_name(element)
		ns = self.lookup_namespace(prefix)
		if ns is None:
			return element
		elif self.lookup_namespace('') == ns:
			return name
		else:
			return ns.prefix + ':' + name
