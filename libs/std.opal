
# MIT License
# 
# Copyright (c) 2020 thatsOven
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

$args ["--static"]

new dynamic endl = "\n";

new function out(*messages) {
    for message in messages {
        $embed print(message, end = "", flush = True)
    }
}

new function read(message = "") {
    $embed return input(message)
}

new function justifyString(message: str, length: int, left: bint = True, fill: str = " ") str {
    if len(message) > length {
        throw Exception("Length of string is greater than defined length");
    }

    if left {
        return fill * (length - len(message)) + message;
    } else {
        return message + fill * (length - len(message));
    }
}

new function tolerance(value: object, tol: object) object {
    return range(round(value - tol), round(value + tol));
}

new function limitToRange(value, min_, max_, pacman = False, returnChanged = False) {
    if value < min_ {
        if returnChanged {
            return (max_ if pacman else min_), True;
        } else {
            return max_ if pacman else min_;
        }
    }

    if value > max_ {
        if returnChanged {
            return (min_ if pacman else max_), True;
        } else {
            return max_ if pacman else min_;
        }
    }

    if returnChanged {
        return value, False;
    } else {
        return value;
    }
}

inline:
new function swap(a: object, b: object) tuple {
    return b, a;
}

inline:
new function compare(a: object, b: object) int {
    return (a > b) - (b > a);
}

inline:
new function arraySwap(array: object, a: int, b: int) void {
    array[a], array[b] = array[b], array[a];
}

inline:
new function multiSwapRight(array: object, a: int, b: int, len: int) void {
    for i in range(len) {
        arraySwap(array, a + i, b + i);
    }
}

inline:
new function multiSwapLeft(array: object, a: int, b: int, len: int) void {
    for i in range(len) {
        arraySwap(array, a + len - i - 1, b + len - i - 1);
    }
}

inline:
new function insertToLeft(array: object, from_: int, to: int) void {
    new dynamic tmp = array[from_];
    for i in range(from_ - 1, to - 1, -1) {
        array[i + 1] = array[i];
    }
    array[to] = tmp;
}

inline:
new function insertToRight(array: object, from_: int, to: int) void {
    new dynamic tmp = array[from_];
    for i in range(from_, to) {
        array[i] = array[i + 1];
    }
    array[to] = tmp;
}

inline:
new function rotate(array: object, a: int, m: int, b: int) void {
    while b - m > 1 && m - a > 1 {
        if b - m < m - a {
            multiSwapRight(array, a, m, b - m);
            a += b - m;
        } else {
            multiSwapLeft(array, a, b - (m - a), m - a);
            b -= m - a;
        }
    }

    if b - m == 1 {
        insertToLeft(array, m, a);
    } elif m - a == 1 {
        insertToRight(array, a, b - 1);
    }
}

$cdef
$cy cdivision  True
$cy wraparound False
inline:
new function _lrBinarySearch(array: object, value: object, a: int, b: int, left: bint) int {
    new int m, cmp;
    
    while a < b {
        m = a + (b - a) / 2;
        
        cmp = compare(value, array[m]);

        if cmp <= 0 if left else cmp < 0 {
            b = m;
        } else {
            a = m + 1;
        }
    }

    return a;
}

new function lrBinarySearch(array, value, a = 0, b = None, left = True) {
    if b is None {
        b = len(array);
    } elif b < 0 {
        b += len(array);
    }

    return _lrBinarySearch(array, value, a, b, left);
}

$cdef
$cy cdivision  True
$cy wraparound False
inline:
new function _binarySearch(array: object, value: object, a: int, b: int) int {
    new int m, cmp;
    
    while a < b {
        m = a + (b - a) / 2;

        cmp = compare(value, array[m]);
        if cmp == 0 {
            return m;
        }

        if cmp < 0 {
            b = m;
        } else {
            a = m + 1;
        }
    }

    return -1;
}

new function binarySearch(array, value, a = 0, b = None) {
    if b is None {
        b = len(array);
    } elif b < 0 {
        b += len(array);
    }

    return _binarySearch(array, value, a, b);
}

$cdef
$cy wraparound False
inline:
new function _linearSearchWithKey(array: object, value: object, a: int, b: int, get: object) int {
    for i in range(a, b) {
        if get(array[i]) == value {
            return i;
        }
    }

    return -1;
}

$cdef
$cy wraparound False
inline:
new function _linearSearch(array: object, value: object, a: int, b: int) int {
    for i in range(a, b) {
        if array[i] == value {
            return i;
        }
    }

    return -1;
}

new function linearSearch(array, value, a = 0, b = None, get = None) {
    if b is None {
        b = len(array);
    } elif b < 0 {
        b += len(array);
    }

    if get is None {
        return _linearSearch(array, value, a, b);
    } else {
        return _linearSearchWithKey(array, value, a, b, get);
    }
}

$cy wraparound False
inline: new function _reverse(array: object, a: int, b: int) void {
    for b--; a < b; a++, b-- {
        arraySwap(array, a, b);
    }
}

new function reverse(array, a = 0, b = None) {
    if b is None {
        b = len(array);
    } elif b < 0 {
        b += len(array);
    }

    _reverse(array, a, b);
}

new function getNearestPowerOfTwo(n: int, floor: bint) int {
    new int v = n - 1;
    v |= v >> 1;
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;
    v++;

    if floor {
        return v >> 1;
    } else {
        return v;
    }
}

new function translate(value, min_, max_, minResult, maxResult) {
    new dynamic deltaOrig = max_      - min_,
                deltaOut  = maxResult - minResult,
                scaled    = float(value - min_) / float(deltaOrig);

    return minResult + (scaled * deltaOut);
}