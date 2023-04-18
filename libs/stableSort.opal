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
package libs.merge: import _merge;

$cdef
$cy wraparound False
new function getReversedRuns(array: object, a: int, b: int) bint {
    new int i;
    for i = a; i < b - 1; i++ {
        if array[i] <= array[i + 1] {
            break;
        }
    }

    if i - a > 8 {
        reverse(array, a, i + 1);
    }

    return i == b;
}

$cdef
$cy wraparound False
new function insertSort(array: object, a: int, b: int) void {
    for i in range(a + 1, b) {
        if array[i] < array[i - 1] {
            insertToLeft(array, i, lrBinarySearch(array, array[i], a, i - 1, False));
        }
    }
}

$cdef
$cy cdivision  True
$cy wraparound False
new function sort(array: object, a: int, b: int, auxSize: int, aux: list) void {
    if getReversedRuns(array, a, b) {
        return;
    }

    new int m;
    if b - a > 32 {
        m = a + (b - a) / 2;
        sort(array, a, m, auxSize, aux);
        sort(array, m, b, auxSize, aux);
        _merge(array, a, m, b, True, auxSize, aux);
    } else {
        insertSort(array, a, b);
    }
}

new function stableSort(array, a = 0, b = None, aux = None, auxSize = None) {
    if b is None {
        b = len(array);
    }
    
    if aux is None {
        auxSize = (b - a) // 2 if auxSize is None else auxSize;
        aux = [None for _ in range(auxSize)];
    } elif auxSize is None {
        auxSize = len(aux);
    }

    sort(array, a, b, auxSize, aux);
}