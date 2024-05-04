import numpy as np
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

k = 512

#Behold the sorting algorithm!
rDiff = sourceGraphic.matmul([r,k*(r-g)+.99,k*(r-b)+.99])
gDiff = sourceGraphic.matmul([g,k*(g-r)-.01,k*(g-b)+.99])
bDiff = sourceGraphic.matmul([b,k*(b-r)-.01,k*(b-g)-.01])

uu = u*(255/256)
# these vectors look like [max or 0, 0 or mid or 1, min or 0]
# sometimes off by 3/256 and I'm not sure why.
rParts,gParts,bParts = [x.matmul([r+g+b-2*u, r-g-b+u,r-b-g , u]) for x in [rDiff,gDiff,bDiff]]
maxmidmin = (rParts*0.5 + gParts*0.5) + bParts*0.5 # mid is in the interval [0.5,1]
#end of sorting algorithm


#We want (mid - min) / (max-min)
numer = 2*((g-.5)-b)
denom = 2*(r-b)
d1 = maxmidmin.matmul([numer, (numer+denom)/2, (2*denom-numer)/2] + [u]) # h,(h+1)/2, (2-h)/2 (2-a/b = (2b-a)/b)
div = maxmidmin.matmul([denom,denom,denom] + [u])
h = divideBlend(d1, div)

lum = (r+g+b)/3

#lumMat = np.array([(r+g+b)/3,(2*r-g-b+2*u)/4,(g-b+u)/2,u])
lumParts = sourceGraphic.matmul([lum,(3*lum)/2,(3*lum)/2,u])
#print(maxmidmin.matmul([2*r,2*(g)-u,2*b]).mkSVG())
#print(gParts.mkSVG())

maxmidminPretty = maxmidmin.matmul([2*r,2*(g)-u,2*b])

if __name__ == "__main__":
    import sys
    if len(sys.argv)==2:
        print(eval(sys.argv[1]).mkSVG())
    else:
        print("Usage(testing): python3 huerotate.py 'expr'\n    expr describes a filter\nOutputs an svg with the filter having id='generated'",file=sys.stderr)

