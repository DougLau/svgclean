* Add --dpi option to allow unit conversion (normalization).
* Make --basic option work for circles and ellipses.
* Convert horizontal/vertical L path commands to H/V.
* Make --digits option apply to all user units in applicable attributes.
* Remove all trailing zeros from all numbers (after decimal point).
* Remove redundant colinear points from path or polygon data.
* Write comments and documentation.
* Remove overflow style if not on svg, pattern or marker element.
* Use viewBox to scale all points by 10, 100, etc. so that no decimal
  points are needed in path data (integer only).
* Add option to remove metadata elements.
* Add option to select output encoding, with invalid characters replaced
  by entity references.

Needs DOM or elementtree (after version 1.0):

* Remove id attributes which are never referenced.
* Remove all elements in defs which are never referenced.
* Remove empty g elements
* Pull all style attributes out of elements and generate a stylesheet
  with classes for each unique style.
* Identify and replace cut-and-pasted paths with use elements
  (test with decorations/wreath_of_evergreens_with_red_berries.svg)
* Remove elements with style display:none or visibility:hidden if there
  are no references to them (this may break animations, though).
  (test with computer/TV_zazou.svg)
