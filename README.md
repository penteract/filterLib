An attempt to build a self-inverse SVG filter which inverts brightness while preserving hue

SVG filters aren't easy to write directly, so lets make a Python library to help.

The ultimate goal of huerotate.py is to make a filter which transforms each constant-hue half-slice of the RGB cube independently - a point in the RGB cube should be reflected in the cube-bisecting plane perpendicular to the white-black diagonal, then scaled towards or away from the white-black axis by a factor depending on hue and luminance that sends the surface of the reflected cube to the surface of the cube.


Bugs observed:
In bug.html, Firefox displays the images with the filter #gParts essentially identically to chromium (and this result is the intended one). However, Firefox's screenshot tool and its color picker both show colors other than the one normally displayed in the filtered image for pixels which have a green component exactly 1 (out of 256 in the sRGB color space) less than the red component in the source image. These pixels form a diagonal line in the filtered image.

The filter #sorted behaves differently in Chromium and Firefox, behaving non-continuously in Firefox at pixels where color components are close in value. The intended behaviour of the filter is to sort pixel components so that the red component is highest, then the green, then the blue. It approximately does this in chromium, and at most points in Firefox. This may be related to the bug above, but I think I found some settings in which this bug occurred, but the above did not.

Chromium doesn't always render entire filtered images after zooming in/out. Sometimes it fills the empty space with a bright green background. It does render properly when the page is refreshed, even when zoomed.
