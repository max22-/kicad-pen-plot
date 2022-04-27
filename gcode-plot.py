#!/usr/bin/env python3

import sys
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
    


gcode += "( PADS )"

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
        radius = (sx - pen_diameter) / 2
        gcode += "( circle )\n"
        gcode += f"G00 X{xc+radius:.3f} Y{yc:.3f}\nG01 Z0 F{feed_rate:.3f}\n"
        gcode += f"G03 X{xc:.3f} Y{yc+radius:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
        gcode += f"G03 X{xc-radius:.3f} Y{yc:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
        gcode += f"G03 X{xc:.3f} Y{yc-radius:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
        gcode += f"G03 X{xc+radius:.3f} Y{yc:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
    elif shape == PAD_SHAPE_RECT:
        gcode += "( rect )\n"
        gcode += f"G00 X{xc + (sx - pen_diameter) / 2 : .3f} Y{yc + (sy - pen_diameter) / 2 : .3f}\n"
        gcode += f"G01 Z0 F{feed_rate:.3f}\n"
        gcode += f"G01 X{xc - (sx - pen_diameter) / 2 : .3f} Y{yc + (sy - pen_diameter) / 2 : .3f}\n"
        gcode += f"G01 X{xc - (sx - pen_diameter) / 2 : .3f} Y{yc - (sy - pen_diameter) / 2 : .3f}\n"
        gcode += f"G01 X{xc + (sx - pen_diameter) / 2 : .3f} Y{yc - (sy - pen_diameter) / 2 : .3f}\n"
        gcode += f"G01 X{xc + (sx - pen_diameter) / 2 : .3f} Y{yc + (sy - pen_diameter) / 2 : .3f}\n"
    elif shape == PAD_SHAPE_OVAL:
        gcode += "( oval )\n"
        if sx == sy:
            radius = (sx - pen_diameter) / 2
            gcode += f"G00 X{xc+radius:.3f} Y{yc:.3f}\nG01 Z0 F{feed_rate:.3f}\n"
            gcode += f"G03 X{xc:.3f} Y{yc+radius:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
            gcode += f"G03 X{xc-radius:.3f} Y{yc:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
            gcode += f"G03 X{xc:.3f} Y{yc-radius:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
            gcode += f"G03 X{xc+radius:.3f} Y{yc:.3f} R{radius:.3f} F{feed_rate:.3f}\n"
        else:
            print("Warning: real ovals not suported (yet)", file = sys.stderr)
    else:
        print("Warning: unknown pad shape", file=sys.stderr)
        gcode += "( unknown pad shape )\n"
    gcode += f"G00 Z{z_safe:.3f}\n"


print(gcode)


#for m in dir(board.GetPads()[0]):
#    print(m)
