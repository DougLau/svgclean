#
#   svgclean/style.py
#
#   This is a module to interpret SVG style attributes.
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
from . import color
from . import opacity
from . import stroke

# FIXME: option to convert all style to embedded CSS with class attributes
# FIXME: option to convert all style to external CSS with class attributes

_INHERIT = 'inherit'

class InvalidStyleError(Exception):
	pass

class Style(object):
	# FIXME: add missing styles
	ALL = (
		'visibility', 'display', 'color',
		'font-family', 'font-size', 'font-stretch', 'font-style',
		'font-variant', 'font-weight', 'text-anchor', 'writing-mode',
		'kerning', 'letter-spacing',
		'fill', 'fill-opacity', 'fill-rule',
		'stroke', 'stroke-dasharray', 'stroke-dashoffset',
		'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit',
		'stroke-opacity', 'stroke-width',
		'clip-path', 'clip-rule', 'mask', 'opacity',
		'enable-background', 'filter',
		'overflow',
		'marker', 'marker-start', 'marker-mid', 'marker-end',
		'stop-color', 'stop-opacity',
	)

	def __init__(self, parent, attrs):
		self.parent = parent
		self._props = {}
		self._set_presentation_attrs(attrs)
		self._parse_style_attr(attrs)

	def _set_presentation_attrs(self, attrs):
		for name in Style.ALL:
			if name in attrs:
				value = attrs[name].strip().strip(';')
				self.set_prop(name, value)
				del attrs[name]

	def _parse_one_style(self, s):
		try:
			name, value = s.split(':')
		except ValueError:
			print('Discarding invalid style: %s' % s,
			      file=sys.stderr)
			return
		name = name.strip()
		value = value.strip()
		self.set_prop(name, value)

	def _parse_style_attr(self, attrs):
		if 'style' in attrs:
			for s in attrs['style'].split(';'):
				s = s.strip()
				if s:
					self._parse_one_style(s)
			del attrs['style']

	def _set_prop(self, name, value):
		if value is _INHERIT:
			pass
		elif name in color.STYLES:
			color.validate(value)
		elif name in opacity.STYLES:
			opacity.validate(value)
		elif name in stroke.STYLES:
			stroke.validate(name, value)
		self._props[name] = value

	def set_prop(self, name, value):
		if name not in Style.ALL:
			print(('Discarding unknown style: %s:%s' %
			      (name, value)), file=sys.stderr)
			return
		try:
			self._set_prop(name, value)
		except ValueError:
			print(('Invalid style value: %s:%s' % (name, value)),
			      file=sys.stderr)

	def get_prop(self, name):
		try:
			return self._props[name]
		except KeyError:
			if self.parent:
				return self.parent.get_prop(name)

	def del_prop(self, name, verbose):
		try:
			value = self._props[name]
			if verbose:
				print('Removing style: %s:%s' % (name, value),
				      file=sys.stderr)
			del self._props[name]
		except KeyError:
			pass

	def normalize(self):
		for name in self._props:
			value = self._props[name]
			if value is _INHERIT:
				continue
			elif name in color.STYLES:
				v = color.normalize(value)
			elif name in opacity.STYLES:
				v = opacity.normalize(value)
			elif name in stroke.STYLES:
				v = stroke.normalize(name, value)
			else:
				continue
			self._props[name] = v

	def compress(self, verbose):
		stroke.compress(self, verbose)
		for name in Style.ALL:
			if name in self._props:
				value = self._props[name]
				par = self.parent.get_prop(name)
				if opacity.compress(name, value):
					self.del_prop(name, verbose)
				elif value == par:
					self.del_prop(name, verbose)

	def as_inline(self):
		props = []
		for p in Style.ALL:
			if p in self._props:
				props.append(':'.join((p, self._props[p])))
		return ';'.join(props)

	def set_inline_style(self, attrs):
		value = self.as_inline()
		if value:
			attrs['style'] = value

	def set_presentation_attributes(self, attrs):
		for p in self._props:
			attrs[p] = self._props[p]

	def __str__(self):
		props = []
		for p in Style.ALL:
			if p in self._props:
				props.append(':'.join((p, self._props[p])))
		if props:
			return "style='" + ';'.join(props) + "'"
		else:
			return ''

FILL_STYLES = {
	'fill': 'black',
	'fill-opacity': '1',
	'fill-rule': 'nonzero',
}

def compress_fill_styles(style):
	if style.get('fill', 'black') == 'none':
		for s in FILL_STYLES:
			if s in style:
				del style[s]
		style['fill'] = 'none'
		return

ROOT = Style(None, {
	'display': 'inline',
	'visibility': 'visible',
	'opacity': '1',
	'flood-opacity': '1',
	'stop-opacity': '1',
	'fill': 'black',
	'fill-opacity': '1',
	'fill-rule': 'nonzero',
	'stroke': 'none',
	'stroke-dasharray': 'none',
	'stroke-dashoffset': '0',
	'stroke-linecap': 'butt',
	'stroke-linejoin': 'miter',
	'stroke-miterlimit': '4',
	'stroke-opacity': '1',
	'stroke-width': '1',
	'marker': 'none',
	'marker-start': 'none',
	'marker-end': 'none',
	'marker-mid': 'none',
})
