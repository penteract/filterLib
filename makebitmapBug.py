import math
import sys

w=0x100
h=0x100

header=f"""
42 4d 36 {hex((w*h*3)//256)[-2:]} 00 00 00 00 00 00 36 00 00 00 28 00
00 00 40      00                   00 00 40 00 00 00 01 00 18 00 00 00
00 00 00 {hex((w*h*3)//256)[-2:]} 00 00 13 0b 00 00 13 0b 00 00 00 00
00 00 00 00 00 00"""

hdr=bytes([0x42,0x4d])
hsz=0x36
psz=3 # assume w*psz is a multiple of 4
hdr+=(hsz+psz*w*h).to_bytes(4,"little")
hdr+=bytes(int(k,16) for k in "00 00  00 00  36 00 00 00   28 00 00 00".split())
hdr+=w.to_bytes(4,"little")
hdr+=h.to_bytes(4,"little")
hdr+=bytes(int(k,16) for k in "01 00  18 00  00 00 00 00".split())
hdr+=(psz*w*h).to_bytes(4,"little")
hdr+=bytes(int(k,16) for k in "13 0b 00 00 13 0b 00 00  00 00 00 00 00 00 00 00".split())

assert len(hdr)==0x36

CENTER=0.58/1.5
NUMINCENTER=3

def g(x,y):
  return x

def r(x,y):
  return y

def b(x,y):
  return ((x*16)%256)+ y%16

k=10
sys.stdout.buffer.write(hdr + bytes(int((g(x,y) if c==1 else r(x,y) if c==2 else b(x,y))) for α in range(h) for β in range(w) for c in range(psz) for (x,y) in [(int(β/k+128-128/k), int(α/k+128- 128/k))] ))

#[(β,α)]))#

