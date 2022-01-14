"""
MIT License

Copyright (c) 2020-2022 thatsOven

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

from libs.std  import *

def _checkBounds(array, a, m, b):
    if   array[m - 1] <= array[m]: return True
    elif array[a] > array[b - 1]:
        rotate(array, a, m, b)
        return True
    return False

class Merge:
    def __init__(self, size = None, aux = None):
        if aux is None:
            aux = []

        self.aux = aux

        self.__capacity = size
            
        if size is not None and size > len(self.aux):
            for _ in range(len(self.aux) - size):
                self.aux.append(0)

    def __mergeUp(self, array, start, mid, end):
        for i in range(mid - start):
            self.aux[i] = array[i + start]

        bufferPointer = 0
        left = start
        right = mid

        while left < right and right < end:
            if self.aux[bufferPointer] <= array[right]:
                array[left] = self.aux[bufferPointer]
                left += 1
                bufferPointer += 1
            else:
                array[left] = array[right]
                left += 1
                right += 1
        
        while left < right:
            array[left] = self.aux[bufferPointer]
            left += 1
            bufferPointer += 1

    def __mergeDown(self, array, start, mid, end):
        for i in range(end - mid):
            self.aux[i] = array[i + mid]

        bufferPointer = end - mid - 1
        left = mid - 1
        right = end - 1

        while right > left and left >= start:
            if self.aux[bufferPointer] >= array[left]:
                array[right] = self.aux[bufferPointer]
                right -= 1
                bufferPointer -= 1
            else:
                array[right] = array[left]
                right -= 1
                left -= 1
        
        while right > left:
            array[right] = self.aux[bufferPointer]
            right -= 1
            bufferPointer -= 1

    @staticmethod
    def mergeInPlace(array, a, m, b, check=True):
        if _checkBounds(array, a, m, b): return

        if check:
            b = lrBinarySearch(array, array[m - 1], m, b)
            a = lrBinarySearch(array, array[m]    , a, m - 1, False)

        if m - a <= b - m:
            i = a
            j = m
            while i < j and j < b:
                if array[i] > array[j]:
                    k = lrBinarySearch(array, array[i], j, b, True)
                    rotate(array, i, j, k)
                    i += k - j
                    j = k
                else: i += 1
        else:
            i = m - 1
            j = b - 1
            while j > i and i >= a:
                if array[i] > array[j]:
                    k = lrBinarySearch(array, array[j], a, i, False)
                    rotate(array, k, i + 1, j + 1)
                    j -= (i + 1) - k
                    i = k - 1
                else: j -= 1

    def __rotateMerge(self, array, a, m, m1, m2, m3, b):
        rotate(array, m1, m, m2)

        if m1 - a > 0 and m3 - m1 > 0: self.merge(array,  a, m1, m3, False)
        m3 += 1
        if m2 - m3 > 0 and b - m2 > 0: self.merge(array, m3, m2,  b, False)

    def __checkCapacity(self, size):
        if len(self.aux) < size:
            for _ in range(size - len(self.aux)):
                self.aux.append(0)

    def merge(self, array, a, m, b, check=True):
        if _checkBounds(array, a, m, b): return
        
        if check:
            b = lrBinarySearch(array, array[m - 1], m, b)
            a = lrBinarySearch(array, array[m], a, m - 1, False)

        auxSize = len(array) // 2 if self.__capacity is None else self.__capacity

        self.__checkCapacity(auxSize)

        if b - m < m - a:
            size = b - m
            if   size <= 8:
                Merge.mergeInPlace(array, a, m, b, False)
            elif size <= auxSize:
                self.__mergeDown(array, a, m, b)
            else:
                m2 = m + size // 2
                m1 = lrBinarySearch(array, array[m2], a, m, False)
                m3 = m2 - (m - m1)
                m2 += 1

                self.__rotateMerge(array, a, m, m1, m2, m3, b)
        else:
            size = m - a
            if   size <= 8:
                Merge.mergeInPlace(array, a, m, b, False)
            elif size <= auxSize:
                self.__mergeUp(array, a, m, b)
            else:
                m1 = a + size // 2
                m2 = lrBinarySearch(array, array[m1], m, b)
                m3 = m1 + (m2 - m)

                self.__rotateMerge(array, a, m, m1, m2, m3, b)

def merge(array, a, m, b, auxSize = None, aux = None, check = True):
    Merge(auxSize, aux).merge(array, a, m, b, check)

def mergeTwo(array1, array2):
    output = []

    left  = 0
    right = 0
    
    while left < len(array1) and right < len(array2):
        if array1[left] <= array2[right]:
            output.append(array1[left])
            left += 1
        else:
            output.append(array2[right])
            right += 1
    
    while left < len(array1):
        output.append(array1[left])
        left += 1

    while right < len(array2):
        output.append(array2[right])
        right += 1

    return output
