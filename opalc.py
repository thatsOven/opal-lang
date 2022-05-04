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

import re, os, sys, py_compile, importlib
from timeit  import default_timer
from pathlib import Path

OPS = ("+=", "-=", "**=", "//=", "*=", "/=", "%=", "&=", "|=", "^=", ">>=", "<<=", "=")

class GenericLoop: pass

class CompLoop:
    def __init__(self, comp):
        self.comp = comp

class Macro:
    def __init__(self, name, args = None):
        self.name = name
        self.args = args
        self.code = ""

    def addLine(self, line):
        self.code += line

class Compiler:
    def __init__(self):
        self.out = ""
        self.useIdentifiers = {}

        self.macros = {}
        self.consts = {}

        self.hadError  = False
        self.asDynamic = False
        self.__resetImports()

    def __error(self, msg):
        self.hadError = True
        print("error:", msg)

    def __warning(self, msg, line):
        print(f"warning (line {str(line + 1)}):", msg)

    def __lineErr(self, msg, line):
        self.hadError = True
        print(f"error (line {str(line + 1)}):", msg)

    def __resetImports(self):
        self.imports = {
            "OPAL_ASSERT_CLASSVAR": False,
            "asyncio": False
        }

    def newObj(self, objNames, name, type_):
        if self.asDynamic and type_ != "untyped":
            objNames[name] = "dynamic"
        else: objNames[name] = type_

    def newIdentifier(self, name, as_):
        self.useIdentifiers[name] = as_

    def getSameLevelParenthesis(self, section, openCh, closeCh, charPtr):
        pCount = 1

        while charPtr < len(section):
            if   section[charPtr] == openCh:
                pCount += 1
            elif section[charPtr] == closeCh:
                pCount -= 1

            if pCount == 0:
                return charPtr

            charPtr += 1

        self.__error('unbalanced parenthesis "' + openCh + closeCh + '"')
        return charPtr

    def getUntil(self, section, ch, charPtr):
        content = ""

        while section[charPtr] != ch or (section[charPtr - 1] == "\\" and section[charPtr] == ch):
            if section[charPtr - 1] == "\\" and section[charPtr] == ch:
                content = content[:-1]

            content += section[charPtr]
            charPtr += 1

            if charPtr >= len(section):
                charPtr = len(section) - 2
                self.__error('expecting character "' + ch + '"')
                break

        charPtr += 1

        return content, charPtr

    def getBlock(self, section, openCh, closeCh, charPtr):
        blockStart = charPtr
        charPtr = self.getSameLevelParenthesis(section, openCh, closeCh, charPtr)
        return section[blockStart:charPtr], charPtr + 1

    def simpleBlockStatement(self, section, objNames, statement, charPtr, tabs, loop, inLoop):
        condition, charPtr = self.getUntil(section, "{", charPtr)
        block, charPtr = self.getBlock(section, "{", "}", charPtr)

        if block.replace(" ", "") == "":
            self.out += ("\t" * tabs) + statement + " " + condition.strip() + ":pass\n"
        else:
            self.out += ("\t" * tabs) + statement + " " + condition.strip() + ":\n"
            objNames = self.__compiler(block, objNames, tabs + 1, inLoop)

        return self.__compiler(section[charPtr:], objNames, tabs, loop)

    def simpleBlock(self, section, objNames, statement, charPtr, tabs, loop):
        _, charPtr = self.getUntil(section, "{", charPtr)
        block, charPtr = self.getBlock(section, "{", "}", charPtr)

        if block.replace(" ", "") == "":
            self.out += ("\t" * tabs) + statement + ":pass\n"
        else:
            self.out += ("\t" * tabs) + statement + ":\n"
            objNames = self.__compiler(block, objNames, tabs + 1, loop)

        return self.__compiler(section[charPtr:], objNames, tabs, loop)

    def matchStatement(self, section, objNames, value, tabs, loop):
        charPtr = 0

        while charPtr < len(section):
            while section[charPtr] == " ":
                charPtr += 1
                if charPtr >= len(section): break

            if re.match(r"\bcase", section[charPtr:]):
                charPtr += 4
                caseVal, charPtr = self.getUntil(section, "{", charPtr)
                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                self.out += ("\t" * tabs) + "elif " + caseVal.strip() + "==" + value + ":\n" + ("\t" * (tabs + 1)) + "_OPAL_MATCHED_" + str(tabs) + "=True\n"
                if block.replace(" ", "") != "":
                    objNames = self.__compiler(block, objNames, tabs + 1, loop)

                return self.matchStatement(section[charPtr:], objNames, value, tabs, loop)

            if re.match(r"\bfound", section[charPtr:]):
                charPtr += 5
                _, charPtr = self.getUntil(section, "{", charPtr)
                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                if block.replace(" ", "") == "": break
                else:
                    self.out += ("\t" * tabs)  + "if _OPAL_MATCHED_" + str(tabs) + ":\n"
                    return self.__compiler(block, objNames, tabs + 1, loop)

            if re.match(r"\bdefault", section[charPtr:]):
                charPtr += 7
                _, charPtr = self.getUntil(section, "{", charPtr)
                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                if block.replace(" ", "") != "":
                    self.out += ("\t" * tabs) + "else:\n"
                    objNames = self.__compiler(block, objNames, tabs + 1, loop)
                    return self.matchStatement(section[charPtr:], objNames, value, tabs, loop)

            charPtr += 1

        return objNames

    def getOp(self, expr):
        for op in OPS:
            names = expr.split(op, maxsplit = 1)
            if len(names) == 2: return op, names

    def __isBlockNew(self, section):
        return (
            re.match(r"\bfunction ",       section) or
            re.match(r"\bclass ",          section) or
            re.match(r"\bstaticmethod ",   section) or
            re.match(r"\bclassmethod ",    section) or
            re.match(r"\bmethod ",         section) or
            re.match(r"\brecord ",         section)
            )

    def __compiler(self, section, objNames, tabs, loop):
        charPtr = 0
        lastPkg = ""
        nextUnchecked = False

        while charPtr < len(section):
            while section[charPtr] == " ":
                charPtr += 1
                if charPtr >= len(section): break

            found = False
            if re.match(r"\bnew ", section[charPtr:]):
                charPtr += 4
                if self.__isBlockNew(section[charPtr:]):
                    hasThis = False
                    isRecord = False
                    if re.match(r"\bfunction ", section[charPtr:]):
                        translates = "def"
                        charPtr += 9
                    elif re.match(r"\bstaticmethod ", section[charPtr:]):
                        translates = "@staticmethod\n" + ("\t" * tabs) + "def"
                        charPtr += 13
                    elif re.match(r"\bclassmethod ", section[charPtr:]):
                        translates = "@classmethod\n" + ("\t" * tabs) + "def"
                        charPtr += 11
                        hasThis = True
                    elif re.match(r"\bmethod ", section[charPtr:]):
                        translates = "def"
                        charPtr += 7
                        hasThis = True
                    elif re.match(r"\brecord ", section[charPtr:]):
                        translates = "class"
                        charPtr += 7
                        isRecord = True
                    else:
                        translates = "class"
                        charPtr += 6

                    if translates != "class" or isRecord:
                        name, charPtr = self.getUntil(section, "(", charPtr)
                        name = name.replace(" ", "")

                        args, charPtr = self.getBlock(section, "(", ")", charPtr)
                        args = args.strip()

                        if hasThis:
                            args = "this," + args

                        rawParams = re.split(r'(?![^(]*\)),', args.replace(" ", ""))

                        params = []

                        for param in rawParams:
                            if   param.startswith("**"):
                                fparam = param[2:].strip()
                            elif param.startswith("*"):
                                fparam = param[1:].strip()
                            else:
                                fparam = param.strip()

                            if fparam != "":
                                params.append(fparam.split("=", maxsplit = 1)[0])

                        if isRecord:
                            self.newObj(objNames, name, "class")

                            _, charPtr = self.getUntil(section, ";", charPtr)

                            self.out += (
                                ("\t" * tabs) + "class " + name + ":\n" +
                                ("\t" * (tabs + 1)) + "def __init__(this," + args + "):\n"
                            )

                            for p in params:
                                self.out += ("\t" * (tabs + 2)) + "this." + p + "=" + p + "\n"

                            continue
                        else:
                            self.newObj(objNames, name, "untyped")

                            _, charPtr = self.getUntil(section, "{", charPtr)
                    else:
                        info, charPtr = self.getUntil(section, "{", charPtr)
                        info = info.split(":", maxsplit = 1)
                        name = info[0].replace(" ", "")

                        if len(info) == 2:
                            args = info[1].replace(" ", "")
                        else:
                            args = ""

                        self.newObj(objNames, name, "class")

                    block, charPtr = self.getBlock(section, "{", "}", charPtr)

                    if args.replace(" ", "") == "" and translates == "class":
                        self.out += ("\t" * tabs) + translates + " " + name + ":\n"
                    else:
                        self.out += ("\t" * tabs) + translates + " " + name + "(" + args + "):\n"

                    if block.replace(" ", "") == "":
                        self.out += ("\t" * (tabs + 1)) + "pass\n"
                        continue
                    else:
                        if translates == "class": self.__compiler(block, objNames, tabs + 1, loop)
                        else:
                            intObjs = objNames.copy()
                            for name in params:
                                intObjs[name] = "dynamic"
                            self.__compiler(block, intObjs, tabs + 1, loop)
                        return self.__compiler(section[charPtr:], objNames, tabs, loop)
                else:
                    info, charPtr = self.getUntil(section, ";", charPtr)

                    tmp = info.split(" ", maxsplit = 1)
                    varType = tmp[0].replace(" ", "")
                    varList = re.split(r'(?![^(]*\)),', tmp[1])

                    for var in varList:
                        if var.replace(" ", "") == "": continue

                        internalInfo = var.split("=", maxsplit=1)

                        if len(internalInfo) == 1:
                            name = var.replace(" ", "")

                            if varType != "dynamic":
                                if re.match(r"\<.+\>", varType):
                                    classType, _ = self.getUntil(varType, ">", 1)
                                    self.newObj(objNames, name, "classVar::" + classType)

                                    if not self.imports["OPAL_ASSERT_CLASSVAR"]:
                                        self.out = "from libs.std import _OPAL_ASSERT_CLASSVAR_TYPE_\n" + self.out
                                        self.imports["OPAL_ASSERT_CLASSVAR"] = True
                                else:
                                    self.newObj(objNames, name, varType)
                            else:
                                self.newObj(objNames, name, "dynamic")
                        else:
                            name = internalInfo[0].replace(" ", "")
                            internalInfo[1] = internalInfo[1].strip()

                            if varType != "dynamic":
                                if re.match(r"\<.+\>", varType):
                                    classType, _ = self.getUntil(varType, ">", 1)
                                    self.newObj(objNames, name, "classVar::" + classType)

                                    if not self.imports["OPAL_ASSERT_CLASSVAR"]:
                                        self.out = "from libs.std import _OPAL_ASSERT_CLASSVAR_TYPE_\n" + self.out
                                        self.imports["OPAL_ASSERT_CLASSVAR"] = True

                                    self.out += ("\t" * tabs) + name + "=_OPAL_ASSERT_CLASSVAR_TYPE_(" + classType + "," + internalInfo[1] + ")\n"
                                else:
                                    self.newObj(objNames, name, varType)

                                    if varType == "auto":
                                        self.out += ("\t" * tabs) + name + "=" + internalInfo[1] + "\n"
                                    else:
                                        self.out += ("\t" * tabs) + name + "=" + varType + "(" + internalInfo[1] + ")" + "\n"
                            else:
                                self.newObj(objNames, name, "dynamic")
                                self.out += ("\t" * tabs) + name + "=" + internalInfo[1] + "\n"

                    continue

            if re.match(r"\bnamespace ", section[charPtr:]):
                charPtr += 10
                name, charPtr = self.getUntil(section, "{", charPtr)
                name = name.replace(" ", "")

                self.newObj(objNames, name, "class")

                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                if block.replace(" ", "") == "":
                    self.out += ("\t" * tabs) + "class " + name + ":pass\n"
                    continue
                else:
                    self.out += ("\t" * tabs) + "class " + name + ":\n"

                    self.__compiler(block, objNames, tabs + 1, loop)
                    return self.__compiler(section[charPtr:], objNames, tabs, loop)

            if re.match(r"\bimport ", section[charPtr:]):
                charPtr += 7
                module, charPtr = self.getUntil(section, ";", charPtr)
                modules = module.split(",")

                broken = False

                for item in modules:
                    item = item.replace(" ", "")
                    if item != "*":
                        self.newObj(objNames, item, "untyped")
                    else:
                        if lastPkg == "":
                            self.__error('"import *" has been found with no defined package')
                            broken = True
                            break
                        else:
                            modl = importlib.import_module(lastPkg)
                            for name in dir(modl):
                                if callable(getattr(modl, name)):
                                    self.newObj(objNames, name, "untyped")

                            del modl

                        lastPkg = ""

                if not broken:
                    self.out += ("\t" * tabs) + "import " + module + "\n"

                continue

            if re.match(r"\basync:", section[charPtr:]):
                charPtr += 6

                if not self.imports["asyncio"]:
                    self.out = "import asyncio\n" + self.out
                    self.imports["asyncio"] = True

                self.out += "async "

                continue

            if re.match(r"\bawait:", section[charPtr:]):
                charPtr += 6

                if not self.imports["asyncio"]:
                    self.out = "import asyncio\n" + self.out
                    self.imports["asyncio"] = True

                self.out += "await "

                continue

            if re.match(r"\buse ", section[charPtr:]):
                charPtr += 4
                identifier, charPtr = self.getUntil(section, ";", charPtr)

                identifier = identifier.split(" as ", maxsplit=1)
                identifier[0] = identifier[0].replace(" ", "")

                if len(identifier) == 1:
                    self.newIdentifier(identifier[0], "::python")
                else:
                    identifier[1] = identifier[1].replace(" ", "")
                    self.newIdentifier(identifier[0], identifier[1].strip())

                continue

            if re.match(r"\@.*", section[charPtr:]):
                expr, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + expr + "\n"

                continue

            if re.match(r"\bunchecked:", section[charPtr:]):
                charPtr += 10
                nextUnchecked = True

                continue

            if re.match(r"\bquit;", section[charPtr:]):
                charPtr += 5
                self.out += ("\t" * tabs) + "quit()\n"

                continue

            if re.match(r"\breturn;", section[charPtr:]):
                charPtr += 7
                self.out += ("\t" * tabs) + "return\n"

                continue

            if re.match(r"\bbreak;", section[charPtr:]):
                charPtr += 6

                if loop is None:
                    self.__error('"break" has been found outside of a loop')
                    continue

                self.out += ("\t" * tabs) + "break\n"

                continue

            if re.match(r"\bcontinue;", section[charPtr:]):
                charPtr += 9

                if loop is None:
                    self.__error('"continue" has been found outside of a loop')
                    continue
                elif isinstance(loop, CompLoop):
                    self.out += ("\t" * tabs) + loop.comp

                self.out += ("\t" * tabs) + "continue\n"

                continue

            if re.match(r"\bpackage ", section[charPtr:]):
                charPtr += 8
                lastPkg, charPtr = self.getUntil(section, ":", charPtr)
                lastPkg = lastPkg.strip()
                self.out += ("\t" * tabs) + "from " + lastPkg + " "

                continue

            if re.match(r"\breturn ", section[charPtr:]):
                charPtr += 7
                value, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "return " + value.strip() + "\n"

                continue

            if re.match(r"\bsuper\W", section[charPtr:]):
                charPtr += 5
                expr, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "super" + expr.strip() + "\n"

                continue

            if re.match(r"\bdel ", section[charPtr:]):
                charPtr += 4
                name, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "del " + name.strip() + "\n"

                continue

            if re.match(r"\bassert ", section[charPtr:]):
                charPtr += 7
                expr, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "assert " + expr.strip() + "\n"

                continue

            if re.match(r"\byield ", section[charPtr:]):
                charPtr += 6
                expr, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "yield " + expr.strip() + "\n"

                continue

            if re.match(r"\bglobal ", section[charPtr:]):
                charPtr += 7
                var, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "global " + var.replace(" ", "") + "\n"

                continue

            if re.match(r"\bexternal ", section[charPtr:]):
                charPtr += 9
                var, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "nonlocal " + var.replace(" ", "") + "\n"

                continue

            if re.match(r"\?[a-zA-Z0-9]+", section[charPtr:]):
                charPtr += 1
                value, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + "print(" + value.strip() + ")\n"

                continue

            if re.match(r"\!.*", section[charPtr:]):
                charPtr += 1
                var, charPtr = self.getUntil(section, ";", charPtr)
                self.out += ("\t" * tabs) + var + "=not " + var + "\n"

                continue

            if re.match(r"\bmain\s*\{", section[charPtr:]):
                charPtr += 4
                return self.simpleBlock(section, objNames, 'if __name__=="__main__"', charPtr, tabs, loop)

            if re.match(r"\btry\s*\{", section[charPtr:]):
                charPtr += 3
                return self.simpleBlock(section, objNames, "try", charPtr, tabs, loop)

            if re.match(r"\bcatch.*\{", section[charPtr:]):
                charPtr += 5
                return self.simpleBlockStatement(section, objNames, "except", charPtr, tabs, loop, loop)

            if re.match(r"\bsuccess\s*\{", section[charPtr:]):
                charPtr += 7
                return self.simpleBlock(section, objNames, "else", charPtr, tabs, loop)

            if re.match(r"\belse\s*\{", section[charPtr:]):
                charPtr += 4
                return self.simpleBlock(section, objNames, "else", charPtr, tabs, loop)

            if re.match(r"\bif.+\{", section[charPtr:]):
                charPtr += 2
                return self.simpleBlockStatement(section, objNames, "if", charPtr, tabs, loop, loop)

            if re.match(r"\belif.+\{", section[charPtr:]):
                charPtr += 4
                return self.simpleBlockStatement(section, objNames, "elif", charPtr, tabs, loop, loop)

            if re.match(r"\bwhile.+\{", section[charPtr:]):
                charPtr += 5
                return self.simpleBlockStatement(section, objNames, "while", charPtr, tabs, loop, GenericLoop())

            if re.match(r"\bwith.+\{", section[charPtr:]):
                charPtr += 4
                return self.simpleBlockStatement(section, objNames, "with", charPtr, tabs, loop, loop)

            if re.match(r"\bdo.+\{", section[charPtr:]):
                charPtr += 2
                condition, charPtr = self.getUntil(section, "{", charPtr)
                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                self.out += ("\t" * tabs) + "while True:\n"
                check = "if not (" + condition.strip() + "):break\n"
                objNames = self.__compiler(block, objNames, tabs + 1, CompLoop(check))
                self.out += ("\t" * (tabs + 1)) + check

                return self.__compiler(section[charPtr:], objNames, tabs, loop)

            if re.match(r"\bfor.+\{", section[charPtr:]):
                charPtr += 3
                info, charPtr = self.getUntil(section, "{", charPtr)
                info = info.split(";")

                if len(info) == 1:
                    variables = info[0].split(" in ")[0].replace(" ", "")
                    if len(variables) != 0:
                        if variables[0] == "(":
                            variables = variables[1:]
                    variables = [x for x in re.split(r'(?![^(]*\)),', variables) if x != ""]

                    for variable in variables:
                        variable = variable.replace(" ", "")
                        if variable != "":
                            self.newObj(objNames, variable, "dynamic")

                    statement = "for " + info[0] + ":\n"
                else:
                    variables = info[0].replace(" ", "")
                    if len(variables) != 0:
                        if variables[0] == "(":
                            variables = variables[1:]
                    variables = re.split(r'(?![^(]*\)),', variables)

                    increments = info[2].replace(" ", "").replace("++", " += 1").replace("--", " -= 1")
                    if len(increments) != 0:
                        if increments[-1] == ")":
                            increments = increments[:-1]
                    increments = [x for x in re.split(r'(?![^(]*\)),', increments) if x != ""]

                    statement = ""
                    for variable in variables:
                        variable = variable.replace(" ", "")
                        if variable != "":
                            self.newObj(objNames, variable.split("=")[0], "dynamic")
                            statement += variable + "\n" + ("\t" * tabs)

                    info[1] = info[1].strip()

                    if info[1] == "": statement += "while True:\n"
                    else:             statement += "while " + info[1] + ":\n"

                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                self.out += ("\t" * tabs) + statement

                if len(info) != 1 and len(increments) != 0:
                    finalInc = ""
                    for increment in increments:
                        increment = increment.replace(" ", "")
                        if increment != "":
                            finalInc += increment + "\n" + ("\t" * (tabs + 1))
                    finalInc = finalInc[:-(tabs + 1)]
                else: finalInc = ""

                objNames = self.__compiler(block, objNames, tabs + 1, CompLoop(finalInc))

                if finalInc != "":
                    self.out += ("\t" * (tabs + 1)) + finalInc

                return self.__compiler(section[charPtr:], objNames, tabs, loop)

            if re.match(r"\brepeat.+\{", section[charPtr:]):
                charPtr += 6
                value, charPtr = self.getUntil(section, "{", charPtr)
                value = value.strip()

                try:
                    _ = int(value)
                except ValueError:
                    block, charPtr = self.getBlock(section, "{", "}", charPtr)

                    self.out += ("\t" * tabs) + "for _ in range(int(abs(" + value + "))):\n"

                    objNames = self.__compiler(block, objNames, tabs + 1, GenericLoop())
                    return self.__compiler(section[charPtr:], objNames, tabs, loop)
                else:
                    if int(value) == 0:
                        charPtr = self.getSameLevelParenthesis(section, "{", "}", charPtr)
                        continue
                    else:
                        block, charPtr = self.getBlock(section, "{", "}", charPtr)

                        if int(value) > 0:
                            self.out += ("\t" * tabs) + "for _ in range(" + value + "):\n"
                        else:
                            self.out += ("\t" * tabs) + "for _ in range(" + value + ",1):\n"

                        objNames = self.__compiler(block, objNames, tabs + 1, GenericLoop())
                        return self.__compiler(section[charPtr:], objNames, tabs, loop)

            if re.match(r"\bmatch.+\{", section[charPtr:]):
                charPtr += 5
                value, charPtr = self.getUntil(section, "{", charPtr)
                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                matched = str(tabs)
                self.out += ("\t" * tabs) + "_OPAL_MATCHED_" + matched + "=False\n" + ("\t" * tabs) + "if False:pass\n"
                objNames = self.matchStatement(block, objNames, value.strip(), tabs, loop)
                self.out += ("\t" * tabs) + "del _OPAL_MATCHED_" + matched + "\n"

                return self.__compiler(section[charPtr:], objNames, tabs, loop)

            if re.match(r"\benum.+\{", section[charPtr:]):
                charPtr += 4
                name, charPtr = self.getUntil(section, "{", charPtr)
                name = name.replace(" ", "")
                block, charPtr = self.getBlock(section, "{", "}", charPtr)

                variables = re.split(r'(?![^(]*\)),', block)
                names     = [x.split("=", maxsplit = 1)[0].replace(" ", "") for x in variables]

                if name != "":
                    inTabs = tabs + 1
                    self.out += ("\t" * tabs) + "class " + name + ":\n" + ("\t" * inTabs)
                else: inTabs = tabs

                self.out += "\t" * tabs
                for varName in names:
                    self.out += varName + ","

                if self.out[-1] == ",":
                    self.out = self.out[:-1]

                self.out += ("\t" * tabs) + "=range(" + str(len(variables)) + ")\n"

                for varName in variables:
                    splitted = varName.split("=", maxsplit = 1)

                    if len(splitted) == 2:
                        self.out += ("\t" * inTabs) + splitted[0].replace(" ", "") + "=" + splitted[1].strip() + "\n"

                continue

            if re.match(r"\bdynamic:\s*", section[charPtr:]):
                charPtr += 8
                expr, charPtr = self.getUntil(section, ";", charPtr)
                op, names = self.getOp(expr)
                names[0] = names[0].replace(" ", "")

                varsSplitted = names[0].split(",")

                autoTypes = []
                if not nextUnchecked:
                    for name in varsSplitted:
                        name = name.replace(" ", "")
                        if objNames[name] == "auto":
                            autoTypes.append("_OPAL_AUTOMATIC_TYPE_" + name)
                            self.out += ("\t" * tabs) + "_OPAL_AUTOMATIC_TYPE_" + name + "=type(" + name + ")\n"

                self.out += ("\t" * tabs) + names[0] + op + names[1].strip() + "\n"

                if not nextUnchecked:
                    for name in varsSplitted:
                        name = name.replace(" ", "")
                        if objNames[name] != "untyped":
                            testing = re.sub(r"\w*", "", name).replace(" ", "")

                            if not (re.match(r"\[+", testing) or re.match(r"\]+", testing) or re.match(r"\.+", testing)):
                                if objNames[name] != "dynamic":
                                    if objNames[name] != "auto":
                                        splitted = objNames[name].split("::", maxsplit = 1)
                                        if len(splitted) == 2 and splitted[0] == "classVar":
                                            self.out += ("\t" * tabs) + name + "=_OPAL_ASSERT_CLASSVAR_TYPE_(" + splitted[1] + "," + name + ")\n"
                                        else:
                                            self.out += ("\t" * tabs) + name + "=" + objNames[name] + "(" + name + ")\n"
                                    else:
                                        self.out += ("\t" * tabs) + name + "=_OPAL_AUTOMATIC_TYPE_" + name + "(" + name + ")\n" + ("\t" * tabs) + "del _OPAL_AUTOMATIC_TYPE_" + name
                else: nextUnchecked = False

                continue

            if re.match(r"\bdynamic\s*\<\-\s*", section[charPtr:]):
                charPtr += 7
                _, charPtr = self.getUntil(section, "<", charPtr)
                charPtr += 1
                expr, charPtr = self.getUntil(section, ";", charPtr)
                op, names = self.getOp(expr)
                names[0] = names[0].replace(" ", "")

                left = names[0]

                names[0] = names[0].split(",")

                for name in names[0]:
                    objNames[name] = "dynamic"

                self.out += ("\t" * tabs) + left + op + names[1].strip() + "\n"

                continue

            for variable in objNames:
                if re.match(rf"\b{variable}\W", section[charPtr:]):
                    found = True

                    expr, charPtr = self.getUntil(section, ";", charPtr)

                    self.out += ("\t" * tabs)

                    if objNames[variable] != "untyped":
                        expr = expr.replace("++", " += 1").replace("--", " -= 1").strip()
                        splitted = expr.split("=", maxsplit = 1)
                        splitted[0] = splitted[0].replace(" ", "")

                        if not nextUnchecked:
                            testing = re.sub(r"\w*", "", splitted[0]).replace(" ", "")
                            if not (re.match(r"\[+", testing) or re.match(r"\]+", testing) or re.match(r"\.+", testing)):
                                if len(splitted) != 1:
                                    splitted[1] = splitted[1].strip()

                                    if objNames[variable] != "dynamic":
                                        if objNames[variable] != "auto":
                                            classVarTesting = objNames[variable].split("::", maxsplit = 1)
                                            if len(classVarTesting) == 2 and classVarTesting[0] == "classVar":
                                                self.out += splitted[0] + "=_OPAL_ASSERT_CLASSVAR_TYPE_(" + classVarTesting[1] + "," + splitted[1] + ")\n"
                                            else:
                                                self.out += splitted[0] + "=" + objNames[variable] + "(" + splitted[1] + ")\n"
                                        else:
                                            self.out += splitted[0] + "=type(" + objNames[variable] + ")(" + splitted[1] + ")\n"
                                    else:
                                        self.out += splitted[0] + "=" + splitted[1] + "\n"
                                else:
                                    self.out += expr + "\n"
                            else:
                                self.out += expr + "\n"
                        else:
                            nextUnchecked = False
                            self.out += expr + "\n"
                    else:
                        self.out += expr + "\n"
                    break

            if found: continue

            for identifier in self.useIdentifiers:
                if re.match(rf"\b{identifier}\W", section[charPtr:]):
                    found = True
                    charPtr += len(identifier)
                    expr, charPtr = self.getUntil(section, ";", charPtr)
                    self.out += ("\t" * tabs) + (self.useIdentifiers[identifier] + expr if self.useIdentifiers[identifier] != "::python" else expr[1:]) + "\n"
                    break

            if found: continue

            charPtr += 1

        return objNames

    def replaceConsts(self, expr):
        for const in self.consts:
            expr = re.sub(rf"{const}", str(self.consts[const]), expr)
        return expr

    def getDir(self, expr):
        return eval(self.replaceConsts(expr))

    def readFile(self, fileName):
        content = ""
        with open(fileName, "r") as txt:
            for line in txt:
                content += line
        return content

    def __preCompiler(self, source):
        source = re.sub(r"\/\*[^/\*]+\*\/", "", source)
        result = ""
        savingMacro = None

        for i, line in enumerate(source.split("\n")):
            noSpaceLine = line.replace(" ", "")
            if noSpaceLine == "": continue

            if not noSpaceLine[0] in ("$", "#"):
                if savingMacro is None:
                    result += line
                else: savingMacro.addLine(line)

                continue

            if noSpaceLine[0] == "#":
                continue

            if noSpaceLine[0] == "$":
                _, charPtr = self.getUntil(line, "$", 0)
                expr = line[charPtr:]

                if re.match(r"\binclude\s+.+", expr):
                    if savingMacro is not None:
                        self.__warning("precompiler instruction (include) found inside macro definition. ignoring line", i)
                        continue

                    fileDir = expr[8:]
                    result += self.__preCompiler(self.readFile(self.getDir(fileDir)))

                    continue

                if re.match(r"\bincludeDirectory\s+.+", expr):
                    if savingMacro is not None:
                        self.__warning("precompiler instruction (includeDirectory) found inside macro definition. ignoring line", i)
                        continue

                    rawDir = expr[17:]
                    fileDir = self.getDir(rawDir)

                    included = ""
                    for file in [os.path.join(fileDir, f) for f in os.listdir(fileDir) if f.endswith(".opal")]:
                        included += self.readFile(file) + "\n"

                    result += self.__preCompiler(included)

                    continue

                if re.match(r"\bdefine\s+.+", expr):
                    if savingMacro is not None:
                        self.__warning("precompiler instruction (define) found inside macro definition. ignoring line", i)
                        continue

                    info = expr[7:]
                    info = info.split(" ", maxsplit = 1)
                    self.consts[info[0]] = info[1]

                    continue

                if re.match(r"\bmacro\s+.+", expr):
                    if savingMacro is not None:
                        self.__warning("precompiler instruction (macro) found inside macro definition. ignoring line", i)
                        continue

                    info = expr[6:].replace(" ", "")

                    if info[-1] == ")":
                        name, charPtr = self.getUntil(expr, "(", 6)
                        args = expr[charPtr:]

                        name = name.replace(" ", "")
                        args = args[:-1].replace(" ", "")

                        if args != "": savingMacro = Macro(name, args)
                        else:          savingMacro = Macro(name)
                    else:
                        savingMacro = Macro(info)

                    continue

                if re.match(r"\bend", expr):
                    if savingMacro is None:
                        self.__warning("end of macro found with no macro definition. ignoring line", i)
                        continue

                    if savingMacro.code == "":
                        self.__warning(f'the "{savingMacro.name}" macro is being saved as empty', i)

                    self.macros[savingMacro.name] = savingMacro
                    savingMacro = None

                    continue

                if re.match(r"\bcall\s+.+", expr):
                    if savingMacro is not None:
                        self.__warning("precompiler instruction (call) found inside macro definition. ignoring line", i)
                        continue

                    info = expr[5:].replace(" ", "")

                    if info[-1] == ")":
                        name, charPtr = self.getUntil(expr, "(", 5)
                        args = expr[charPtr:]

                        name = name.replace(" ", "")
                        args = args[:-1].replace(" ", "")

                        if name in self.macros:
                            macro = self.macros[name]

                            if args != "":
                                if macro.args != args:
                                    result += "new dynamic " + macro.args + ";unchecked:" + macro.args + "=" + args + ";"
                                else:
                                    result += "new dynamic " + macro.args + ";"
                            result += macro.code
                        else:
                            self.__lineErr(f'trying to call undefined macro "{name}"', i)
                            continue
                    else:
                        if info in self.macros:
                            result += self.macros[info].code
                        else:
                            self.__lineErr(f'trying to call undefined macro "{info}"', i)
                            continue

                    continue

                self.__warning("unknown or incomplete precompiler instruction. ignoring line", i)

        return self.replaceConsts(result)

    def compile(self, section):
        self.__resetImports()
        self.useIdentifiers = {}
        self.macros = {}
        self.out = ""
        self.hadError  = False

        self.__compiler(self.__preCompiler(section).replace("\t", "").replace("\n", ""), {}, 0, None)
        self.asDynamic = False

        if self.hadError: return ""
        else: return self.out

    def compileFile(self, fileIn):
        return self.compile(self.readFile(fileIn))

    def compileToPY(self, fileIn, fileOut):
        result = self.compileFile(fileIn)

        if result != "":
            with open(fileOut, "w") as txt:
                txt.write(result)

def getHomeDirFromFile(file):
    return str(Path(file).parent.absolute()).replace("\\", "\\\\\\\\")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("opal compiler v2022.5.4 - thatsOven")
    else:
        compiler = Compiler()

        if "--dynamic" in sys.argv:
            compiler.asDynamic = True
            sys.argv.remove("--dynamic")

        if "--dir" in sys.argv:
            findDir = False
            idx = sys.argv.index("--dir")
            sys.argv.pop(idx)
            compiler.consts["HOME_DIR"] = sys.argv.pop(idx).replace("\\", "\\\\")
        else:
            findDir = True

        if sys.argv[1] == "pycompile":
            if len(sys.argv) == 2:
                print('input file required for command "pycompile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                compiler.consts["HOME_DIR"] = getHomeDirFromFile(sys.argv[2])

            if len(sys.argv) == 3:
                compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), "output.py")
            else:
                compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), sys.argv[3].replace("\\", "\\\\"))

            if not compiler.hadError:
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")

        elif sys.argv[1] == "compile":
            if len(sys.argv) == 2:
                print('input file required for command "compile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                compiler.consts["HOME_DIR"] = getHomeDirFromFile(sys.argv[2])

            compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), "tmp.py")

            if not compiler.hadError:
                if len(sys.argv) == 3:
                    py_compile.compile("tmp.py", "output.pyc")
                else:
                    py_compile.compile("tmp.py", sys.argv[3].replace("\\", "\\\\"))
                os.remove("tmp.py")
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
        else:
            sys.argv[1] = sys.argv[1].replace("\\", "\\\\")
            if not os.path.exists(sys.argv[1]):
                print('unknown command or nonexistent file "' + sys.argv[1] + '"')
                sys.exit(1)

            if findDir:
                compiler.consts["HOME_DIR"] = getHomeDirFromFile(sys.argv[1])

            result = compiler.compileFile(sys.argv[1])
            if not compiler.hadError: exec(result)
