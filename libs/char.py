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

class char:
    def __init__(self, value):
        if not type(value) in (str, int):
            raise TypeError("char class requires a str or an int object to initialize (got " + str(type(value)) + ")")
        else:
            if type(value) is str:
                if len(value) == 1:
                    self._value = value
                else:
                    raise ValueError("char class requires a one character str or an int to initialize (got str of length " + str(len(value)) + ")")
            else:
                try:
                    self._value = chr(value)
                except:
                    raise ValueError("int value gave to char class initializer is not valid")
                else:
                    self._value = chr(value)

    def toInt(self):
        return ord(self._value)

    def __str__(self):
        return self._value

    def __repr__(self):
        return self._value

    def __del__(self):
        del self._value

    def __add__(self, other):
        if type(other) == int:
            return char(self.toInt() + other)
        elif type(self) == type(other):
            return char(self.toInt() + other.toInt())
        elif type(other) == str:
            return char(self.toInt() + char(other).toInt())
        else:
            raise TypeError("Invalid operator '+' for types " + str(type(self)) + " and " + str(type(other)))

    def __sub__(self, other):
        if type(other) == int:
            return char(self.toInt() - other)
        elif type(self) == type(other):
            return char(self.toInt() - other.toInt())
        elif type(other) == str:
            return char(self.toInt() - char(other).toInt())
        else:
            raise TypeError("Invalid operator '-' for types " + str(type(self)) + " and " + str(type(other)))

    def __mul__(self, other):
        if type(other) == int:
            return char(self.toInt() * other)
        elif type(self) == type(other):
            return char(self.toInt() * other.toInt())
        elif type(other) == str:
            return char(self.toInt() * char(other).toInt())
        else:
            raise TypeError("Invalid operator '*' for types " + str(type(self)) + " and " + str(type(other)))

    def __floordiv__(self, other):
        if type(other) == int:
            return char(self.toInt() // other)
        elif type(self) == type(other):
            return char(self.toInt() // other.toInt())
        elif type(other) == str:
            return char(self.toInt() // char(other).toInt())
        else:
            raise TypeError("Invalid operator '//' for types " + str(type(self)) + " and " + str(type(other)))

    def __mod__(self, other):
        if type(other) == int:
            return char(self.toInt() % other)
        elif type(self) == type(other):
            return char(self.toInt() % other.toInt())
        elif type(other) == str:
            return char(self.toInt() % char(other).toInt())
        else:
            raise TypeError("Invalid operator '%' for types " + str(type(self)) + " and " + str(type(other)))

    def __pow__(self, other):
        if type(other) == int:
            return char(self.toInt() ** other)
        elif type(self) == type(other):
            return char(self.toInt() ** other.toInt())
        elif type(other) == str:
            return char(self.toInt() ** char(other).toInt())
        else:
            raise TypeError("Invalid operator '**' for types " + str(type(self)) + " and " + str(type(other)))

    def __lshift__(self, other):
        if type(other) == int:
            return char(self.toInt() << other)
        elif type(self) == type(other):
            return char(self.toInt() << other.toInt())
        elif type(other) == str:
            return char(self.toInt() << char(other).toInt())
        else:
            raise TypeError("Invalid operator '<<' for types " + str(type(self)) + " and " + str(type(other)))

    def __rshift__(self, other):
        if type(other) == int:
            return char(self.toInt() >> other)
        elif type(self) == type(other):
            return char(self.toInt() >> other.toInt())
        elif type(other) == str:
            return char(self.toInt() >> char(other).toInt())
        else:
            raise TypeError("Invalid operator '>>' for types " + str(type(self)) + " and " + str(type(other)))

    def __and__(self, other):
        if type(other) == int:
            return char(self.toInt() & other)
        elif type(self) == type(other):
            return char(self.toInt() & other.toInt())
        elif type(other) == str:
            return char(self.toInt() & char(other).toInt())
        else:
            raise TypeError("Invalid operator '&' for types " + str(type(self)) + " and " + str(type(other)))

    def __or__(self, other):
        if type(other) == int:
            return char(self.toInt() | other)
        elif type(self) == type(other):
            return char(self.toInt() | other.toInt())
        elif type(other) == str:
            return char(self.toInt() | char(other).toInt())
        else:
            raise TypeError("Invalid operator '|' for types " + str(type(self)) + " and " + str(type(other)))

    def __xor__(self, other):
        if type(other) == int:
            return char(self.toInt() ^ other)
        elif type(self) == type(other):
            return char(self.toInt() ^ other.toInt())
        elif type(other) == str:
            return char(self.toInt() ^ char(other).toInt())
        else:
            raise TypeError("Invalid operator '^' for types " + str(type(self)) + " and " + str(type(other)))

    def __eq__(self, other):
        return self.toInt() == other.toInt()

    def __ne__(self, other):
        return self.toInt() != other.toInt()
