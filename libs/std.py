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

endl = "\n"

def out(*messages):
    for message in messages:
        print(message, end = "", flush = True)

def read(message = ""):
    return input(message)

def justifyString(message, length, left = True, fill = " "):
    if len(message) > length:
        raise Exception("Length of string is greater than defined length")

    if left:
        return fill * (length - len(message)) + message
    else:
        return message + fill * (length - len(message))

def tolerance(value, tol):
    return range(round(value - tol), round(value + tol))

def limitToRange(variable, min_, max_, pacman = False, returnChanged = False):
    if variable < min_:
        if returnChanged:
            return (max_ if pacman else min_), True
        else:
            return (max_ if pacman else min_)
    if variable > max_:
        if returnChanged:
            return (min_ if pacman else max_), True
        else:
            return (min_ if pacman else max_)
    if returnChanged:
        return variable, False
    else:
        return variable

def swap(a, b):
    return b, a

def compare(a, b):
    return (a > b) - (b > a)

def arraySwap(array, a, b):
    array[a], array[b] = array[b], array[a]

def multiSwapRight(array, a, b, len):
    for i in range(0, len):
        arraySwap(array, a + i, b + i)

def multiSwapLeft(array, a, b, len):
    for i in range(0, len):
        arraySwap(array, a + len - i - 1, b + len - i - 1)

def insertToLeft(array, _from, to):
    temp = array[_from]
    for i in range(_from - 1, to - 1, -1):
        array[i + 1] = array[i]
    array[to] = temp

def insertToRight(array, _from, to):
    temp = array[_from]
    for i in range(_from, to):
        array[i] = array[i + 1]
    array[to] = temp

def rotate(array, start, split, end):
    while end - split > 1 and split - start > 1:
        if end - split < split - start:
            multiSwapRight(array, start, split, end - split)
            start += end - split
        else:
            multiSwapLeft(array, start, end - (split - start), split - start)
            end   -= split - start

    if     end - split == 1: insertToLeft(array, split, start)
    elif split - start == 1: insertToRight(array, start, end - 1)

def rotateOOP(array, a, m, b):
    if b - m == m - a:
        multiSwapLeft(array, a, m, m - a)
        return
    aux = []
    for i in range(m, b):
        aux.append(array[i])
    for i in range(a, m):
        aux.append(array[i])
    for i in range(a, b):
        array[i] = aux[i - a]

def lrBinarySearch(array, value, start = 0, end = None, left = True, comparefn = compare):
    if end is None: end = len(array)

    a = start
    b = end
    while a < b:
        m = a + ((b - a) // 2)

        cmp = comparefn(value, array[m])
        if cmp <= 0 if left else cmp < 0:
            b = m
        else: a = m+1

    return a

def binarySearch(array, value, start = 0, end = None, comparefn = compare):
    if end is None: end = len(array)

    a = start
    b = end
    while a < b:
        m = a + ((b - a) // 2)

        cmp = comparefn(value, array[m])
        if cmp == 0: return m

        if cmp < 0: b = m
        else:       a = m + 1

    return -1

def linearSearch(array, value, start = 0, end = None, getVal = lambda x : x):
    if end is None: end = len(array)

    for i in range(start, end):
        if getVal(array[i]) == value:
            return i

    return -1

def reverse(array, start, end):
    end -= 1
    while start < end:
        arraySwap(array, start, end)
        start += 1
        end -= 1

def getNearestPowerOfTwo(n, floor):
    v = n
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    v += 1
    x = v >> 1
    if floor: return x
    else:     return v

def translate(value, min_, max_, minResult, maxResult):
    deltaOrig = max_      - min_
    deltaOut  = maxResult - minResult

    scaled = float(value - min_) / float(deltaOrig)

    return minResult + (scaled * deltaOut)

def _OPAL_ASSERT_CLASSVAR_TYPE_(className, inputVal):
    if type(inputVal) is className: return inputVal
    else:                           raise  TypeError("Invalid type " + str(type(inputVal)) + " for variable of type " + str(className))

class dynamic: pass
