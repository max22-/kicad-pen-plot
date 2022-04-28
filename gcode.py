import math

class GCode:
    def __init__(self):
        self.follow = []
        self.pen_diameter = 0.4
        self.feed_rate = 500.0
        self.z_safe = 5.0
        
    def run(self, tr):
        gcode = ""
        for f in self.follow:
            gcode += f.run(tr)
        return gcode

    def __rshift__(self, other):
        self.follow.append(other)
        return self

    def transform(self, tr):
        return Transform(self, tr)

    def translate(self, vec):
        return self.transform(lambda p: (p[0] + vec[0], p[1] + vec[1]))

    def rotate(self, angle):
        return self.transform(lambda p: (p[0] * math.cos(angle) - p[1] * math.sin(angle), p[0] * math.sin(angle) + p[1] * math.cos(angle)))
        
            
class Transform(GCode):
    def __init__(self, op, f):
        super().__init__()
        self.op = op
        self.f = f

    def run(self, tr):
        return self.op.run(lambda x: tr(self.f(x))) + super().run(tr)

class G21(GCode):
    def __init__(self):
        super().__init__()
    def run(self, tr):
        return "G21\n" + super().run(tr)
    
class G92(GCode):
    def __init__(self, X=None, Y=None, Z=None):
        super().__init__()
        if X is None and Y is None and Z is None:
            raise RuntimeError("Please provide at least one argument for X, Y or Z")
        self.x = X
        self.y = Y
        self.z = Z

    def run(self, tr):
        (x2, y2) = tr((self.x, self.y))
        x_str = "" if self.x is None else f"X{x2:.3f} "
        y_str = "" if self.y is None else f"Y{y2:.3f} "
        z_str = "" if self.z is None else f"X{self.z:.3f} "
        return f"G92 {x_str}{y_str}{z_str}\n" + super().run(tr)

class G00(GCode):
    def __init__(self, X=None, Y=None, Z=None):
        super().__init__()
        if X is None and Y is None and Z is None:
            raise RuntimeError("Please provide at least one argument for X, Y or Z")
        self.x = X
        self.y = Y
        self.z = Z

    def run(self, tr):
        (x2, y2) = tr((self.x, self.y))
        x_str = "" if self.x is None else f"X{x2:.3f} "
        y_str = "" if self.y is None else f"Y{y2:.3f} "
        z_str = "" if self.z is None else f"X{self.z:.3f} "
        return f"G00 {x_str}{y_str}{z_str}\n" + super().run(tr)

class G01(GCode):
    def __init__(self, X=None, Y=None, Z=None, F=None):
        super().__init__()
        if X is None and Y is None and Z is None:
            raise RuntimeError("Please provide at least one argument for X, Y or Z")
        self.x = X
        self.y = Y
        self.z = Z
        self.f = F

    def run(self, tr):
        (x2, y2) = tr((self.x, self.y))
        x_str = "" if self.x is None else f"X{x2:.3f} "
        y_str = "" if self.y is None else f"Y{y2:.3f} "
        z_str = "" if self.z is None else f"X{self.z:.3f} "
        f_str = "" if self.f is None else f"X{self.f:.3f} "
        return f"G01 {x_str}{y_str}{z_str}{f_str}\n" + super().run(tr)


if __name__ == "__main__":
    op = (
      G21()
      >> G92(X=0, Y=0, Z=0)
      >> G00(X=0, Y=0, Z=5)
      >> (G01(X=10, Y=0, Z=0, F=500)
          .translate((5, 5))
          .rotate(math.radians(45)))
    )
    print(op.follow)
    print(op.run(lambda x: x))
    
