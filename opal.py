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

class IO:
    from libs.std import endl, out, read

class Utils:
    from libs.std import (
                            swap,
                            tolerance,
                            limitToRange,
                            translate
                         )

    class Iterables:
        from libs.std import (
                              multiSwapLeft,
                              multiSwapRight,
                              insertToLeft,
                              insertToRight,
                              rotate,
                              rotateOOP,
                              binarySearch,
                              linearSearch,
                              reverse
                              )

        from libs.std import arraySwap as swap

        from libs.sort       import sort
        from libs.merge      import Merge, merge, mergeTwo
        from libs.stableSort import stableSort
        from libs.fastSort   import fastSort

    class Strings:
        from libs.std import justifyString as justify

    class Integers:
        from libs.std import getNearestPowerOfTwo

class Typing:
    from libs.std import (
        mode, hybrid, check,
        force, none
    )

from libs.std      import dynamic
from libs.Array    import Array
from libs.Stack    import Stack
from libs.Vector   import Vector
from libs.char     import char
from libs.Queue    import Queue

from libs.graphics.Graphics import Graphics

from pygame.locals import *
