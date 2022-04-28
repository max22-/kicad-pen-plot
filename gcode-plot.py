#!/usr/bin/env python3

import sys
import math
from pcbnew import *

scale = 1000000 # conversion in micrometers (unit used by kicad)

layer = "F.Cu"

z_safe = 5
feed_rate = 500.0
pen_diameter = 0.4



gcode = f"""
G21
G92 X0 Y0 Z0

G00 Z{z_safe:.3f}
"""

if len(sys.argv) < 2:
    print(f"usage: {sys.argv[0]} file.kicad_pcb", file=sys.stderr)
    sys.exit(1)

board = LoadBoard(sys.argv[1])
for track in board.GetTracks():
    xs, ys = track.GetStart()
    xe, ye = track.GetEnd()
    if track.GetLayerName() == layer:
        if pen_diameter != track.GetWidth()/scale:
            print(f"Warning: pen diameter different from track width: {pen_diameter} <--> {track.GetWidth()/scale}", file=sys.stderr)
        gcode += f"G00 X{xs/scale:.3f} Y{ys/scale:.3f}\nG01 Z0 F{feed_rate:.3f}\n"
        gcode += f"G01 X{xe/scale:.3f} Y{ye/scale:.3f} F{feed_rate:.3f}\n"
        gcode += f"G00 Z{z_safe:.3f}\n"
    


gcode += "( PADS )\n"

# x, y : center
# d : diameter
# f : feed rate
# step : length of each line segment making the circle
def circle(x, y, d, f, step = 0.1):
    gcode = f"( circle )\nG00 X{x+d/2:.3f} Y{y:.3f}\nG01 Z0 F{f:.3f}\n"
    n = math.floor(math.pi * d / step)
    theta = 2 * step / d
    for i in range(n):
        px = x + d/2 * math.cos(i * theta)
        py = y + d/2 * math.sin(i * theta)
        gcode += f"G01 X{px:.3f} Y{py:.3f} F{f}\n"
    gcode += f"G01 X{x+d/2:.3f} Y{y:.3f}\n"
    return gcode

def rectangle(xc, yc, sx, sy, angle, f):
    gcode = "( rect )\n"
    gcode += f"G00 X{xc + sx / 2 : .3f} Y{yc + sy / 2 : .3f}\n"
    gcode += f"G01 Z0 F{f:.3f}\n"
    gcode += f"G01 X{xc - sx / 2 : .3f} Y{yc + sy / 2 : .3f} F{f:.3f}\n"
    gcode += f"G01 X{xc - sx / 2 : .3f} Y{yc - sy / 2 : .3f} F{f:.3f}\n"
    gcode += f"G01 X{xc + sx / 2 : .3f} Y{yc - sy / 2 : .3f} F{f:.3f}\n"
    gcode += f"G01 X{xc + sx / 2 : .3f} Y{yc + sy / 2 : .3f} F{f:.3f}\n"
    gcode += "\n"
    return gcode

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
        gcode += circle(xc, yc, sx - pen_diameter, feed_rate)
    elif shape == PAD_SHAPE_RECT:
        gcode += rectangle(xc, yc, sx - pen_diameter, sy - pen_diameter, 0, feed_rate)
    elif shape == PAD_SHAPE_OVAL:
        gcode += "( oval )\n"
        if sx == sy:
            gcode += circle(xc, yc, sx - pen_diameter, feed_rate)
        else:
            print("Warning: real ovals not suported (yet)", file = sys.stderr)
    else:
        print("Warning: unknown pad shape", file=sys.stderr)
        gcode += "( unknown pad shape )\n"
    gcode += f"G00 Z{z_safe:.3f}\n\n"


print(gcode)


#for m in dir(board.GetPads()[0]):
#    print(m)
