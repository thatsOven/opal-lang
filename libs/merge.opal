
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

package libs.std: import *;

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
        b = _lrBinarySearch(array, array[m - 1], m,     b, True);
        a = _lrBinarySearch(array, array[m]    , a, m - 1, False);
    }

    new int i, j, k;

    if m - a <= b - m {
        i = a;
        j = m;
        while i < j && j < b {
            if array[i] > array[j] {
                k = _lrBinarySearch(array, array[i], j, b, True);
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
                k = _lrBinarySearch(array, array[j], a, i, False);
                rotate(array, k, i + 1, j + 1);
                j -= i + 1 - k;
                i = k - 1;
            } else {
                j--;
            }
        }
    }
}

new dynamic rotateMerge;

$cy cdivision  True
$cy wraparound False
inline:
new function _merge(array: object, a: int, m: int, b: int, check: bint, auxSize: int, aux: list) void {
    if checkBounds(array, a, m, b) {
        return;
    }

    if check {
        b = _lrBinarySearch(array, array[m - 1], m, b, True);
        a = _lrBinarySearch(array, array[m], a, m - 1, False);
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
            m1 = _lrBinarySearch(array, array[m2], a, m, False);
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
            m2 = _lrBinarySearch(array, array[m1], m, b, True);
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