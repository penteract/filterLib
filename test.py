import traceback,sys

cases=[]

def test(testCase,name=None):
    if name is None: name=testCase.__name__
    print("<!-- ======== Test :",name,"======== -->")
    try:
        result = testCase().mkFilter(id=name, **{"color-interpolation-filters":"sRGB"})
        # results are easier to see in the sRGB color space
        print(result)
    except Exception as e:
        print("<!--")
        traceback.print_exc(file=sys.stdout)
        print("-->")
    else:
        cases.append(name)
        print("<!-- No Exceptions -->")
    print("<!-- ======== end of Test",name," ======== -->")
    return None

import filterLib

"""
#Test the testing code
@test
def divZeroFail():
    return (1/0)

@test
def divOne():
    return (1/1)
"""


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

hue180 = getmat(np.pi)

print('<svg xmlns="http://www.w3.org/2000/svg">')

from filterLib import *

@test
def colorMatrix():
    matrix = np.array(hue180)
    filtr = sourceGraphic.matmul(matrix)
    return filtr
@test
def simpleExpression():
    filtr = sourceGraphic*sourceGraphic
    return filtr
@test
def combiningExpression():
    filtr = sourceGraphic*sourceGraphic+sourceGraphic
    filtr2 = 3*filtr+sourceGraphic
    filtr3 = filtr+filtr2+.1 # This should be a single filterEffect
    filtr4 = filtr3*sourceGraphic
    filtr5 = filtr4+.2
    return filtr5
@test
def componentTransfer():
    cr = comGamma(1,-1,-1)
    cg = comDiscrete([0,0.5,1])
    return ComponentEffect(sourceGraphic,cr,cg)

@test
def composedComponentsDivision():
    cr = comGamma(.5,1,0.5)
    cg = comGamma(0,1,0)
    a = ComponentEffect(sourceGraphic,cr,cg)
    cr2 = comGamma(1,-1,-1)
    b = ComponentEffect(a,cr2)
    cr3 = comDiscrete([0,.3,.6,1.])
    c = ComponentEffect(b,cr3)
    return c

@test
def flood():
    return FloodEffect("#F0F8")

@test
def alphaDivision():
    #non-premul
    m1 = sourceGraphic.matmul(
        [[0.,0.,0.,0.,0.],#r
         [0.,0.,0.,0.,0.],#b
         [0.,0.,0.,0.,0.],#g
         [.5,0.,0.,0.,0.] #α
            ])
    flood = FloodEffect("#FF00007F")
    c = m1+flood # premul
    m2 = c.matmul(#non-premul, so division by α has occured
        [[2.,0.,0.,0.,-1.],#r
         [0.,0.,0.,0.,0.],#b
         [0.,0.,0.,0.,0.],#g
         [0.,0.,0.,0.,1.] #α
            ])
    cr3 = comDiscrete([0,.3,.6,1.])
    c = ComponentEffect(m2,cr3)
    return c

def test2(fn):
    name = fn.__name__
    test(fn)
    cr3 = comDiscrete([0,.3,.6,1.])
    test(lambda:ComponentEffect(fn(),cr3),name+"_discrete")
@test2
def libDivGamma():
    transformed = sourceGraphic.matmul([[0]*3]*2+[[.5,0,0,0,.5]] )
    return divideGamma(FloodEffect("#FF0000") , transformed,limit=0.5)*2-1
@test2
def libDiv2():
    transformed = sourceGraphic.matmul([[.5,0,0,0,.5]] )
    return divideBlend(FloodEffect("#7F0000FF") , transformed)*2-1

#print("</defs>")
#print("<rect x='0' y='0' width='100' height='100' />")
print("<image x='0' y='0' href='./tst.bmp'/>")
print("<text x='256' y='14'> Unfiltered </text>")
for i,name in enumerate(cases):
    print(f"<image x='0' y='{(i+1)*16}' href='./tst.bmp' filter='url(#{name})'/>")
    print(f"<text x='256' y='{(i+2)*16-2}'> {name} </text>")
    if "_discrete" in name:
        print(f"<rect x='{256/3-0.5}' y='{16*(i+2)-24}' width='1' height='16' fill='#0f7'/>")

    #print(f"<image x='{i*16}' y='0' href='./tst.bmp' />")
print(f"<rect x='{256/3-0.5}' y='{16*6-24}' width='1' height='16' fill='#0f7'/>")
print(f"<rect x='{256/3-0.5}' y='{16*8-24}' width='1' height='16' fill='#0f7'/>")
print("</svg>")
