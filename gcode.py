import math

class GCode:
       
    def __rshift__(self, other):
        return Sequence([self, other])

    def transform(self, tr):
        return Transform(self, tr)

    def translate(self, vec):
        return self.transform(lambda p: (p[0] + vec[0], p[1] + vec[1]))

    def rotate(self, angle):
        return self.transform(lambda p: (p[0] * math.cos(angle) - p[1] * math.sin(angle), p[0] * math.sin(angle) + p[1] * math.cos(angle)))

    def flip_y(self):
        return self.transform(lambda p: (p[0], -p[1]))


class Sequence(GCode):
    def __init__(self, ops = []):
        self.ops = ops

    def __rshift__(self, other):
        self.ops.append(other)
        return self
        
    def run(self, tr, state):
        res = ""
        for o in self.ops:
            s = o.run(tr, state)
            if s != "":
                res += s
                res += "\n"
        return res
                    
class Transform(GCode):
    def __init__(self, op, f):
        self.op = op
        self.f = f

    def run(self, tr, state):
        return self.op.run(lambda x: tr(self.f(x)), state)

class G21(GCode):
    def run(self, tr, state):
        return "G21"
    
class G92(GCode):
    def __init__(self, X=None, Y=None, Z=None):
        if X is None and Y is None and Z is None:
            raise RuntimeError("Please provide at least one argument for X, Y or Z")
        self.x = X
        self.y = Y
        self.z = Z

    def run(self, tr, state):
        (x2, y2) = tr((self.x, self.y))
        (_, _, z) = state["pos"]
        state["pos"] = (x2, y2, z)
        x_str = "" if self.x is None else f"X{x2:.3f} "
        y_str = "" if self.y is None else f"Y{y2:.3f} "
        z_str = "" if self.z is None else f"X{self.z:.3f} "
        return f"G92 {x_str}{y_str}{z_str}"

class Move(GCode):
    def __init__(self, command, X, Y, Z):
        self.command = command
        self.x = X
        self.y = Y
        self.z = Z

    def coords_string(self, tr, state):
        x1, y1, z1 = state["pos"]
        (x2, y2) = tr((self.x, self.y))
        z2 = self.z if self.z is not None else z1
        state["pos"] = (x2, y2, z2)
        
        x_str = f"X{x2:.3f} " if x2 != x1 else ""
        y_str = f"Y{y2:.3f} " if y2 != y1 else ""
        z_str = f"Z{z2:.3f} " if z2 != z1 else ""
        res = x_str + y_str + z_str
        return res
        

class G00(Move):
    def __init__(self, X, Y, Z=None):
        super().__init__("G00", X, Y, Z)

    def run(self, tr, state):
        coords_str = self.coords_string(tr, state)
        if coords_str != "":
            res = f"G00 {coords_str}"
        else:
            res = ""
        return res

class G01(Move):
    def __init__(self, X, Y, Z=None, F=None):
        super().__init__("G01", X, Y, Z)
        self.f = F

    def run(self, tr, state):
        coords_str = self.coords_string(tr, state)
        if self.f != None:
           state["feed_rate"] = self.f
        feed_rate = state["feed_rate"]
        f_str = f"F{feed_rate:.3f}"
        if coords_str != "":
            res = f"G01 {coords_str}{f_str}"
        else:
            res = ""
        return res

class Tone(GCode):
    def __init__(self, freq=440, dur=0.5):
        self.freq = freq
        self.dur = dur

    def run(self, tr, state):
        ms = math.floor(self.dur * 1000)
        return f"M300 S{self.freq} P{ms}"

class ZSafe(GCode):
    def run(self, tr, state):
        (x, y, z) = state["pos"]
        z_safe = state["z_safe"]
        state["pos"] = (x, y, z_safe)
        if z != z_safe:
            return f"G00 Z{z_safe}"
        else:
            return ""

class Comment(GCode):
    def __init__(self, msg):
        self.msg = msg
    def run(self, tr, state):
        return f"( {self.msg} )"

class DisableSteppers(GCode):
    def run(self, tr, state):
        return "M84"


class PowerOff(GCode):
    def run(self, tr, state):
        return "M80"
               

def Rectangle(w, h):
    return Comment("Rectangle") >> G00(X=0, Y=0) >> G01(X=0, Y=0, Z=0) >> G01(X=w, Y=0) >> G01(X=w, Y=h) >> G01(X=0, Y=h) >> G01(X=0, Y=0)

class RectangleInnerContour(GCode):
    def __init__(self, w, h):
        self.w = w
        self.h = h
    def run(self, tr, state):
        pd = state["pen_diameter"]
        if pd > self.w or pd > self.h:
            raise RuntimeError(f"Pen (d={pd}) too big for rectangle with w={self.w}, h={self.h}")
        return Rectangle(self.w - pd, self.h - pd).run(tr, state)

# step : length of each line segment making the circle
def Circle(d, step=0.01):
    res = (
        Comment("Circle")
        >> G00(X = d/2, Y = 0)
        >> G01(X = d/2, Y = 0)
    )
    n = math.floor(math.pi * d / step)
    theta = 2 * step / d
    for i in range(n):
        res >> G01(X = d/2 * math.cos(i * theta), Y = d/2 * math.sin(i * theta))
    res >> G01(X = d/2, Y = 0)
    return res

class CircleInnerContour(GCode):
    def __init__(self, d, step = 0.01):
        self.d = d
        self.step = step

    def run(self, tr, state):
        pd = state["pen_diameter"]
        if pd > self.d:
            raise RuntimeError(f"Pen (d={pd}) too big for circle with d={self.d}")
        return Circle(self.d - pd, self.step).run(tr, state)

if __name__ == "__main__":
    op = (
      G21()
      >> G92(X=0, Y=0, Z=0)
      >> G00(X=0, Y=0, Z=5)
      >> G01(X=10, Y=0, Z=0, F=500).translate((5, 5)).rotate(math.radians(45))
      >> ZSafe()
      >> Tone()
      >> (Rectangle(45, 53).translate((10, 5)).rotate(math.radians(45)))
      >> ZSafe()
      >> Circle(10).translate((-10, 0))
      >> ZSafe()
      >> G00(X = 0, Y = 0)
      >> PowerOff()
    )
    print(op.run(tr = lambda x: x, state = {"pos": (0, 0, 0), "pen_diameter": 0.4, "feed_rate": 500, "z_safe": 5}))
    
