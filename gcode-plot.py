#!/usr/bin/env python3

import sys
import math
from pcbnew import *
from gcode import *

if len(sys.argv) < 2:
    print(f"usage: {sys.argv[0]} file.kicad_pcb", file=sys.stderr)
    sys.exit(1)

scale = 1000000 # conversion in micrometers (unit used by kicad)

layer = "F.Cu"

state = {"pos" : (0, 0, 0), "pen_diameter": 0.4, "feed_rate": 500, "z_safe": 5}

gcode = Comment(f"Layer: {layer}") >> G21() >> G92(X=0, Y=0, Z=0) >> ZSafe()


board = LoadBoard(sys.argv[1])
for track in board.GetTracks():
    xs, ys = track.GetStart()
    xe, ye = track.GetEnd()
    if track.GetLayerName() == layer:
        #if pen_diameter != track.GetWidth()/scale:
        #    print(f"Warning: pen diameter different from track width: {pen_diameter} <--> {track.GetWidth()/scale}", file=sys.stderr)
        gcode >> G00(X = xs / scale, Y = ys / scale) >> G01(X = xs / scale, Y = ys / scale, Z = 0)
        gcode >> G01(X = xe / scale, Y = ye / scale)
        gcode >> ZSafe()
        
gcode >> Comment("PADS")

for pad in board.GetPads():
    xc, yc = pad.GetCenter()
    sx, sy = pad.GetSize()
    xc /= scale
    yc /= scale
    sx /= scale
    sy /= scale
    shape = pad.GetShape()
    orientation = pad.GetOrientationDegrees()
    #print(f"orientation = {orientation}")
    if shape == PAD_SHAPE_CIRCLE:
        gcode >> CirclePadContour(sx).translate((xc, yc))
    elif shape == PAD_SHAPE_RECT:
        gcode >> RectanglePadContour(sx, sy).rotate(math.radians(orientation)).translate((xc, yc))
    elif shape == PAD_SHAPE_OVAL:
        gcode >> Comment("Oval")
        if sx == sy:
            gcode >> CirclePadContour(sx).translate((xc, yc))            
        else:
            print("Warning: real ovals not suported (yet)", file = sys.stderr)
    else:
        print("Warning: unknown pad shape", file=sys.stderr)
        Comment("unknown pad shape")
    gcode >> ZSafe()

gcode >> G00(X = 0, Y = 0) >> PowerOff()


print(gcode.flip_y().translate((0, 45)).run(tr = lambda x: x, state = state))


#for m in dir(board.GetPads()[0]):
#    print(m)
