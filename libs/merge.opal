
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

$cdef
$cy wraparound False
inline: new function swap(array: object, a: int, b: int) void {
    array[a], array[b] = array[b], array[a];
}

$cdef
inline: new function compare(a: object, b: object) int {
    return (a > b) - (b > a);
}

$cdef
$cy cdivision  True
$cy wraparound False
inline:
new function lrBinarySearch(array: object, value: object, a: int, b: int, left: bint) int {
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

$cdef
$cy wraparound False
inline:
new function multiSwapRight(array: object, a: int, b: int, len: int) void {
    new int i;
    for i in range(len) {
        swap(array, a + i, b + i);
    }
}

$cdef
$cy wraparound False
inline:
new function multiSwapLeft(array: object, a: int, b: int, len: int) void {
    new int i;
    for i in range(len) {
        swap(array, a + len - i - 1, b + len - i - 1);
    }
}

$cdef
$cy wraparound False
inline:
new function insertToLeft(array: object, from_: int, to: int) void {
    new dynamic tmp = array[from_];
    new int i;
    for i in range(from_ - 1, to - 1, -1) {
        array[i + 1] = array[i];
    }
    array[to] = tmp;
}

$cdef
$cy wraparound False
inline:
new function insertToRight(array: object, from_: int, to: int) void {
    new dynamic tmp = array[from_];
    new int i;
    for i in range(from_, to) {
        array[i] = array[i + 1];
    }
    array[to] = tmp;
}

$cdef
$cy wraparound False
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
$cy wraparound False
inline: new function checkBounds(array: object, a: int, m: int, b: int) bint {
    if array[m - 1] <= array[m] {
        return True;
    } elif array[a] > array[b - 1] {
        rotate(array, a, m, b);
        return True;
    }
    return False;
}

$cdef
$cy wraparound False
new function mergeUp(array: object, a: int, m: int, b: int, aux: list) void {
    new int i;
    for i in range(m - a) {
        aux[i] = array[i + a];
    }

    new int buf = 0,
            l   = a,
            r   = m;

    for ; l < r && r < b; l++ {
        if aux[buf] <= array[r] {
            array[l] = aux[buf];
            buf++;
        } else {
            array[l] = array[r];
            r++;
        }
    }

    for ; l < r; l++, buf++ {
        array[l] = aux[buf];
    }
}

$cdef
$cy wraparound False
new function mergeDown(array: object, a: int, m: int, b: int, aux: list) void {
    new int i;
    for i in range(b - m) {
        aux[i] = array[i + m];
    }

    new int buf = b - m - 1,
            l   = m - 1,
            r   = b - 1;

    for ; r > l && l >= a; r-- {
        if aux[buf] >= array[l] {
            array[r] = aux[buf];
            buf--;
        } else {
            array[r] = array[l];
            l--;
        }
    }

    for ; r > l; r--, buf-- {
        array[r] = aux[buf];
    }
}

$cy wraparound False
new function mergeInPlace(array: object, a: int, m: int, b: int, check: bint = True) void {
    if checkBounds(array, a, m, b) {
        return;
    }

    if check {
        b = lrBinarySearch(array, array[m - 1], m,     b, True);
        a = lrBinarySearch(array, array[m]    , a, m - 1, False);
    }

    new int i, j, k;

    if m - a <= b - m {
        i = a;
        j = m;
        while i < j && j < b {
            if array[i] > array[j] {
                k = lrBinarySearch(array, array[i], j, b, True);
                rotate(array, i, j, k);
                i += k - j;
                j = k;
            } else {
                i++;
            }
        }
    } else {
        i = m - 1;
        j = b - 1;
        while j > i && i >= a {
            if array[i] > array[j] {
                k = lrBinarySearch(array, array[j], a, i, False);
                rotate(array, k, i + 1, j + 1);
                j -= i + 1 - k;
                i = k - 1;
            } else {
                j--;
            }
        }
    }
}

use rotateMerge;

$cy cdivision  True
$cy wraparound False
inline:
new function _merge(array: object, a: int, m: int, b: int, check: bint, auxSize: int, aux: list) void {
    if checkBounds(array, a, m, b) {
        return;
    }

    if check {
        b = lrBinarySearch(array, array[m - 1], m, b, True);
        a = lrBinarySearch(array, array[m], a, m - 1, False);
    }

    new int size, m1, m2, m3;

    if b - m < m - a {
        size = b - m;

        if size <= 8 {
            mergeInPlace(array, a, m, b, False);
        } elif size <= auxSize {
            mergeDown(array, a, m, b, aux);
        } else {
            m2 = m + size / 2;
            m1 = lrBinarySearch(array, array[m2], a, m, False);
            m3 = m2 - (m - m1);
            m2++;

            rotateMerge(array, a, m, m1, m2, m3, b, auxSize, aux);
        }
    } else {
        size = m - a;
        if size <= 8 {
            mergeInPlace(array, a, m, b, False);
        } elif size <= auxSize {
            mergeUp(array, a, m, b, aux);
        } else {
            m1 = a + size / 2;
            m2 = lrBinarySearch(array, array[m1], m, b, True);
            m3 = m1 + (m2 - m);

            rotateMerge(array, a, m, m1, m2, m3, b, auxSize, aux);
        }
    }
}

$cdef
$cy wraparound False
new function rotateMerge(array: object, a: int, m: int, m1: int, m2: int, m3: int, b: int, auxSize: int, aux: list) void {
    rotate(array, m1, m, m2);

    if m1 - a > 0 && m3 - m1 > 0 {
        _merge(array, a, m1, m3, False, auxSize, aux);
    }
    m3++;
    if m2 - m3 > 0 && b - m2 > 0 {
        _merge(array, m3, m2, b, False, auxSize, aux);
    }
}

$cy wraparound False
$cy cdivision  True
new function merge(array: object, a: int, m: int, b: int, auxSize: object = None, aux: object = None, check: bint = True) void {
    if aux is None {
        auxSize = max(m - a, b - m) if auxSize is None else auxSize;
        aux = [None for _ in range(auxSize)];
    } elif auxSize is None {
        auxSize = len(aux);
    }

    _merge(array, a, m, b, check, auxSize, aux);
}

$cy wraparound False
new function mergeTwo(array1: object, array2: object) list {
    new int size = len(array1) + len(array2);
    new list aux = [None for _ in range(size)];

    new int buf = 0,
            l   = 0,
            r   = 0;

    for ; l < len(array1) and r < len(array2); buf++ {
        if array1[l] <= array2[r] {
            aux[buf] = array1[l];
            l++;
        } else {
            aux[buf] = array2[r];
            r++;
        }
    }

    for ; l < len(array1); l++, buf++ {
        aux[buf] = array1[l];
    }

    for ; r < len(array2); r++, buf++ {
        aux[buf] = array2[r];
    }

    return aux;
}