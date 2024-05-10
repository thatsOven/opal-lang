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

from collections import deque

class Queue:
    def __init__(self):
        self.__q    = deque()
        self.__list = None

    def push(self, val):
        self.__q.append(val)
        self.__list = None

    def pop(self):
        if len(self.__q) == 0: return None
        self.__list = None
        return self.__q.popleft()

    def look(self):
        if len(self.__q) == 0: return None
        return self.__q[0]

    def isEmpty(self):
        return len(self.__q) == 0

    def toList(self):
        if self.__list == None:
            self.__list = list(self.__q)

        return self.__list

    def __repr__(self):
        return str(self.toList())

    def __len__(self):
        return len(self.__q)

    def __str__(self):
        return str(self.toList())
