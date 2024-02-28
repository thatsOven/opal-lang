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

class NameStack:
    def __init__(self):
        self.array = []

    def push(self, item):
        self.array.append(item)

    def pop(self):
        self.array.pop()

    def lookfor(self, item):
        array = self.array.copy()

        while len(array) > 0:
            curr = array.pop()

            if curr[1] == item:
                return curr
            
    def lookforBeforeFn(self, item):
        array = self.array.copy()

        while len(array) > 0:
            curr = array.pop()

            if curr[1] in ("fn", "cfn"):
                return True

            if curr[1] == item:
                return False
            
        return True

    def getCurrentLocation(self):
        array = self.array.copy()
        curr  = array.pop()
        names = [curr]

        while curr[1] != "file":
            curr = array.pop()
            names.append(curr)

        out = "in "
        for name in reversed(names):
            match name[1]:
                case "file":
                    out += name[0] + ": "
                case "fn" | "cfn":
                    out += name[0] + "()."
                case "macro":
                    out += f"($call {name[0]})."
                case "conditional": pass
                case _:
                    out += name[0] + "."

        return out.strip()[:-1]

class GenericLoop: pass

class CompLoop:
    def __init__(self, comp):
        self.comp = comp

class Macro:
    def __init__(self, name, args = None):
        self.name = name
        self.args = args
        self.code = ""

    def add(self, line):
        self.code += line

class IfBlock:
    def __init__(self, cond):
        self.cond = cond
        self.code = ""

    def add(self, line):
        self.code += line