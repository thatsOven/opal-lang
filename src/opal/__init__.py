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

try:
    class IO:
        from opal.libs.std import endl, out, read

    class Utils:
        from opal.libs.std import (
                                swap,
                                tolerance,
                                limitToRange,
                                translate
                            )

        class Iterables:
            from opal.libs.std import (
                                multiSwapLeft,
                                multiSwapRight,
                                insertToLeft,
                                insertToRight,
                                rotate,
                                binarySearch,
                                linearSearch,
                                reverse
                                )

            from opal.libs.std import arraySwap as swap

            from opal.libs.sort       import sort
            from opal.libs.merge      import merge, mergeTwo
            from opal.libs.stableSort import stableSort
            from opal.libs.fastSort   import fastSort

        class Strings:
            from opal.libs.std import justifyString as justify

        class Integers:
            from opal.libs.std import getNearestPowerOfTwo
except ImportError:
    print("WARNING: Part of the opal standard library was not imported due to it not being built properly")

class Typing:
    from opal.libs._internals import (
        mode, hybrid, check,
        force, none
    )

from opal.libs._internals import dynamic
from opal.libs.Array      import Array
from opal.libs.Stack      import Stack
from opal.libs.Vector     import Vector
from opal.libs.char       import char
from opal.libs.Queue      import Queue

from opal.libs.graphics.Graphics import Graphics

from pygame.locals import *
