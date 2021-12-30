"""
MIT License

Copyright (c) 2020-2021 thatsOven

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

from libs.std   import *
from libs.merge import Merge

class __sorter:
    def __init__(self, size, aux):
        self.__merge = Merge(size, aux)
    
    @classmethod
    def __getReversedRuns(self, array, a, b):
        i = a
        while i < b - 1:
            if array[i] <= array[i + 1]: break
            i += 1
        
        if i - a > 8:
            reverse(array, a, i + 1)

        return i == b

    @classmethod
    def insertSort(self, array, a, b):
        for i in range(a + 1, b):
            if array[i] < array[i - 1]:
                insertToLeft(array, i, lrBinarySearch(array, array[i], a, i - 1, False))

    def sort(self, array, a, b):
        if self.__getReversedRuns(array, a, b): return
        if b - a > 32:
            m = a + (b - a) // 2
            self.sort(array, a, m)
            self.sort(array, m, b)
            self.__merge.merge(array, a, m, b)
        else:
            self.insertSort(array, a, b)

def stableSort(array, a = 0, b = None, aux = None, auxSize = None):
    if b is None: b = len(array)
    if aux is None:
        aux = []
        auxSize = len(array) // 2 if auxSize is None else auxSize
    elif auxSize is None: auxSize = len(aux)

    __sorter(auxSize, aux).sort(array, a, b)