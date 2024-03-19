
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

$include os.path.join(HOME_DIR, "helpers.opal")
$embed from cpython.mem cimport PyMem_Malloc, PyMem_Free
use PyMem_Free;

$cdef
$cy wraparound False
inline: new function findMinMaxWithKey(array: object, a: int, b: int, getfn: object) tuple {
    new dynamic currMin = getfn(array[a]),
                currMax = currMin;

    for i in range(a + 1, b) {
        new dynamic val = getfn(array[i]);

        if     val < currMin {
            currMin = val;
        } elif val > currMax {
            currMax = val;
        }
    }

    return currMin, currMax;
} 

$cdef
$cy wraparound False
inline: new function findMinMax(array: object, a: int, b: int) tuple {
    new dynamic currMin = array[a],
                currMax = currMin;

    for i in range(a + 1, b) {
        new dynamic val = array[i];

        if     val < currMin {
            currMin = val;
        } elif val > currMax {
            currMax = val;
        }
    }

    return currMin, currMax;
}

$macro endSection
    new int s = a, e;
    for i in range(auxLen) {
        e = offset[i];

        if e - s <= 1 {
            s = offset[i];
            continue;
        }

        if e - s > 16 {
            heapSort(array, s, e);
        } else {
            uncheckedInsertionSort(array, s, e);
        }

        s = offset[i];
    }

    PyMem_Free(count);
    PyMem_Free(offset);
$end

$cy wraparound False
$cy cdivision  True
new function __sortWithKey(array: object, a: int, b: int, getfn: object) void {
    new dynamic min_, max_;
    min_, max_ = findMinMaxWithKey(array, a, b, getfn);

    new int auxLen  = b - a;
    new float CONST = auxLen / float(max_ - min_ + 1);

    $cdef
    new (size_t*) count  = <size_t*>PyMem_Malloc((auxLen + 1) * sizeof(size_t)),
                  offset = <size_t*>PyMem_Malloc((auxLen + 1) * sizeof(size_t));
    
    new int i;
    for i in range(auxLen + 1) {
        count[i] = 0;
    }

    for i in range(a, b) {
        count[int((getfn(array[i]) - min_) * CONST)]++;
    }

    offset[0] = a;
    for i in range(1, auxLen + 1) {
        offset[i] = count[i - 1] + offset[i - 1];
    }

    new int orig, from_, dig, to;
    new dynamic num, tmp;
    for v in range(auxLen) {
        while count[v] > 0 {
            orig  = offset[v];
            from_ = orig;
            num   = array[from_];

            array[from_] = -1;

            while True {
                dig = int((getfn(num) - min_) * CONST);
                to  = offset[dig];

                offset[dig]++;
                count[dig]--;

                tmp       = array[to];
                array[to] = num;
                num       = tmp;
                from_     = to;

                if from_ == orig {
                    break;
                } 
            }
        }
    }

    $call endSection
}

$cy wraparound False
$cy cdivision  True
new function __sort(array: object, a: int, b: int) void {
    new dynamic min_, max_;
    min_, max_ = findMinMax(array, a, b);

    new int auxLen  = b - a;
    new float CONST = auxLen / float(max_ - min_ + 1);

    $cdef
    new (size_t*) count  = <size_t*>PyMem_Malloc((auxLen + 1) * sizeof(size_t)),
                  offset = <size_t*>PyMem_Malloc((auxLen + 1) * sizeof(size_t));
    
    new int i;
    for i in range(auxLen + 1) {
        count[i] = 0;
    }

    for i in range(a, b) {
        count[int((array[i] - min_) * CONST)]++;
    }

    offset[0] = a;
    for i in range(1, auxLen + 1) {
        offset[i] = count[i - 1] + offset[i - 1];
    }

    new int orig, from_, dig, to;
    new dynamic num, tmp;
    for v in range(auxLen) {
        while count[v] > 0 {
            orig  = offset[v];
            from_ = orig;
            num   = array[from_];

            array[from_] = -1;

            while True {
                dig = int((num - min_) * CONST);
                to  = offset[dig];

                offset[dig]++;
                count[dig]--;

                tmp       = array[to];
                array[to] = num;
                num       = tmp;
                from_     = to;

                if from_ == orig {
                    break;
                } 
            }
        }
    }

    $call endSection
}

new function fastSort(array, a = 0, b = None, getfn = None) {
    if b is None {
        b = len(array);
    } elif b < 0 {
        b += len(array);
    }

    if getfn is None {
        __sort(array, a, b);
    } else {
        __sortWithKey(array, a, b, getfn);
    }
}
