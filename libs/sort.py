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
from libs.std import *
from libs._helpers import heapSort, uncheckedInsertionSort

incs = (48, 21, 7, 3, 1)
medianOfSixteenSwaps = (
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
)

def shellSort(array, lo, hi):
    for k in incs:
        for i in range(k + lo, hi):
            v = array[i]
            j = i
            
            while j >= k + lo and array[j - k] > v:
                array[j] = array[j - k]
                j -= k
            array[j] = v

def partition(array, a, b, p):
    i = a - 1
    j = b

    while True:
        i += 1
        while i < b  and array[i] < array[p]: i += 1

        j -= 1
        while j >= a and array[j] > array[p]: j -= 1

        if i < j: arraySwap(array, i, j)
        else:     return j

def medianOfThree(array, a, b):
    m = a + (b - 1 - a) // 2

    if array[a] > array[m]: arraySwap(array, a, m)
    if array[m] > array[b - 1]: 
        arraySwap(array, m, b - 1)
        
        if array[a] > array[m]: return

    arraySwap(array, a, m)

def compSwap(array, a, b, g, s):
    if array[s + (a * g)] > array[s + (b * g)]:
        arraySwap(array, s + (a * g), s + (b * g))

def medianOfSixteen(array, a, b):
    gap = (b - 1 - a) // 16

    for i in range(0, len(medianOfSixteenSwaps), 2): 
        compSwap(array, medianOfSixteenSwaps[i], 
                        medianOfSixteenSwaps[i+1], gap, a)

    arraySwap(array, a, a + (8 * gap))

def getSortedRuns(array, a, b):
    rs = True
    s  = True

    for i in range(a, b - 1):
        if array[i] > array[i + 1]: 
            s    = False
        else: rs = False

        if (not s) and (not rs): return False
    
    if rs and not s:
        reverse(array, a, b)
        return True
        
    return s

def medianOfSixteenQuickSort(array, a, b, d, unbalanced):
    while b - a > 32:
        if getSortedRuns(array, a, b): return
        if d == 0:
            heapSort(array, a, b)
            return

        if unbalanced: p = a
        else:
            medianOfThree(array, a, b)
            p = partition(array, a, b, a)
        
        l = p - a
        r = b - p - 1
        if unbalanced or (l == 0 or r == 0) or (l / r >= 16 or r / l >= 16):
            if b - a > 80:
                arraySwap(array, a, p)
                if l < r:
                    medianOfSixteenQuickSort(array, a, p, d - 1, True)
                    a = p
                else:
                    medianOfSixteenQuickSort(array, p + 1, b, d - 1, True)
                    b = p
                medianOfSixteen(array, a, b)
                p = partition(array, a + 1, b, a)
            else:
                shellSort(array, a, b)
                return
        
        arraySwap(array, a, p)

        d -= 1
        medianOfSixteenQuickSort(array, p + 1, b, d, False)
        b = p
    uncheckedInsertionSort(array, a, b)

def sort(array, a = 0, b = None):
    if b is None: b = len(array)
    medianOfSixteenQuickSort(array, a, b, int(2 * math.log2(b - a)), False)
