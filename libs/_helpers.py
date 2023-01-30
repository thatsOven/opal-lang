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

from libs.std import arraySwap as swap

def siftDown(array, r, d, a):
    while r <= d // 2:
        l = 2 * r

        if l < d and array[a + l - 1] < array[a + l]:
            l += 1
            
        if array[a + r - 1] < array[a + l - 1]:
            swap(array, a + r - 1, a + l - 1)
            r = l
        else:
            break

def heapify(array, a, b):
    l = b - a
    i = l // 2
    while i >= 1:
        siftDown(array, i, l, a)
        i -= 1
    
def heapSort(array, a, b):
    heapify(array, a, b)
    i = b - a
    while i > 1:
        swap(array, a, a + i - 1)
        siftDown(array, 1, i-1, a)
        i -= 1

def uncheckedInsertionSort(array, a, b):
    for i in range(a + 1, b): 
        if array[i] < array[a]: 
            swap(array, i, a)

        key = array[i] 
        j = i-1
        
        while key < array[j]: 
            array[j+1] = array[j] 
            j -= 1
        array[j+1] = key
