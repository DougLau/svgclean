0.30 (11 Dec 2013)
* Added svg2pixy conversion program.

0.29 (4 Sep 2013)
* Fixed problem with --basic and rect elements with no x or y attrib.
* Converted to be compatible with python 3.

0.28 (30 Jun 2012)
* Simplified choice layer selection.

0.27 (2 Mar 2012)
* Added --attrib option to remove superfluous attributes.

0.26 (1 Mar 2012)
* Improved mksketch tool.

0.25 (9 Feb 2011)
* Implement --basic option to convert line/rect to paths.
* Improved mksketch tool.

0.24 (2 Feb 2011)
* Rewrote sketcher for new footile format.

0.23 (28 Mar 2008)
* Format/transform/optimise points attributes for polygon/polyline.
* Implement --poly option to convert polygon/polyline to paths.

0.22 (25 Mar 2008)
* Rewrote format module for simpler formatting.

0.21 (24 Mar 2008)
* Implemented --transform option to apply transformations to path data.

0.20 (19 Dec 2006)
* Implemented --recursive option to recursively clean files.

0.19 (4 Aug 2006)
* Added mksketch program.

0.18 (3 Aug 2006)
* Fixed a namespace bug with element closing tags.

0.17 (28 Jun 2006)
* Implemented --prefix option to change all namespace prefixes to
* customary values. (test with office/ballpoint_pen_jonathan_d_01.svg)

0.16 (27 Jun 2006)
* Implemented --namespace option to discard all elements from unknown
  namespaces.  This gets rid of stupid foreignObject filled with Adobe
  Illustrator crap. (test with office/pen_sek_01.svg)

0.15 (3 Mar 2006)
* Implemented --letter option to omit command letter on subsequent
  commands of same type.  (test with transportation/hummer_01.svg) 
* Changed --precision option to --digits

0.14 (3 Mar 2006)
* Added GPL license stuff.

0.13 (2 Mar 2006)
* Add support for distutils.
* Remove style which matches style of parent elements.
* Remove redundant style attributes (ex. stroke-width with stroke:none)
* Add option to convert all style to presentation attributes.
* Convert paths to relative coordinates after initial move.
* Remove comments.
* Remove style which matches default values.
* Move style attributes into a single "style" attribute.
* Select options from command-line switches (or dot-file?)
* Add DOCTYPE declaration if one doesn't exist
* Make default namespace svg and remove all svg: element prefixes.
* Convert "smooth" (reflected control point) "C" curves to "S" curves.
* Convert "smooth" (reflected control point) "Q" curves to "T" curves.
