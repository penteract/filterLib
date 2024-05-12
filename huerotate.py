import numpy as np
import sys
lumr = .213
lumg=.715
lumb=.072
lum3 = [lumr,lumg,lumb]
lumd = np.diag([lumr,lumg,lumb])
kmat = np.mat([lum3]*3)
cosmat =  np.identity(3)-kmat
sinmat = np.mat([
    [-lumr,-lumb,1-lumb],
    [.143,.140,-.283],
    [lumr-1,lumg,lumb]])
def getmat(θ):
    return kmat + np.cos(θ)*cosmat + np.sin(θ)*sinmat
"""
for i in range(8):
    print(i)
    for v in np.linalg.eig(getmat(i))[1]:
        if np.linalg.norm(v.imag)<0.01:
            print(v.real)
    #print(np.linalg.eig(getmat(i)))
"""
def matstr(m):
    assert m.shape==(3,3)
    #" ".join([" ".join( str(x[0,0]) for x in )+" 0 0" for row in np.array(m))

hue180 = getmat(np.pi)

back = np.linalg.inv(hue180) # hue180 is self-inverse, but if it wasn't, this would give the answer we care about

sz=256
if False:
    a_in = (np.fromiter(np.ndindex(sz,sz,sz),dtype="3int")/(sz-1)).transpose()
    a = back*a_in
    b = np.clip(a,0,1)

    print("Fraction of the color cube which is reachable after hue-rotate(180) and clipping:",
          np.sum(np.all(a==b ,axis=0))/(sz**3))
    print("equal to the fraction of the color space which is not clipped after the transformation")
    a2 = hue180*(a_in*.8+.1)
    b2 = np.clip(a,0,1)
    print("Fraction of the color cube which is not clipped after invert(0.9) hue-rotate(180):",np.sum(np.all(a2==b2 ,axis=0))/(sz**3))
    #sum(k[0] and k[1] and k[2])

from filterLib import *

filtr = sourceGraphic.matmul(np.array(hue180))

anim = ";".join( matToValues(np.array(getmat(i*np.pi*2/12))) for i in range(12+1) )
#filtr.addInner(
#    f'<animate attributeName="values" values={repr(anim)} dur=10s repeatCount="indefinite" />')

#print((filtr*sourceGraphic).mkSVG())

r=np.array([1.,0.,0.,0.,0.])
g=np.array([0.,1.,0.,0.,0.])
b=np.array([0.,0.,1.,0.,0.])
a=np.array([0.,0.,0.,1.,0.])
u=np.array([0.,0.,0.,0.,1.])


add = 1.
sub = 0.0

k=2550 # In Firefox, this effectively gets clamped to 255 (although this doesn't cause a problem). In chromium, this needs to be larger than 255 (I assume some things aren't being discretized to sRGB bytes)


rDiff = sourceGraphic.matmul([r,k*(r-g)+u*add,k*(r-b)+u*add])
gDiff = sourceGraphic.matmul([g,k*(g-r)-u*sub,k*(g-b)+u*add])
bDiff = sourceGraphic.matmul([b,k*(b-r)-u*sub,k*(b-g)-u*sub])


uu = u*(255/256)
#Behold the sorting algorithm!

# these vectors look like [max or 0, 0 or mid or 1, min or 0]
half = 0.5

rParts,gParts,bParts = [x.matmul([r+g+b-2*u, r-g-b+u,r-b-g , u]) for x in [rDiff,gDiff,bDiff]]
maxmidmin = (rParts*half + gParts*half) + bParts*half # mid is in the interval [0.5,1], the others are in [0,0.5]
#end of sorting algorithm


#We want (mid - min) / (max-min)
numer = 2*((g-half*u)-b)
denom = 2*(r-b)
three = 3

# h,(h+1)/3, (2-h)/3 (2-a/b = (2b-a)/b)
d1 = maxmidmin.matmul([numer, (numer+denom)/three, (2*denom-numer)/three] + [u])
div = maxmidmin.matmul([u-denom,u-denom,u-denom] + [u])
h = BlendEffect("color-dodge", div, d1)

#,(h+1)/3, (2-h)/3 (2-a/b = (2b-a)/b)
d12 = maxmidmin.matmul([u, (numer+denom)/three, (2*denom-numer)/three] + [u])
div2 = maxmidmin.matmul([u*0,u-denom,u-denom] + [u])
uh12h = BlendEffect("color-dodge", div2, d12)

lum = (r+g+b)/3


maxmidminPretty = maxmidmin.matmul([r/half,(g-u*half)/half,b/half])

# There are a few options for how to do the next bit.
# What we want is f(3l,1-h)/f(3l,h) where f(x,y) = x/(y+1) if x<y else (3-x)/(2-y)
# this can be simplifiied into:
# (h+1)/(2-h) if 3l < min(h+1,2-h)
# (2-h)/(h+1) if 3l > max(h+1,2-h)
# (1-l)/l if h+1>3l>2-h
# l/(1-l) if 2-h>3l>h+1

#alternative:
# a,b <- (l>((h+1)/3) `excl` (((h+1)/3), l)) * (l>((2-h)/3) `excl` (l , (2-h)/3) )
# a/b



lumParts = sourceGraphic.matmul([lum,(3*lum)/three,(3*lum)/three,u])

c1c2 =  (uh12h - lumParts)*255 + 1.0

# (l>((h+1)/3) `excl` l) ,  (l>((2-h)/3) `excl` l)
lumexcls = BlendEffect("exclusion",lumParts,c1c2).matmul([u,b,g*0.5,u])
hexcls = BlendEffect("exclusion",uh12h,c1c2)
udividenddivisor = lumexcls*hexcls
divisor = udividenddivisor.matmul([u*0,u*0,u-g,u])

satscale = BlendEffect("color-dodge",  divisor, udividenddivisor).matmul([u*0.5,b,b,u])


#An orthogonal transformation sending setting the color cube to stand on the black corner,
# sending the white-black axis to (0.0,0.5,0.5) - (1.0,0.5,0.5)
lumMat = np.array([(r+g+b)/3,(2*r-g-b+2*u)/4,(g-b+u)/2,u])

lumMatI = np.array([(u-(r+g+b)/3),(2*r-g-b+2*u)/4,(g-b+u)/2,u])

lumSpaceI = sourceGraphic.matmul(lumMatI)
k = lumSpaceI*satscale*2 - 1*satscale + 0.5

lumMat2 = np.array([((r+g+b)/3),(2*r-g-b+2*u)/4,(g-b+u)/2,u])

invLum2 = np.linalg.inv(lumMat2[:3,:3])

invLum2 = np.concatenate((invLum2,
    np.transpose( [ [0,0,0], - np.matmul(invLum2, lumMat2[:3,4])]) ),
    axis=1)


result = (k).matmul(invLum2)


import math

def kprev(n,k):
    for i in range(k):
        n=math.nextafter(n,0)
    return n

#u*((255.0 + 1/255 - 0.5)/255)
#rDiff2 = sourceGraphic.matmul([r* ((0x90+1) /256 - 1*2**(-23)), #(128.496 - 0/257 + 0* (2**-25))/255,
#                               b*((0x90+1)/256) ,
#                               u*(0x01 - 1/255)/255,a])


# matrix entries other than bias get rounded to nearest 1/128
#r* ((0x90+1) /256 - 1*2**(-23)),
#b*((0x90+1)/256) ,



                               #kprev((128.0 - 1/257 + 0* (2**-25))/255 ,0),a])

# smallest value in 5th matrix column which gives color component 0xff (to within 2**-24)
#for webRender: 255.5/256 (boundary within 2**-24)
#for integer path: (255 - 1/256)/255 (boundary within (2**-28))
# smallest value which gives color component 0x1
# for integer path: (0x01 - 1.0/256)/255 (boundary within 2**-24)
# for webRender: (0.5 + 0.625/256)/256 (boundary within 2**-24)


                              # ((255.0 + .4/255 - 0.5)/255),a])
#k = rDiff2.matrix[1][2]
#print(k,k*255+0.5,file=sys.stderr)

if __name__ == "__main__":
    import sys
    if len(sys.argv)==2:
        print(eval(sys.argv[1]).mkSVG(**{"color-interpolation-filters":"sRGB"}) )
    else:
        print("Usage(testing): python3 huerotate.py 'expr'\n    expr describes a filter\nOutputs an svg with the filter having id='generated'",file=sys.stderr)

