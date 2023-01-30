"""
MIT License

Copyright (c) 2020-2023 thatsOven

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

from libs.std      import dynamic
from libs.sort     import sort
from libs.fastSort import fastSort

class Array:
    def __init__(self, capacity, arrayType = dynamic, contents = None):
        self._capacity = capacity
        self._arrayType = arrayType
        if contents is None:
            self._array = [0 for _ in range(capacity)]
        else:
            if self._arrayType != dynamic:
                contents = self.__assertType(contents)
            self._array = contents + [0 for _ in range(capacity - len(contents))]

    def __assertType(self, contents):
        if self._arrayType == dynamic: return contents

        for i in range(len(contents)):
            if type(contents[i]) != self._arrayType:
                raise TypeError("Input value at index " + str(i) + " (" + str(contents[i]) + ") does not match array type " + str(self._arrayType))
        return contents

    def toList(self):
        return self._array.copy()

    def sort(self, start = 0, end = None):
        if self._arrayType in (int, float):
            fastSort(self._array, start, end)
        else:
            sort(self._array, start, end)

    def __repr__(self):
        return str(self._array)

    def __len__(self):
        return self._capacity

    def __getitem__(self, idx):
        if 0 <= idx < self._capacity:
            return self._array[idx]
        else:
            raise IndexError("Index " + str(idx) + " out of range for length " + str(self._capacity))

    def __setitem__(self, idx, equals):
        if self._arrayType != dynamic:
            if type(equals) != self._arrayType:
                raise TypeError("Cannot assign value of type " + str(type(equals)) + " to array of type " + str(self._arrayType))
        if 0 <= idx < self._capacity:
            self._array[idx] = equals
        else:
            raise IndexError("Index " + str(idx) + " out of range for length " + str(self._capacity))

    def __iter__(self):
        return iter(self._array)

    def __str__(self):
        return str(self._array)

    def __neg__(self):
        for i in range(self._capacity):
            self._array[i] = -self._array[i]

    def __abs__(self):
        for i in range(self._capacity):
            self._array[i] = abs(self._array[i])

    def __round__(self, n=0):
        for i in range(self._capacity):
            self._array[i] = round(self._array[i], n)

    def __add__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] += other
            return self
        elif type(other) == type(self):
            if self._arrayType == other._arrayType or self._arrayType == dynamic:
                return Array(self._capacity + other._capacity, self._arrayType, self._array.copy() + other._array.copy())
            else:
                raise TypeError("Cannot concatenate two arrays of types " + str(type(self)) + " and " + str(type(other)))
        else:
            raise TypeError("Invalid operator '+' for types " + str(type(self)) + " and " + str(type(other)))

    def __sub__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] -= other
            return self
        else:
            raise TypeError("Cannot subtract members of array of type " + str(self._arrayType) + " with type " + str(type(other)))

    def __mul__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] *= other
            return self
        else:
            raise TypeError("Cannot multiply members of array of type " + str(self._arrayType) + " with type " + str(type(other)))

    def __truediv__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] /= other
            return self
        else:
            raise TypeError("Cannot divide members of array of type " + str(self._arrayType) + " with type " + str(type(other)))

    def __floordiv__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] //= other
            return self
        else:
            raise TypeError("Cannot divide members of array of type " + str(self._arrayType) + " with type " + str(type(other)))

    def __mod__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] %= other
            return self
        else:
            raise TypeError("Cannot use the '%' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __pow__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] **= other
            return self
        else:
            raise TypeError("Cannot use the '**' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __lshift__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] <<= other
            return self
        else:
            raise TypeError("Cannot use the '<<' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __rshift__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] >>= other
            return self
        else:
            raise TypeError("Cannot use the '>>' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __and__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] &= other
            return self
        else:
            raise TypeError("Cannot use the '&' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __or__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] |= other
            return self
        else:
            raise TypeError("Cannot use the '|' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __xor__(self, other):
        if type(other) == self._arrayType or self._arrayType == dynamic:
            for i in range(self._capacity):
                self._array[i] ^= other
            return self
        else:
            raise TypeError("Cannot use the '^' operator with members of array of type " + str(self._arrayType) + " and type " + str(type(other)))

    def __eq__(self, other):
        if type(self) != type(other): return False
        return self._array == other._array and self._arrayType == other._arrayType

    def __ne__(self, other):
        if type(self) != type(other): return False
        return self._array != other._array and self._arrayType != other._arrayType
