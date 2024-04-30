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

print((filtr*.8+.1+0*sourceGraphic).mkFilter())

