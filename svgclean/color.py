#
#   svgclean/color.py
#
#   This is a module to parse SVG color styles.
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

STYLES = (
	'color',
	'fill',
	'stroke',
	'flood-color',
	'lighting-color',
	'stop-color',
)

_KEYWORDS = {
	'aliceblue': 0xf0f8ff,
	'antiquewhite': 0xfaebd7,
	'aqua': 0x00ffff,
	'aquamarine': 0x7fffd4,
	'azure': 0xf0ffff,
	'beige': 0xf5f5dc,
	'bisque': 0xffe4c4,
	'black': 0x000000,
	'blanchedalmond': 0xffebcd,
	'blue': 0x0000ff,
	'blueviolet': 0x8a2be2,
	'brown': 0xa52a2a,
	'burlywood': 0xdeb887,
	'cadetblue': 0x5f9ea0,
	'chartreuse': 0x7fff00,
	'chocolate': 0xd2691e,
	'coral': 0xff7f50,
	'cornflowerblue': 0x6495ed,
	'cornsilk': 0xfff8dc,
	'crimson': 0xdc143c,
	'cyan': 0x00ffff,
	'darkblue': 0x00008b,
	'darkcyan': 0x008b8b,
	'darkgoldenrod': 0xb8860b,
	'darkgray': 0xa9a9a9,
	'darkgreen': 0x006400,
	'darkgrey': 0xa9a9a9,
	'darkkhaki': 0xbdb76b,
	'darkmagenta': 0x8b008b,
	'darkolivegreen': 0x556b2f,
	'darkorange': 0xff8c00,
	'darkorchid': 0x9932cc,
	'darkred': 0x8b0000,
	'darksalmon': 0xe9967a,
	'darkseagreen': 0x8fbc8f,
	'darkslateblue': 0x483d8b,
	'darkslategray': 0x2f4f4f,
	'darkslategrey': 0x2f4f4f,
	'darkturquoise': 0x00ced1,
	'darkviolet': 0x9400d3,
	'deeppink': 0xff1493,
	'deepskyblue': 0x00bfff,
	'dimgray': 0x696969,
	'dimgrey': 0x696969,
	'dodgerblue': 0x1e90ff,
	'firebrick': 0xb22222,
	'floralwhite': 0xfffaf0,
	'forestgreen': 0x228b22,
	'fuchsia': 0xff00ff,
	'gainsboro': 0xdcdcdc,
	'ghostwhite': 0xf8f8ff,
	'gold': 0xffd700,
	'goldenrod': 0xdaa520,
	'gray': 0x808080,
	'green': 0x008000,
	'greenyellow': 0xadff2f,
	'grey': 0x808080,
	'honeydew': 0xf0fff0,
	'hotpink': 0xff69b4,
	'indianred': 0xcd5c5c,
	'indigo': 0x4b0082,
	'ivory': 0xfffff0,
	'khaki': 0xf0e68c,
	'lavender': 0xe6e6fa,
	'lavenderblush': 0xfff0f5,
	'lawngreen': 0x7cfc00,
	'lemonchiffon': 0xfffacd,
	'lightblue': 0xadd8e6,
	'lightcoral': 0xf08080,
	'lightcyan': 0xe0ffff,
	'lightgoldenrodyellow': 0xfafad2,
	'lightgray': 0xd3d3d3,
	'lightgreen': 0x90ee90,
	'lightgrey': 0xd3d3d3,
	'lightpink': 0xffb6c1,
	'lightsalmon': 0xffa07a,
	'lightseagreen': 0x20b2aa,
	'lightskyblue': 0x87cefa,
	'lightslategray': 0x778899,
	'lightslategrey': 0x778899,
	'lightsteelblue': 0xb0c4de,
	'lightyellow': 0xffffe0,
	'lime': 0x00ff00,
	'limegreen': 0x32cd32,
	'linen': 0xfaf0e6,
	'magenta': 0xff00ff,
	'maroon': 0x800000,
	'mediumaquamarine': 0x66cdaa,
	'mediumblue': 0x0000cd,
	'mediumorchid': 0xba55d3,
	'mediumpurple': 0x9370db,
	'mediumseagreen': 0x3cb371,
	'mediumslateblue': 0x7b68ee,
	'mediumspringgreen': 0x00fa9a,
	'mediumturquoise': 0x48d1cc,
	'mediumvioletred': 0xc71585,
	'midnightblue': 0x191970,
	'mintcream': 0xf5fffa,
	'mistyrose': 0xffe4e1,
	'moccasin': 0xffe4b5,
	'navajowhite': 0xffdead,
	'navy': 0x000080,
	'oldlace': 0xfdf5e6,
	'olive': 0x808000,
	'olivedrab': 0x6b8e23,
	'orange': 0xffa500,
	'orangered': 0xff4500,
	'orchid': 0xda70d6,
	'palegoldenrod': 0xeee8aa,
	'palegreen': 0x98fb98,
	'paleturquoise': 0xafeeee,
	'palevioletred': 0xdb7093,
	'papayawhip': 0xffefd5,
	'peachpuff': 0xffdab9,
	'peru': 0xcd853f,
	'pink': 0xffc0cb,
	'plum': 0xdda0dd,
	'powderblue': 0xb0e0e6,
	'purple': 0x800080,
	'red': 0xff0000,
	'rosybrown': 0xbc8f8f,
	'royalblue': 0x4169e1,
	'saddlebrown': 0x8b4513,
	'salmon': 0xfa8072,
	'sandybrown': 0xf4a460,
	'seagreen': 0x2e8b57,
	'seashell': 0xfff5ee,
	'sienna': 0xa0522d,
	'silver': 0xc0c0c0,
	'skyblue': 0x87ceeb,
	'slateblue': 0x6a5acd,
	'slategray': 0x708090,
	'slategrey': 0x708090,
	'snow': 0xfffafa,
	'springgreen': 0x00ff7f,
	'steelblue': 0x4682b4,
	'tan': 0xd2b48c,
	'teal': 0x008080,
	'thistle': 0xd8bfd8,
	'tomato': 0xff6347,
	'turquoise': 0x40e0d0,
	'violet': 0xee82ee,
	'wheat': 0xf5deb3,
	'white': 0xffffff,
	'whitesmoke': 0xf5f5f5,
	'yellow': 0xffff00,
	'yellowgreen': 0x9acd32,
}

_TRIPLET = re.compile('^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$')
_SEXTUPLET = re.compile('^#([0-9a-fA-F]{6})$')
_FUNCTION = re.compile(
	'^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$')
_PERCENT = re.compile(
	'^rgb\(\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*\)$')
_URL = re.compile('^url\(#.*\)$')

def validate(value):
	'Validate a color style value'
	v = value.lower()
	if v == 'none':
		return
	if v in _KEYWORDS:
		return
	if _TRIPLET.match(v):
		return
	if _SEXTUPLET.match(v):
		return
	if _FUNCTION.match(v):
		return
	if _PERCENT.match(v):
		return
	if _URL.match(v):
		return
	raise ValueError(value)

def _triplet(r, g, b):
	return (int(r * 2, 16) << 16) + (int(g * 2, 16) << 8) + int(b * 2, 16)

def _rgb(r, g, b):
	r = max(0, min(int(r), 255))
	g = max(0, min(int(g), 255))
	b = max(0, min(int(b), 255))
	return (r << 16) + (g << 8) + b

def _percent(r, g, b):
	r = round(255 * float(r) / 100)
	g = round(255 * float(g) / 100)
	b = round(255 * float(b) / 100)
	return _rgb(r, g, b)

def normalize_to_int(value):
	v = value.lower()
	if v in _KEYWORDS:
		return _KEYWORDS[v]
	m = _TRIPLET.match(v)
	if m:
		return _triplet(m.group(1), m.group(2), m.group(3))
	m = _SEXTUPLET.match(v)
	if m:
		return int(m.group(1), 16)
	m = _FUNCTION.match(v)
	if m:
		return _rgb(m.group(1), m.group(2), m.group(3))
	m = _PERCENT.match(v)
	if m:
		return _percent(m.group(1), m.group(2), m.group(3))

def _check_pair(h):
	if h[0] == h[1]:
		return h[0]

def _check_triplet(value):
	rgb = '%06x' % value
	rr = rgb[0:2]
	gg = rgb[2:4]
	bb = rgb[4:6]
	r = _check_pair(rr)
	g = _check_pair(gg)
	b = _check_pair(bb)
	if r and g and b:
		return '%s%s%s' % (r, g, b)
	else:
		return rgb

def normalize(value):
	'Normalize a color style value'
	v = normalize_to_int(value)
	if v is None:
		return value
	elif v in list(_KEYWORDS.values()):
		for key in _KEYWORDS:
			if _KEYWORDS[key] == v:
				return key
	h = _check_triplet(v)
	return '#' + h

def _normalize(value):
	v = normalize(value)
	print('%s\t%s' % (v, value))

if __name__ == '__main__':
	_normalize('white')
	_normalize('#fff')
	_normalize('#ffffff')
	_normalize('rgb(255,255,255)')
	_normalize('rgb(100%,100%,100%)')
	_normalize('rgb(98%,98%,98%)')
	_normalize('black')
	_normalize('#000')
	_normalize('#000000')
	_normalize('rgb(0,0,0)')
	_normalize('rgb(0%,0%,0%)')
	_normalize('magenta')
	_normalize('lightpink')
	_normalize('#ffb6c2')
	_normalize('#667788')
	_normalize('#123')
