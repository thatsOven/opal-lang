"""
MIT License

Copyright (c) 2020 thatsOven

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math

class Vector:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return str((self.x, self.y, self.z))

    def __del__(self):
        del self.x
        del self.y
        del self.z

    def copy(self):
        return Vector(self.x, self.y, self.z)

    def distance(a, b):
        return math.sqrt(((b.x - a.x) ** 2) + ((b.y - a.y) ** 2) + ((b.z - a.z) ** 2))

    def heading(self):
        return math.atan2(self.y, self.x)

    def cross(a, b):
        return Vector(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x
        )

    def dot(a, b):
        tmpA = a.copy().normalize()
        tmpB = b.copy().normalize()

        vals = (tmpA * tmpB).toList(3)
        sum_ = 0

        for val in vals:
            sum_ += val

        return sum_

    def magnitude(self, value=None):
        if value is None:
            return math.sqrt((self.x ** 2) + (self.y ** 2) + (self.z ** 2))
        else:
            self.normalize()

            self.x *= value
            self.y *= value
            self.z *= value

            return self.copy()

    def normalize(self):
        mag = self.magnitude()

        if mag == 0:
            self.x = 0
            self.y = 0
            self.z = 0
        else:
            self.x /= mag
            self.y /= mag
            self.z /= mag

        return self.copy()

    def limit(self, value):
        mag = self.magnitude()

        if mag > value:
            self.magnitude(value)

    def toList(self, dimension):
        return list(self)[:dimension]

    def fromList(self, xyz):
        if   len(xyz) == 0:
            return Vector()
        elif len(xyz) == 1:
            return Vector(xyz[0])
        elif len(xyz) == 2:
            return Vector(xyz[0], xyz[1])
        else:
            return Vector(xyz[0], xyz[1], xyz[2])

    def fromAngle(self, angle):
        # only works for 2d vectors
        return Vector(math.cos(angle), math.sin(angle))

    def getIntCoords(self):
        return Vector(int(self.x), int(self.y), int(self.z))

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    def __pos__(self):
        return Vector(self.x, self.y, self.z)

    def __abs__(self):
        return Vector(abs(self.x), abs(self.y), abs(self.z))

    def __iter__(self):
        return iter([self.x, self.y, self.z])

    def __round__(self, n=0):
        return Vector(round(self.x, n), round(self.y, n), round(self.z, n))

    def __add__(self, other):
        if type(other) == type(self):
            return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            return Vector(self.x + other  , self.y + other,   self.z + other)

    def __sub__(self, other):
        if type(other) == type(self):
            return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            return Vector(self.x - other  , self.y - other  , self.z - other)

    def __mul__(self, other):
        if type(other) == type(self):
            return Vector(self.x * other.x, self.y * other.y, self.z * other.z)
        else:
            return Vector(self.x * other  , self.y * other  , self.z * other)

    def __floordiv__(self, other):
        if type(other) == type(self):
            return Vector(self.x // other.x, self.y // other.y, self.z // other.z)
        else:
            return Vector(self.x // other  , self.y // other  , self.z // other)

    def __truediv__(self, other):
        if type(other) == type(self):
            return Vector(self.x / other.x, self.y / other.y, self.z / other.z)
        else:
            return Vector(self.x / other  , self.y / other  , self.z / other)

    def __mod__(self, other):
        if type(other) == type(self):
            return Vector(self.x % other.x, self.y % other.y, self.z % other.z)
        else:
            return Vector(self.x % other  , self.y % other  , self.z % other)

    def __pow__(self, other):
        if type(other) == type(self):
            return Vector(self.x ** other.x, self.y ** other.y, self.z ** other.z)
        else:
            return Vector(self.x ** other  , self.y ** other  , self.z ** other)

    def __lshift__(self, other):
        if type(other) == type(self):
            return Vector(self.x << other.x, self.y << other.y, self.z << other.z)
        else:
            return Vector(self.x << other  , self.y << other,   self.z << other)

    def __rshift__(self, other):
        if type(other) == type(self):
            return Vector(self.x >> other.x, self.y >> other.y, self.z >> other.z)
        else:
            return Vector(self.x >> other  , self.y >> other  , self.z >> other)

    def __and__(self, other):
        if type(other) == type(self):
            return Vector(self.x & other.x, self.y & other.y, self.z & other.z)
        else:
            return Vector(self.x & other  , self.y & other  , self.z & other)

    def __or__(self, other):
        if type(other) == type(self):
            return Vector(self.x | other.x, self.y | other.y, self.z | other.z)
        else:
            return Vector(self.x | other  , self.y | other  , self.z | other)

    def __xor__(self, other):
        if type(other) == type(self):
            return Vector(self.x ^ other.x, self.y ^ other.y, self.z ^ other.z)
        else:
            return Vector(self.x ^ other  , self.y ^ other  , self.z ^ other)

    def __eq__(self, other):
        if type(self) != type(other): return False
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        if type(self) != type(other): return True
        return self.x != other.x and self.y != other.y and self.z != other.z

    def __lt__(self, other):
        if type(self) != type(other): return False
        return self.x < other.x and self.y < other.y and self.z < other.z

    def __le__(self, other):
        if type(self) != type(other): return False
        return self.x <= other.x and self.y <= other.y and self.z <= other.z

    def __gt__(self, other):
        if type(self) != type(other): return False
        return self.x > other.x and self.y > other.y and self.z > other.z

    def __ge__(self, other):
        if type(self) != type(other): return False
        return self.x >= other.x and self.y >= other.y and self.z >= other.z
