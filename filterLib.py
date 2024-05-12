#import numpy

def paramsToString(params):
    return " ".join(k+f"='{v}'" for k,v in params.items())

class Effect():
    """Filter effects"""
    rendering=False
    def __init__(self,elementName):
        self.elementName=elementName
        self.ref=None
        self.params={}
        self.innerElements=[]
        self.clon=None
    def mkSVG(self,*args,**kwargs):
        f = self.mkFilter(*args,**kwargs)
        return "<svg xmlns='http://www.w3.org/2000/svg'><defs>"+f+"</defs></svg>"
    def mkFilter(self,**filterParams):
        params={"id":"generated",
                "color-interpolation-filters":"sRGB", # This is morally right lots of the time, even if it looks worse
                "x":"0%","y":"0%","width":"100%","height":"100%"} # For the filters I'm considering at the moment,we don't need anything outside the source bounding box.
        params.update(filterParams)

        output=['<filter '+paramsToString(params)+'>']
        self.render([0],output)
        output.append("</filter>")
        self.resetRef()
        return "\n".join(output)
    def render(self,counter,output):
        if self.ref is not None:
            return self.ref
        if self.rendering:
            raise Exception("Loop of effect dependencies")
        self.rendering=True
        params = {"in"+(str(i+1) if i>0 else ""):ef.render(counter,output) for i,ef in enumerate(self.inputs)}
        params.update(self.params)
        self.ref="ef"+str(counter[0])
        params["result"]=self.ref
        output.append(f'<{self.elementName} {paramsToString(params)}>')
        for line in self.innerElements:
            output.append(line)
        output.append(f'</{self.elementName}>')
        self.rendering=False
        counter[0]+=1
        return self.ref
    def resetRef(self):
        if self.ref is not None:
            self.ref=None
            for k in self.inputs:
                k.resetRef()
    def matmul(self,matrix):
        """multiply each pixel's RGBA vector by a matrix (extended to be 4 by 5)"""
        return MatrixEffect(matrix,self)
    def addInner(self,inner):
        self.innerElements.append(inner)
    def __radd__(self,other):
        return self.__add__(other)
    def __rmul__(self,other):
        return self.__mul__(other)
    def __mul__(self,other):
        return ExpressionEffect(0.0,1.0,0.0,0.0,self,None).__mul__(other)
    def __truediv__(self,other):
        return self*(other**(-1))
    def __add__(self,other):
        return ExpressionEffect(0.0,1.0,0.0,0.0,self,None).__add__(other)
    def __sub__(self,other):
        return self.__add__((-1)*other)
    def __rsub__(self,other):
        return other + ((-1)*self)
    def __str__(self):
        return f"<{self.__class__.__name__}({','.join(str(x) for x in self.inputs)})>"
    def then(self,other):
        """Combine 2 Effects (does not intelligently combine expressions"""
        return other.compose(self)
    def compose(self,other,top=True):
        """apply self to other (replace sourceGraphic with other inside self) """
        abstract
    def _start_compose(self,other):
        if self.rendering:
            raise Exception("Loop of effect dependencies")
        self.rendering=True
        return [x.compose(other,False) for x in self.inputs]

    def _end_compose(self,top,result):
        self.rendering=False
        self.ref=result
        if top:
            self.resetRef()
        return result



class SourceGraphic(Effect):
    """dummy Effect to represent the null element"""
    def __init__(self):
        pass
    def mkFilter(self):
        raise Exception("Don't bother making a filter that does nothing")
    def render(self,*args):
        return "SourceGraphic"
    def resetRef(self):
        pass
    def __str__(self):
        return f"<{self.__class__.__name__}>"
    def then(self,other):
        return other
    def compose(self,other,top=True):
        return other

sourceGraphic=SourceGraphic()

def extend(matrix):
    m = list(map(list,matrix))
    assert 1<=len(m)<=5,m
    for r in m:
        assert len(r)<=5,m
    if len(m)==5:
        assert m[-1]==[0,0,0,0,1],m[-1]
        m=m[:-1]
    newm =[[0]*5 for i in range(4)]
    for i in range(4):
        newm[i][i]=1
    for i,r in enumerate(m):
        for j,v in enumerate(r):
            newm[i][j]=v
    return newm

def matToValues(mat):
    """Turns a 4 by 5 matrix into something suitable for feColorMatrix's values attribute"""
    mat=extend(mat)
    r = ",".join(" ".join(map(str,x)) for x in mat)
    assert r.count(",")==3,r
    assert r.count(" ")==4*4,r
    return r


class MatrixEffect(Effect):
    def __init__(self,matrix,in1):
        """matrix: an iterable of 4 iterables of length 5
           in1: the input effect"""
        super().__init__("feColorMatrix")
        self.inputs=[in1]
        self.matrix = extend(matrix)
        #self.params["type"]="matrix" this is the initial value
        self.params["values"]=matToValues(self.matrix)
    def compose(self,other,top=True):
        if self.ref is not None:
            return self.ref
        inps = self._start_compose(other)
        return self._end_compose(top,MatrixEffect(self.matrix,*inps))


class ExpressionEffect(Effect):
    """A balance between trying to be clever so that avoidable clipping doesn't happen
       and trying not to be too clever so that clipping happens predictably
       Warning: watch out for the alpha channel. This uses pre-multiplied alpha,"""
    def __init__(self,k1,k2,k3,k4,in1,in2):
        super().__init__("feComposite")
        self.params["operator"] = "arithmetic"
        self.inputs=[in1,in2]
        self.params["k1"]=k1
        self.params["k2"]=k2
        self.params["k3"]=k3
        self.params["k4"]=k4
        self.ks=(k1,k2,k3,k4)
        if in2 is None:
            assert k1==0.0 and k3==0.0
            l = comLinear(k2,k4)
            self.inner = ComponentEffect(in1,l,l,l,l)
    def render(self,*args,**kwargs):
        if self.inputs[1] is None:
            return self.inner.render(*args,**kwargs)
        else:
            return super().render(*args,**kwargs)
    def __add__(self,other):
        if isinstance(other,int):
            other=float(other)
        if isinstance(other,float):
            (k1,k2,k3,k4) = self.ks
            return ExpressionEffect(k1,k2,k3,k4+other,*self.inputs)
        elif isinstance(other,ExpressionEffect):
            if (other.inputs[0] is self.inputs[0] and
                  (other.inputs[1] is self.inputs[1] or other.inputs[1] is None or self.inputs[1] is None)):
                return ExpressionEffect(*[a+b for a,b in zip(self.ks,other.ks)],
                                        self.inputs[0], self.inputs[1] or other.inputs[1])
            elif ((other.inputs[0] is self.inputs[1] or self.inputs[1] is None) and
                  (other.inputs[1] is self.inputs[0] or other.inputs[1] is None)):
                (k1,k2,k3,k4) = self.ks
                (o1,o2,o3,o4) = other.ks
                return ExpressionEffect(k1+o1,k2+o3,k3+o2,k4+o4,
                                        self.inputs[0], self.inputs[1] or other.inputs[0])
            elif other.inputs[1] is None:
                (k1,k2,k3,k4) = other.ks
                return ExpressionEffect(0.0 ,1.0, k2, k4 ,self, other.inputs[0])
        if isinstance(other,Effect):
            if self.inputs[0] is other:
                (k1,k2,k3,k4) = self.ks
                return ExpressionEffect(k1, k2+1, k3, k4 ,*self.inputs)
            elif self.inputs[1] is other:
                (k1,k2,k3,k4) = self.ks
                return ExpressionEffect(k1, k2, k3+1, k4 ,*self.inputs)
            elif self.inputs[1] is None:
                (k1,k2,k3,k4) = self.ks
                return ExpressionEffect(0.0 ,k2, 1.0, k4 ,self.inputs[0], other)
            else:
                return ExpressionEffect(0.0,1.0,1.0,0.0,self,other)
        else:
            return NotImplemented
    def __mul__(self, other):
        if isinstance(other,int):
            other=float(other)
        if isinstance(other,float):
            return ExpressionEffect(*[k*other for k in self.ks],*self.inputs)
        elif isinstance(other,ExpressionEffect):
            if self.inputs[1] is None and other.inputs[1] is None:
                (k1,k2,k3,k4) = self.ks
                (o1,o2,o3,o4) = other.ks
                return ExpressionEffect(k2*o2, k2*o4, k4*o2, k4*o4, self.inputs[0], other.inputs[0])
            elif other.inputs[1] is None:
                (o1,o2,o3,o4) = other.ks
                return ExpressionEffect(o2, o4, 0.0, 0.0, self, other.inputs[0])
        if isinstance(other,Effect):
            if self.inputs[1] is None:
                (k1,k2,k3,k4) = self.ks
                return ExpressionEffect(k2, 0.0, k4, 0.0, self.inputs[0], other)
            else:
                return ExpressionEffect(1.0, 0.0, 0.0, 0.0, self, other)
        else:
            return NotImplemented
    def __str__(self):
        return f"<{self.__class__.__name__}({','.join(str(x) for x in self.inputs)})>"
    def compose(self,other,top=True):
        if self.ref is not None:
            return self.ref
        if self.inputs[1] is None:
            return self.inner.compose(other,top=top)
        else:
            inps = self._start_compose(other)
            return self._end_compose(top,ExpressionEffect(*self.ks,*inps))
    def resetRef(self,*args,**kwargs):
        if self.inputs[1] is None:
            return self.inner.resetRef(*args,**kwargs)
        else:
            return super().resetRef(*args,**kwargs)

class ComponentEffect(Effect):
    """Warning: uses premultiplied alpha"""
    def __init__(self,in1,*components):
        super().__init__("feComponentTransfer")
        self.inputs=[in1]
        self.components=tuple(str(c) for c in components)
        assert len(components)<=4
        for channel,component in zip("RGBA",components):
            self.addInner(f"<feFunc{channel} {component} />")
    def compose(self,other,top=True):
        if self.ref is not None:
            return self.ref
        inps = self._start_compose(other)
        return self._end_compose(top,ComponentEffect(*inps,*self.components))


class Gamma():
    def __init__(self,amplitude,exponent,offset):
        self.amplitude = amplitude
        self.exponent = exponent
        self.offset = offset
    def __str__(self):
        return comGamma(self.amplitude,self.exponent,self.offset)
    def __pow__(self,exp):
        assert self.offset==0.0
        return Gamma(self.amplitude**(exp),self.exponent*exp,0.)
    def __mul__(self,other):
        if isinstance(other,int):
            other=float(other)
        if isinstance(other,float):
            return Gamma(self.amplitude*other,self.exponent,self.offset*other)
        return NotImplemented
    def __add__(self,other):
        if isinstance(other,int):
            other=float(other)
        if isinstance(other,float):
            return Gamma(self.amplitude,self.exponent,self.offset+other)
        return NotImplemented
    def __radd__(self,other):
        return self.__add__(other)
    def __rmul__(self,other):
        return self.__mul__(other)
    def __truediv__(self,other):
        return self.__mul__(1.0/other)
    def __rtruediv__(self,other):
        if isinstance(other,int):
            other=float(other)
        if isinstance(other,float):
            return other*(self**(-1))

γ = Gamma(1.,1.,0.)

def comGamma(amplitude,exponent,offset):
    return " ".join(["type='gamma'"]+[f"{a}='{b}'" for a,b in locals().items()])

def comTable(tableValues):
    return "type='table' tableValues="+ repr(" ".join(map(str,tableValues)))

def comDiscrete(tableValues):
    return "type='discrete' tableValues="+ repr(" ".join(map(str,tableValues)))

def comLinear(slope,intercept):
    return " ".join(["type='linear'"]+[f"{a}='{b}'" for a,b in locals().items()])

def comId():
    return "type='identity'"


class FloodEffect(Effect):
    def __init__(self,color):
        super().__init__("feFlood")
        self.inputs=[]
        self.params["flood-color"]=color
    def compose(self,other,top=True):
        return self

class BlendEffect(Effect):
    def __init__(self,mode,in1,in2):
        super().__init__("feBlend")
        self.inputs=[in1,in2]
        self.params["mode"]=mode
    def compose(self,other,top=True):
        if self.ref is not None:
            return self.ref
        inps = self._start_compose(other)
        return self._end_compose(top,BlendEffect(self.params["mode"],*inps))

def divideGamma(dividend,blueDivisor,limit=0.1):
    """Divide the red and green components of the dividend by the blue component of the divisor"""
    return ((ComponentEffect(blueDivisor,comLinear(0,0),comLinear(0,0), limit/γ,comLinear(0,1))
      + dividend).matmul(
        [[1.,0.,0.,0.,0.],
         [0.,1.,0.,0.,0.],
         [0.,0.,0.,0.,0.],
         [0.,0.,1.,0.,0.],
            ]) + FloodEffect("#000000FF"))
    """ .matmul(
               [[1/limit,0.,0.,0.,0.],
                [0.,1./limit,0.,0.,0.],
                [0.,0.,1.,0.,0.],
                [0.,0.,0.,0.,1.],
                    ]
                )"""

def divideGammaAlt(dividend,redDivisor,limit=0.1):
    """Divide the color components of the dividend by the red component of the divisor"""
    return ComponentEffect(redDivisor, limit/γ).matmul(
        [[1.,0.,0.,0.,0.],
         [1.,0.,0.,0.,0.],
         [1.,0.,0.,0.,0.],
         [0.,0.,0.,0.,1.],
            ])*dividend


def divideAlpha(dividend,redDivisor,limit=0.1):
    scaledDown = ComponentEffect(dividend, comId(),comId(),comId(),comLinear(0.,limit))
    divAlpha = redDivisor.matmul(
        [[0.,0.,0.,0.,0.],
         [0.,0.,0.,0.,0.],
         [0.,0.,0.,0.,0.],
         [1.,0.,0.,0.,-limit]])
    return (scaledDown + divAlpha).matmul(
               [[1.,0.,0.,0.,0.],
                [0.,1.,0.,0.,0.],
                [0.,0.,1.,0.,0.],
                [0.,0.,0.,0.,1.]])
def divideAlpha2(dividend,redDivisor,limit=0.1):
    scaledDown = ComponentEffect(dividend, comId(),comId(),comId(),comLinear(0.,limit))
    divAlpha = redDivisor.matmul(
        [[0.,0.,0.,0.,0.],
         [0.,0.,0.,0.,0.],
         [0.,0.,0.,0.,0.],
         [1.,0.,0.,0.,-limit]])
    return (scaledDown + divAlpha) + FloodEffect("#000000FF")

def divideBlend(dividend,divisor):
    inv = comLinear(-1.,1.)
    divisor = ComponentEffect(divisor,inv,inv,inv, comId())
    return BlendEffect("color-dodge", divisor, dividend)

def preserveAlpha(effect):
    """Apply the input alpha"""
    return



