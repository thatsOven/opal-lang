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

from libs._helpers import heapSort, uncheckedInsertionSort

def findMinMax(array, a, b):
    currMin = array[a]
    currMax = array[a]
    for i in range(a + 1, b):
        if   array[i] < currMin:
            currMin = array[i]
        elif array[i] > currMax:
            currMax = array[i]
    return currMin, currMax

def fastSort(array, a = 0, b = None):
    if b is None: b = len(array)
    
    min_, max_ = findMinMax(array, a, b)

    auxLen = b - a

    count  = [0 for _ in range(auxLen + 1)]
    offset = [0 for _ in range(auxLen + 1)]

    CONST = auxLen / (max_ - min_ + 1)

    for i in range(a, b):
        count[int((array[i] - min_) * CONST)] += 1

    offset[0] = a

    for i in range(1, auxLen):
        offset[i] = count[i - 1] + offset[i - 1]

    for v in range(auxLen):
        while count[v] > 0:
            orig  = offset[v]
            from_ = orig
            num   = array[from_]

            array[from_] = -1

            while True:
                dig = int((num - min_) * CONST)
                to  = offset[dig]

                offset[dig] += 1
                count[dig]  -= 1

                tmp       = array[to]
                array[to] = num
                num       = tmp
                from_     = to

                if from_ == orig: break

    for i in range(auxLen):
        s = offset[i - 1] if i > 0 else a
        e = offset[i]

        if e - s <= 1:
            continue

        if e - s > 16:
            heapSort(array, s, e)
        else:
            uncheckedInsertionSort(array, s, e)
