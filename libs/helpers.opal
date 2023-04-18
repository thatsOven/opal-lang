
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

package libs.std: import arraySwap as swap;

$cdef
$cy cdivision  True
$cy wraparound False
new function siftDown(array: object, r: int, d: int, a: int) void {
    new int l;

    while r <= d / 2 {
        l = 2 * r;

        if l < d && array[a + l - 1] < array[a + l] {
            l++;
        }

        if array[a + r - 1] < array[a + l - 1] {
            swap(array, a + r - 1, a + l - 1);
            r = l;
        } else {
            break;
        }
    }
}

$cdef
$cy cdivision  True
$cy wraparound False
inline: new function heapify(array: object, a: int, b: int) void {
    new int l = b - a,
            i = l / 2;

    for ; i >= 1; i-- {
        siftDown(array, i, l, a);
    }
}

$cdef
$cy wraparound False
inline: new function heapSort(array: object, a: int, b: int) void {
    heapify(array, a, b);

    new int i;
    for i = b - a; i > 1; i-- {
        swap(array, a + i - 1);
        siftDown(array, 1, i - 1, a);
    }
}

$cdef
$cy wraparound False
new function uncheckedInsertionSort(array: object, a: int, b: int) void {
    new int i, j;

    for i in range(a + 1, b) {
        if array[i] < array[a] {
            swap(array, i, a);
        }

        new dynamic key = array[i];
        
        for j = i - 1; key < array[j]; j-- {
            array[j + 1] = array[j];
        }
        array[j + 1] = key;    
    }   
} 