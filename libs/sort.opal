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

$args ["--compile-only", "--static"]

package math: import log2;
package libs.std: import _reverse as reverse, arraySwap as swap;

$include os.path.join(HOME_DIR, "helpers.opal")

$nocompile
cdef short swapsLen = 120

cdef short[5] incs = [48, 21, 7, 3, 1]
cdef short[120] swaps = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
    1, 3, 5, 7, 9, 11, 13, 15, 2, 4, 6, 8, 10, 12, 14, 16,
    1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15, 4, 8, 12, 16,
    1, 9, 2, 10, 3, 11, 4, 12, 5, 13, 6, 14, 7, 15, 8, 16,
    6, 11, 7, 10, 4, 13, 14, 15, 8, 12, 2, 3, 5, 9,
    2, 5, 8, 14, 3, 9, 12, 15, 6, 7, 10, 11,
    3, 5, 12, 14, 4, 9, 8, 13,
    7, 9, 11, 13, 4, 6, 8, 10, 
    4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
    7, 8, 9, 10
]
$restore

$cdef
$cy wraparound False
new function shellSort(array: object, a: int, b: int) void {
    new short k;
    new int i, j;

    for k in incs {
        for i in range(k + a, b) {
            new dynamic v = array[i];
            
            for j = i; j >= k + a && array[j - k] > v; j -= k {
                array[j] = array[j - k];
            }
            array[j] = v;
        }
    }
}

$cdef
$cy cdivision  True
$cy wraparound False
new function medianOfThree(array: object, a: int, b: int) void {
    new int m = a + (b - 1 - a) / 2;

    if array[a] > array[m] {
        swap(array, a, m);
    }

    if array[m] > array[b - 1] {
        swap(array, m, b - 1);

        if array[a] > array[m] {
            return;
        }
    }

    swap(array, a, m);
}

$cdef
$cy wraparound False
inline: new function compSwap(array: object, a: int, b: int, g: int, s: int) void {
    new int x = s + (a * g),
            y = s + (b * g);

    if array[x] > array[y] {
        swap(array, x, y);
    }
}

$cdef
$cy cdivision  True
$cy wraparound False
inline: new function medianOfSixteen(array: object, a: int, b: int) void {
    new int g = (b - 1 - a) / 16, i;

    for i in range(0, swapsLen, 2) {
        compSwap(array, swaps[i], swaps[i + 1], g, a);
    }

    swap(array, a, a + (8 * g));
}

$cdef
$cy wraparound False
new function getSortedRuns(array: object, a: int, b: int) bint {
    new bint rs = True,
             s  = True;

    new int i;

    for i in range(a, b - 1) {
        if array[i] > array[i + 1] {
            s = False;
        } else {
            rs = False;
        }

        if (!s) && (!rs) {
            return False;
        }
    }

    if rs && !s {
        reverse(array, a, b);
        return True;
    }

    return s;
}

$cdef
$cy wraparound False
new function partition(array: object, a: int, b: int, p: int) int {
    new int i = a - 1, 
            j = b;

    while True {
        for i++; i <  b && array[i] < array[p]; i++ {}
        for j--; j >= a && array[j] > array[p]; j-- {}

        if i < j {
            swap(array, i, j);
        } else {
            return j;
        }
    }
}

$cy wraparound False
$cy cdivision  True
new function __sort(array: object, a: int, b: int, d: int, unbalanced: bint) void {
    new int p, l, r;

    while b - a > 32 {
        if getSortedRuns(array, a, b) {
            return;
        }

        if d == 0 {
            heapSort(array, a, b);
            return;
        }

        if unbalanced {
            p = a;
        } else {
            medianOfThree(array, a, b);
            p = partition(array, a, b, a);
        }

        l = p - a;
        r = b - p - 1;
        if unbalanced || (l == 0 || r == 0) || (l / r >= 16 || r / l >= 16) {
            if b - a > 80 {
                swap(array, a, p);
                if l < r {
                    __sort(array, a, p, d - 1, True);
                    a = p;
                } else {
                    __sort(array, p + 1, b, d - 1, True);
                    b = p;
                }

                medianOfSixteen(array, a, b);
                p = partition(array, a + 1, b, a);
            } else {
                shellSort(array, a, b);
                return;
            }
        }

        swap(array, a, p);

        d--;
        __sort(array, p + 1, b, d, False);
        b = p;
    }

    uncheckedInsertionSort(array, a, b);
}

new function sort(array, a = 0, b = None) {
    if b is None {
        b = len(array);
    } elif b < 0 {
        b += len(array);
    }

    __sort(array, a, b, int(2 * log2(b - a)), False);
}