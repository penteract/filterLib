An attempt to build a self-inverse SVG filter which inverts brightness while preserving hue

SVG filters aren't easy to write directly, so lets make a Python library to help.

The ultimate goal of huerotate.py is to make a filter which transforms each constant-hue half-slice of the RGB cube independently - a point in the RGB cube should be reflected in the cube-bisecting plane perpendicular to the white-black diagonal, then scaled towards or away from the white-black axis by a factor depending on hue and luminance that sends the surface of the reflected cube to the surface of the cube.


# Bugs observed:

In bug.html, Firefox displays the images with the filter #gParts essentially identically to chromium (and this result is the intended one). However, Firefox's screenshot tool and its color picker both show colors other than the one normally displayed in the filtered image for pixels which have a green component exactly 1 (out of 256 in the sRGB color space) less than the red component in the source image. These pixels form a diagonal line in the filtered image.

The filter #sorted behaves differently in Chromium and Firefox, behaving non-continuously in Firefox at pixels where color components are close in value. The intended behaviour of the filter is to sort pixel components so that the red component is highest, then the green, then the blue. It approximately does this in chromium, and at most points in Firefox. This may be related to the bug above, but I think I found some settings in which this bug occurred, but the above did not.

Chromium doesn't always render entire filtered images after zooming in/out. Sometimes it fills the empty space with a bright green background. It does render properly when the page is refreshed, even when zoomed.


The comment at
https://hg.mozilla.org/mozilla-central/file/tip/layout/svg/FilterInstance.cpp#l737
suggests a candidate place to put the blame.


Alternatively, It might be connected to the 2 different rendering paths described here: https://firefox-source-docs.mozilla.org/gfx/RenderingOverview.html

Are the matrix entries stored in a different order to how they occur in the SVG attribute? (5 sequences of 4 rather than 4 sequences of 5?)
https://searchfox.org/mozilla-central/source/gfx/wr/webrender/src/picture.rs#6404


I think I've found it (and it's related to the 2 different rendering paths:
https://searchfox.org/mozilla-central/source/gfx/2d/FilterProcessingSIMD-inl.h#558
takes the matrix entries in i16s, probably treatedfixed-point signed binary numbers, whereas the webrender path passes things to the GPU as floats. Since I'm using matrix entries as big as 2550, differences arise.

Adding to the saga, I think that in the integer-based code path, color components of #ff are considered to have value 255, while matrix entries of 1.0 are considered to have value 256. This leads to off by one errors, even in cases where converting floats to ints doesn't cause problems. Hopefully this can be fixed by multiplying the last column of the matrix (sometimes called 'bias' in ff source) by 255 instead of shifting it.


# Precise values at which color component changes

### in css rgb(x%,0%,0%) smallest value of x that gives color component 0xff
254.5/255 - (2**-24) (boundary within 2**-24)

### smallest value in 5th matrix column which gives color component 0xff
normal rendering: 255.5/256 (boundary within 2**-24)
under color picker: (255 - 1/256)/255 (boundary within (2**-28))
### smallest value in 5th matrix column which gives color component 0x1
normal rendering: (0.5 + 0.625/256)/256 (boundary within 2**-24)
under color picker: (0x01 - 1.0/255)/255 (boundary within 2**-24)

So, the relavant code processing floating point numbers to do integer arithmetic starts here https://searchfox.org/mozilla-central/source/gfx/2d/FilterProcessingSIMD-inl.h#586 .

In a row `[r,g,b,a,u]` of a matrix, the constant `u` clamped between around +/- 2^16, then multiplied by 255*128, then rounded to the nearest 32-bit signed integer.

The other entries get clamped between +/- 255, then multiplied by 128, then rounded to the nearest 16-bit signed integer.

This means there is no overflow when accumulating `u` and the results the products of r,g,b and a with color component values between 0 and 255 (inclusive) into a 32-bit integer.

The accumulated 32-bit integer is then shifted right by 7 (divided by 128 and truncated towards -inf), and clamped between 0 and 255 (inclusive) to fit back in an 8-bit color component


Cases where it differs from webRender/chromium behaviour:
Matrix entries where precision beyond 1/128 is important
 - a color component of #ff multiplied by a modified entry can never reach even values other than 0x0.
Matrix entries of magnitude above 255
 - `512*r - 256*g` is an example where the clamping would have a big effect
 - The rounding at the end is wrong by 0.5 (out of 255) : adding 64 before the right shift would solve this.

