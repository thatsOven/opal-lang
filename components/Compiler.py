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

from components.utils  import *
from components.Tokens import *
from importlib         import import_module
from traceback         import format_exception
import os

VERSION = (2023, 12, 14)
SET_OPS = ("+=", "-=", "**=", "//=", "*=", "/=", "%=", "&=", "|=", "^=", ">>=", "<<=", "@=", "=")
CYTHON_TYPES = (
    "short", "int", "long", "long long", "float", "bint",
    "double", "long double", "list", "object", "str", 
    "tuple", "dict", "range", "bytes", "bytearray", "complex"
)
CYTHON_FN_TYPES = CYTHON_TYPES + ("void", "bool")
ILLEGAL_CHARS = ("-", "(", ")", "[", "]", "{", "}", "!")

CYTHON_TO_PY_TYPES = {
    "short": "int",
    "long": "int",
    "long long": "int",
    "double": "float",
    "long double": "float",
    "void": "None",
    "bint": "bool"
}

def encode(text):
    return "".join(map(lambda c: rf"\u{ord(c):04x}", text))

def getArgsString(internalVars):
    argsList = []
    for name, type_, mode, default in internalVars:
        if type_ in CYTHON_TO_PY_TYPES:
            type_ = CYTHON_TO_PY_TYPES[type_]

        if type_ in ("dynamic", "auto"):
            if default == "":
                argsList.append(mode + name)
            else:
                argsList.append(mode + name + "=" + default)
        else:
            if default == "":
                argsList.append(f"{mode}{name}:{type_}")
            else:
                argsList.append(f"{mode}{name}:{type_}={default}")

    return ",".join(argsList)
     
class Compiler:
    def __new(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.next()
        objType = next

        hasThis  = False
        isRecord = False

        match next.tok:
            case "function":
                translates = "def"
            case "staticmethod":
                translates = "@staticmethod\n"

                if self.nextAbstract:
                    translates += (" " * tabs) + "@abstractmethod\n"

                translates += (" " * tabs) + "def"
            case "classmethod":
                translates = "@classmethod\n"

                if self.nextAbstract:
                    translates += (" " * tabs) + "@abstractmethod\n"

                translates += (" " * tabs) + "def"
                hasThis = True
            case "method":
                if self.nextAbstract:
                    translates = "@abstractmethod\n" + (" " * tabs) + "def"
                else:
                    translates = "def"

                hasThis = True 
            case "record":
                if self.nextAbstract:
                    self.nextAbstract = False
                    self.__error("cannot create abstract record", next)

                if self.nextCdef:
                    self.nextCdef = False
                    self.__error("cannot use $cdef on record", next)

                translates = "class"
                isRecord = True
            case "class":
                if not self.flags["object"]:
                    self.flags["object"] = True
                    self.out = "from libs._internals import OpalObject\n" + self.out

                translates = "class"
            case _:
                return self.__newVar(tokens, tabs, loop, objNames)
            
        if self.nextUnchecked:
            self.nextUnchecked = False
            self.__error('"unchecked" flag is not effective on functions, methods, records and classes', objType)

        name = tokens.next()

        if translates != "class" or isRecord:
            next = tokens.peek()
            if next.tok != "(":
                if self.nextAbstract:
                    self.nextAbstract = False
                    
                self.__error('expecting character "("', next)
                return loop, objNames
            else: tokens.next()
                        
            args = self.getSameLevelParenthesis("(", ")", tokens)
            if hasThis: 
                if len(args) == 0:
                    args = [Token("this")]
                else:
                    args = [Token("this"), Token(",")] + args

            args = Tokens(args)
            internalVars = []
            if len(args.tokens) != 0:
                while True:
                    next = args.next()
                    mode = ""
                    if next.tok in ("**", "*"):
                        mode = next.tok
                        next = args.next()

                    argName = next.tok

                    if not args.isntFinished():
                        internalVars.append([argName, "dynamic", mode, ""])
                        break
                    
                    next = args.peek()
                    if next is not None and next.tok == ":":
                        args.next()
                        next, type_ = self.getUntilNotInExpr(("=", ","), args, True, False, False)
                        if next != "" and next.tok in ("=", ","): args.pos -= 1
                        type_ = Tokens(type_).join()
                    else:
                        type_ = "dynamic"

                    if type_ == "auto":
                        self.__error('"auto" cannot be used as a parameter type', next)
                        type_ = "dynamic"

                    if not args.isntFinished(): 
                        internalVars.append([argName, type_, mode, ""])
                        break

                    next = args.peek()

                    if next.tok == "=":
                        args.next()
                        tmp, default = self.getUntilNotInExpr(",", args, True, False, False)
                        default = Tokens(default).join()

                        internalVars.append([argName, type_, mode, default])
                        
                        if tmp == "": 
                            break
                        else: 
                            next = tmp
                    else:
                        internalVars.append([argName, type_, mode, ""])

                        if next.tok != ",":
                            self.__error("invalid syntax: arguments should be separated by commas", next)
                        else:
                            next = args.next()

                    if next is None: break
                
            if self.nextAbstract:
                self.nextAbstract = False

                if self.nextStatic:
                    self.nextStatic = False
                    self.__error('cannot use "static" flag on an abstract method', objType)

                if self.nextCdef:
                    self.nextCdef = False
                    self.__error('cannot use $cdef on an abstract method', objType)

                self.newObj(objNames, name, "dynamic")

                peek = tokens.peek()
                if peek is None:
                    self.__error('invalid syntax: expecting ";" or type identifier', next)
                    return loop, objNames

                if peek.tok == ";":
                    tokens.next()
                    retType = "dynamic"
                else:                        
                    _, retType = self.getUntilNotInExpr(";", tokens, True, advance = False)
                    retType = Tokens(retType).join()

                    if retType == "auto":
                        self.__error('"auto" cannot be used as a return type', next)
                        retType = "dynamic"

                if retType in CYTHON_TO_PY_TYPES:
                    retType = CYTHON_TO_PY_TYPES[retType]

                argsString = getArgsString(internalVars)
                        
                if retType == "dynamic":
                    self.out += (" " * tabs) + translates + " " + name.tok + f"({argsString}):pass\n"
                else:
                    self.out += (" " * tabs) + translates + " " + name.tok + f"({argsString})->{retType}:pass\n"

                if self.nextGlobal:
                    self.nextGlobal = False
                    self.out += (" " * tabs) + f"globals()['{name.tok}']={name.tok}\n"

                return loop, objNames
            
            if isRecord:
                if self.nextStatic:
                    self.nextStatic = False
                    self.__error('cannot use "static" flag on a record', objType)

                self.newObj(objNames, name, "class")

                parents = ""
                next = tokens.peek()
                if next is None:
                    self.__error('expecting ";" after record definition', tokens.last())
                elif next.tok == "<-":
                    tokens.next()
                    parents = "(" + Tokens(self.getUntilNotInExpr(";", tokens, True, advance = False)[1]).join() + ")"
                elif next.tok == ";":
                    tokens.next()
                else:
                    self.__error('expecting ";" or "<-" after record definition', next)

                argsString = getArgsString(internalVars)

                self.out += (
                    (" " * tabs) + "class " + name.tok + parents + ":\n" +
                    (" " * (tabs + 1)) + f"def __init__(this,{argsString}):\n"
                )

                for var in internalVars:
                    if var[1] == "dynamic":
                        self.out += (" " * (tabs + 2)) + f"this.{var[0]}={var[0]}\n"
                    else:
                        self.out += (" " * (tabs + 2)) + f"this.{var[0]}:{var[1]}={var[0]}\n"

                if self.nextGlobal:
                    self.nextGlobal = False
                    self.out += (" " * tabs) + f"globals()['{name.tok}']={name.tok}\n"

                return loop, objNames
            
            self.newObj(objNames, name, "dynamic")
        
            peek = tokens.peek()
            if peek is None:
                self.__error('invalid syntax: expecting "{" or type identifier', next)
                return loop, objNames

            canCpdef = False
            if peek.tok == "{":
                tokens.next()
                retType = "dynamic"
            else:
                _, retType = self.getUntilNotInExpr("{", tokens, True, advance = False)
                retType = Tokens(retType).join()

                if retType == "auto":
                    self.__error('"auto" cannot be used as a return type', next)
                    retType = "dynamic"

                if self.__cy:
                    if (not hasThis) and translates == "def" and retType in CYTHON_FN_TYPES:
                        canCpdef = True
                        for variable in internalVars:
                            if variable[1] not in CYTHON_FN_TYPES or variable[2] != "":
                                canCpdef = False
                                break

                        if canCpdef: 
                            translates = "cpdef"
                            cyInternalVars = internalVars.copy()
                            for i in range(len(internalVars)):
                                internalVars[i] = (internalVars[i][0], "dynamic", "", internalVars[i][3])

            if (not canCpdef):
                if retType in CYTHON_TO_PY_TYPES:
                    retType = CYTHON_TO_PY_TYPES[retType]

                argsString = getArgsString(internalVars)
        else:
            argsString = ""
            
            next = tokens.peek()
            if next.tok == ":":
                next = tokens.next()
                next, args = self.getUntil("{", tokens, True)
                argsString = Tokens(args).join() + ",OpalObject"
                
                if self.nextAbstract:
                    self.nextAbstract = False
                    argsString += ",_ABSTRACT_BASE_CLASS_,OpalObject"
            else:
                next = self.checkDirectNext("{", "class definition", tokens)

                if self.nextAbstract:
                    self.nextAbstract = False
                    argsString = "_ABSTRACT_BASE_CLASS_,OpalObject"

            self.newObj(objNames, name, "class")

        if translates == "cpdef":
            if self.nextCdef:
                self.nextCdef = False
                translates = "cdef"

            argsList = []
            for name_, type_, _, default in cyInternalVars:
                if default == "":
                    argsList.append(f"{type_} {name_}")
                else:
                    argsList.append(f"{type_} {name_}={default}")

            argsString = ",".join(argsList)

            if self.nextInline:
                self.nextInline = False
                self.out += (" " * tabs) + translates + " inline " + retType + " " + name.tok + "(" + argsString + "):"
            else:
                self.out += (" " * tabs) + translates + " " + retType + " " + name.tok + "(" + argsString + "):"
        else:
            if self.nextInline:
                self.nextInline = False
                if self.__cy: self.__error('"inline" flag can only be used on optimizable functions', objType)

            isClass = translates == "class"

            if self.nextCdef:
                self.nextCdef = False
                self.__error('$cdef can only be used on classes and optimizable functions', objType)
            
            if isClass and argsString == "":
                self.out += (" " * tabs) + translates + " " + name.tok + "(OpalObject):"
            elif isClass or retType == "dynamic":
                self.out += (" " * tabs) + translates + " " + name.tok + "(" + argsString + "):"
            else:
                self.out += (" " * tabs) + translates + " " + name.tok + "(" + argsString + f")->{retType}:"

        block = self.getSameLevelParenthesis("{", "}", tokens)
        if len(block) == 0:
            self.out += "pass\n"

            if self.nextGlobal:
                self.nextGlobal = False
                self.out += (" " * tabs) + f"globals()['{name.tok}']={name.tok}\n"

            return loop, objNames
        
        self.out += "\n"
        
        block = Tokens(block)
        
        if translates == "class":
            self.__nameStack.push((name.tok, "class"))

            glob = self.nextGlobal
            self.nextGlobal = False

            if self.nextStatic:
                self.nextStatic = False

                backStatic = self.static
                self.static = True
                self.__compiler(block, tabs + 1, loop, objNames)
                self.static = backStatic
            else:
                self.__compiler(block, tabs + 1, loop, objNames)

            self.__nameStack.pop()

            if glob:
                self.out += (" " * tabs) + f"globals()['{name.tok}']={name.tok}\n"

            return loop, objNames

        intObjs = objNames.copy()
        for var in internalVars:
            intObjs[var[0]] = var[1]

        if translates in ("cpdef", "cdef"):
            self.__nameStack.push((name.tok, "cfn"))
        else:
            self.__nameStack.push((name.tok, "fn", retType))

        glob = self.nextGlobal
        self.nextGlobal = False

        if self.nextStatic:
            self.nextStatic = False

            backStatic = self.static
            self.static = True
            self.__compiler(block, tabs + 1, loop, intObjs)
            self.static = backStatic
        else:
            self.__compiler(block, tabs + 1, loop, intObjs)

        self.__nameStack.pop()

        if glob:
            self.out += (" " * tabs) + f"globals()['{name.tok}']={name.tok}\n"

        return loop, objNames
    
    def __newVar(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.last()
        typeTok = next

        if next.tok == "(":
            type_ = Tokens(self.getSameLevelParenthesis("(", ")", tokens)).join()
        else:
            type_ = next.tok
        
        cyType = False
        if (
            self.__cy and (self.nextStatic or self.static) and
            self.__nameStack.lookforBeforeFn("class") and 
            (not self.nextUnchecked) and (not self.nextGlobal)
        ):
            if type_ in CYTHON_TYPES:
                if loop is not None:
                    self.__note("consider moving these declarations outside of a loop so they can be automatically optimized", typeTok)
                elif not self.__nameStack.lookforBeforeFn("conditional"):
                    self.__note("consider moving these declarations outside of a conditional so they can be automatically optimized", typeTok)
                else:
                    cyType = True
        
        if self.nextStatic: self.nextStatic = False

        if (not cyType) and type_ in CYTHON_TO_PY_TYPES:
            type_ = CYTHON_TO_PY_TYPES[type_]

        if self.nextUnchecked:
            self.nextUnchecked = False
            unchecked = True

            if type_ in ("auto", "dynamic"):
                self.__error('"unchecked" flag is not effective on "auto" and "dynamic" typing', typeTok)
        else: unchecked = False

        if self.nextGlobal:
            self.nextGlobal = False
            glob = True
        else: glob = False

        if self.nextInline:
            self.nextInline = False
            self.__error('"inline" flag is not effective on variables declarations', typeTok)

        _, variablesDef = self.getUntilNotInExpr(";", tokens, True, advance = False)
        variablesDef = Tokens(variablesDef)
        
        next = variablesDef.next()

        while True:
            name = next

            if cyType: self.newObj(objNames, name, "dynamic")
            else:      self.newObj(objNames, name, type_)

            if not variablesDef.isntFinished(): 
                if type_ not in ("dynamic", "auto"):
                    if cyType:
                        self.out += (" " * tabs) + "cdef " + type_ + " " + name.tok + "\n"
                    else:
                        self.out += (" " * tabs) + name.tok + ":" + type_ + "\n"

                if type_ == "auto":
                    self.__error(f'auto-typed variables cannot be defined without being assigned', name) 

                break
                
            next = variablesDef.next()
            if   next.tok == "=":
                next, value = self.getUntilNotInExpr(",", variablesDef, True, False)
                value = Tokens(value).join()

                if cyType:
                    self.out += (" " * tabs) + "cdef " + type_ + " " + name.tok + "=" + value + "\n"
                else:
                    if unchecked or type_ in ("auto", "dynamic") or self.typeMode == "none":
                        if glob:
                            self.out += (" " * tabs) + f"globals()['{name.tok}']=" + value + "\n"
                        else:
                            self.out += (" " * tabs) + name.tok + "=" + value + "\n"
                    else:
                        if glob:
                            self.out += (" " * tabs) + f"globals()['{name.tok}']=_OPAL_CHECK_TYPE_({value},{type_})\n"
                        else:
                            self.out += (" " * tabs) + name.tok + f":{type_}=_OPAL_CHECK_TYPE_({value},{type_})\n"
            elif next.tok == ",": 
                if (not unchecked) and type_ not in ("dynamic", "auto"):
                    if cyType:
                        self.out += (" " * tabs) + "cdef " + type_ + " " + name.tok + "\n"
                    else:
                        self.out += (" " * tabs) + name.tok + ":" + type_ + "\n"

                next = variablesDef.next()

                if type_ == "auto":
                    self.__error(f'auto-typed variables cannot be defined without being assigned', name) 
            else:
                self.__error('invalid syntax: expecting "," or "="', next) 

            if next == "": break
        
        return loop, objNames
    
    def __not(self, tokens : Tokens, tabs, loop, objNames):
        _, var = self.getUntilNotInExpr(";", tokens, True, advance = False)

        last = tokens.last()

        if self.nextUnchecked:
            self.nextUnchecked = False
            self.__error('"unchecked" flag is not effective on inline boolean inversions', last)

        if self.nextStatic:
            self.nextStatic = False
            self.__error('"static" flag is not effective on inline boolean inversions', last)

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error('"abstract" flag is not effective on inline boolean inversions', last)

        if self.nextInline:
            self.nextInline = False
            self.__error('"inline" flag is not effective on inline boolean inversions', last)

        if self.nextCdef:
            self.nextCdef = False
            self.__error('$cdef is not effective on inline boolean inversions', last)

        if self.nextGlobal:
            self.nextGlobal = False
            self.__error('"global" flag is not effective on inline boolean inversions', last)
    
        self.out += (" " * tabs) + Tokens(var + [Token("="), Token("not")] + var).join() + "\n"

        return loop, objNames
    
    def __asyncGen(self, keyw):
        def fn(tokens : Tokens, tabs, loop, objNames):
            self.out += (" " * tabs) + keyw + " "
            return loop, objNames
        
        return fn
    
    def __flagsError(self, statement, tok):
        if self.nextUnchecked:
            self.nextUnchecked = False
            self.__error(f'"unchecked" flag is not effective on "{statement}" statement', tok)

        if self.nextStatic:
            self.nextStatic = False
            self.__error(f'"static" flag is not effective on "{statement}" statement', tok)

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error(f'"abstract" flag is not effective on "{statement}" statement', tok)

        if self.nextInline:
            self.nextInline = False
            self.__error(f'"inline" flag is not effective on "{statement}" statement', tok)

        if self.nextCdef:
            self.nextCdef = False
            self.__error(f'$cdef is not effective on "{statement}" statement', tok)

        if self.nextGlobal:
            self.nextGlobal = False
            self.__error(f'"global" flag is not effective on "{statement}" statement', tok)
    
    def __return(self, tokens : Tokens, tabs, loop, objNames):
        kw = tokens.last()

        fnProperties = self.__nameStack.lookfor("fn")
        if fnProperties is None and self.__cy:
            cyFunction = True
            fnProperties = self.__nameStack.lookfor("cfn")
        else: cyFunction = False

        if fnProperties is None:
            self.__error('cannot use "return" outside of a function', kw)

        if self.nextStatic:
            self.nextStatic = False
            self.__error('"static" flag is not effective on "return" statement', kw)

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error('"abstract" flag is not effective on "return" statement', kw)

        if self.nextInline:
            self.nextInline = False
            self.__error('"inline" flag is not effective on "return" statement', kw)
        
        if self.nextCdef:
            self.nextCdef = False
            self.__error('$cdef is not effective on "return" statement', kw)

        if self.nextGlobal:
            self.nextGlobal = False
            self.__error('"global" flag is not effective on "return" statement', kw)

        next = tokens.peek()
        if next.tok == ";":
            tokens.next()
            self.out += (" " * tabs) + "return\n"
            return loop, objNames
        
        _, val = self.getUntilNotInExpr(";", tokens, True, advance = False)

        if self.nextUnchecked:
            self.nextUnchecked = False
            unchecked = True
        else: unchecked = False
           
        if cyFunction or unchecked or fnProperties[2] == "dynamic" or self.typeMode == "none":
            self.out += (" " * tabs) + Tokens([Token("return")] + val).join() + "\n"
        else:
            self.out += (" " * tabs) + Tokens(
                [
                    Token("return"), Token("_OPAL_CHECK_TYPE_"), Token("("), Token("(")
                ] + val + [
                    Token(")"), Token(","), Token(fnProperties[2]), Token(")")
                ]
            ).join() + "\n"

        return loop, objNames
    
    def __break(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        next = tokens.peek()
        if next.tok != ";":
            self.__error('expecting ";" after "break"', next)
        else: tokens.next()

        self.__flagsError("break", keyw)

        if loop is None:
            self.__error('cannot use "break" outside of a loop', keyw)
            return loop, objNames

        self.out += (" " * tabs) + "break\n"

        return loop, objNames
    
    def __continue(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        next = tokens.peek()

        if next is None:
            self.__error('expecting ";" after "continue"', keyw)
        elif next.tok != ";":
            self.__error('expecting ";" after "continue"', next)
        else: tokens.next()

        self.__flagsError("continue", keyw)

        if loop is None:
            self.__error('cannot use "continue" outside of a loop', keyw)
            return loop, objNames
        elif isinstance(loop, CompLoop) and not loop.comp == "":
            self.out += (" " * tabs) + loop.comp

        self.out += (" " * tabs) + "continue\n"

        return loop, objNames
    
    def __untilEnd(self, keyw):
        def fn(tokens : Tokens, tabs, loop, objNames):
            _, val = self.getUntilNotInExpr(";", tokens, True, advance = False)

            self.out += (" " * tabs) + Tokens([Token(keyw)] + val).join() + "\n"

            return loop, objNames
    
        return fn
    
    def __ignore(self, tokens : Tokens, tabs, loop, objNames):
        self.__flagsError("ignore", tokens.last())

        _, val = self.getUntilNotInExpr(";", tokens, True, advance = False)
        self.out += (" " * tabs) + Tokens([Token("except")] + val + [Token(":pass")]).join() + "\n"
        return loop, objNames
    
    def __unchecked(self, tokens : Tokens, tabs, loop, objNames):
        kw = tokens.last()

        next = tokens.peek()
        if next.tok != ":":
            self.__error('expecting ":" after "unchecked"', next)
        else: tokens.next()

        if self.nextUnchecked:
            self.__error('"unchecked" flag was used twice. remove this flag', kw)

        self.nextUnchecked = True

        return loop, objNames
    
    def __static(self, tokens: Tokens, tabs, loop, objNames):
        if self.nextStatic:
            self.__error('"static" flag was used twice. remove this flag', tokens.last())

        next = tokens.peek()
        if next.tok == ":":
            tokens.next()
            self.nextStatic = True
        elif next.tok == "{":
            tokens.next()
            block = self.getSameLevelParenthesis("{", "}", tokens)

            if len(block) == 0:
                return loop, objNames
            
            backStatic = self.static
            self.static = True
            loop, objNames = self.__compiler(Tokens(block), tabs, loop, objNames)
            self.static = backStatic
        else: 
            self.__error('expecting ":" or "{" after "static"', next)

        return loop, objNames
    
    def __global(self, tokens: Tokens, tabs, loop, objNames):
        next = tokens.peek()
        if next.tok == ":":
            if self.nextGlobal:
                self.__error('"global" flag was used twice. remove this flag', tokens.last())

            tokens.next()
            self.nextGlobal = True
            return loop, objNames
        
        return self.__untilEnd("global")(tokens, tabs, loop, objNames)
    
    def __inline(self, tokens: Tokens, tabs, loop, objNames):
        if self.nextInline:
            self.__error('"inline" flag was used twice. remove this flag', tokens.last())

        next = tokens.peek()
        if next.tok == ":":
            tokens.next()
            self.nextInline = True
        else: 
            self.__error('expecting ":" after "inline"', next)

        return loop, objNames
    
    def __abstract(self, tokens : Tokens, tabs, loop, objNames):
        if self.nextAbstract:
            self.__error('"abstract" flag was used twice. remove this flag', tokens.last())

        next = tokens.peek()
        if next.tok != ":":
            self.__error('expecting ":" after "abstract"', next)
        else: tokens.next()

        self.nextAbstract = True

        if not self.flags["abstract"]:
            self.flags["abstract"] = True
            self.out = "from abc import abstractmethod\nfrom abc import ABC as _ABSTRACT_BASE_CLASS_\n" + self.out

        return loop, objNames
    
    def __printReturn(self, tokens : Tokens, tabs, loop, objNames):
        self.__flagsError("?", tokens.last())

        _, val = self.getUntilNotInExpr(";", tokens, True, advance = False)
        strVal = Tokens(val).join()

        self.out += (" " * tabs) + "_OPAL_PRINT_RETURN_(" + strVal + ")\n"

        return loop, objNames
    
    def __package(self, tokens : Tokens, tabs, loop, objNames):
        self.__flagsError("package", tokens.last())

        _, name = self.getUntilNotInExpr(":", tokens, True, advance = False)
        strName = Tokens(name).join()

        self.lastPackage = strName

        self.out += (" " * tabs) + "from " + strName + " "

        return loop, objNames
    
    def __import(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        self.__flagsError("import", keyw)
        _, imports = self.getUntilNotInExpr(";", tokens, True, advance = False)
        
        if len(imports) == 1 and imports[0].tok == "*":
            if self.lastPackage == "":
                self.__error('cannot use "import *" if no package is defined', keyw)
                return loop, objNames
            
            if "." in self.lastPackage:
                  self.imports.append(self.lastPackage.split(".")[0])
            else: self.imports.append(self.lastPackage)
            
            modl = import_module(self.lastPackage)
            for name in dir(modl):
                if callable(getattr(modl, name)):
                    self.newObj(objNames, Token(name), "dynamic")

            self.lastPackage = ""
            self.out += "import *\n"

            return loop, objNames
        
        imports = Tokens(imports)
        
        while imports.isntFinished():
            next = imports.next()
            if next == "": break

            name = next
            if self.lastPackage == "": self.imports.append(name.tok)

            next, nameBuf = self.getUntilNotInExpr(("as", ","), imports, True, False, False)
            if next != "" and next.tok in ("as", ","): imports.pos -= 1
            if len(nameBuf) != 0: 
                name = name.copy()
                name.tok = Tokens(nameBuf).join()

            if not imports.isntFinished():
                self.newObj(objNames, name, "dynamic")
                break
                    
            next = imports.next()
            if next.tok == "as":
                next = imports.next()
                name = next

                if imports.isntFinished():
                    next = imports.next()

            self.newObj(objNames, name, "dynamic")

            if not imports.isntFinished(): break

            if next.tok != ",":
                self.__error("invalid syntax: modules should be separated by commas", next)

        if self.lastPackage != "": 
            if "." in self.lastPackage:
                  self.imports.append(self.lastPackage.split(".")[0])
            else: self.imports.append(self.lastPackage)

            self.lastPackage = ""

        self.out += (" " * tabs) + "import " + imports.join() + "\n"

        return loop, objNames
    
    def __incDec(self, op):
        def fn(tokens : Tokens, tabs, loop, objNames):
            self.__flagsError(op * 2, tokens.last())
            _, var = self.getUntilNotInExpr(";", tokens, True, advance = False)
            strVar = Tokens(var).join()

            self.out += (" " * tabs) + strVar + op + "=1\n"

            return loop, objNames
            
        return fn
    
    def __use(self, tokens : Tokens, tabs, loop, objNames):
        self.__flagsError("use", tokens.last())
        _, identifiers = self.getUntilNotInExpr(";", tokens, True, advance = False)
        identifiers = Tokens(identifiers)
        
        next = identifiers.next()
        while True:
            name = next

            self.newObj(objNames, name, "dynamic")

            if not identifiers.isntFinished(): break
                
            next = identifiers.next()
            if next.tok == ",":
                next = identifiers.next()
            else:
                self.__error('invalid syntax: expecting ","', next) 

            if next == "": break
        
        return loop, objNames
    
    def __simpleBlock(self, keyw, kwname, push = None):
        def fn(tokens : Tokens, tabs, loop, objNames):
            self.checkDirectNext("{", f'"{kwname}"', tokens)
            block = self.getSameLevelParenthesis("{", "}", tokens)

            self.out += (" " * tabs) + keyw

            if len(block) == 0:
                self.out += ":pass\n"
            else: 
                self.out += ":\n"

                if push is None:
                    loop, objNames = self.__compiler(Tokens(block), tabs + 1, loop, objNames)
                else:
                    self.__nameStack.push(push)
                    loop, objNames = self.__compiler(Tokens(block), tabs + 1, loop, objNames)
                    self.__nameStack.pop()

            return loop, objNames
        
        return fn
    
    def __block(self, keyw, inLoop = None, content = None, after = None, push = None):
        def fn(tokens : Tokens, tabs, loop, objNames):
            loopNotDef = inLoop is None
            if loopNotDef: 
                internalLoop = loop
            else:
                internalLoop = inLoop
            
            if content is None:
                _, localContent = self.getUntilNotInExpr("{", tokens, True, advance = False)
            else: localContent = content

            block = self.getSameLevelParenthesis("{", "}", tokens)

            self.out += (" " * tabs) + Tokens([Token(keyw)] + localContent).join()

            if after is not None:
                self.out += ":\n" + (" " * (tabs + 1)) + after + "\n"
            else:
                if len(block) == 0:
                    self.out += ":pass\n"
                    return loop, objNames
                 
                self.out += ":\n"

            if push is None:
                tmp, objNames = self.__compiler(Tokens(block), tabs + 1, internalLoop, objNames)
            else:
                self.__nameStack.push(push)
                tmp, objNames = self.__compiler(Tokens(block), tabs + 1, internalLoop, objNames)
                self.__nameStack.pop()

            if loopNotDef: loop = tmp

            return loop, objNames
        
        return fn
        
    def __main(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()

        self.__flagsError("main", keyw)

        next = tokens.peek()
        if next.tok == "(":
            tokens.next()
            next = tokens.next()
            if next.tok != ")":
                self.__error("invalid syntax: brackets should be closed", next)

            if self.flags["mainfn"]:
                self.__error("main function can only be defined once", keyw)
                return loop, objNames
            else:
                self.flags["mainfn"] = True

            if self.__cy:
                return self.__simpleBlock("cpdef void _OPAL_MAIN_FUNCTION_()", "main()", ("main", "cfn"))(tokens, tabs, loop, objNames)
            else:
                return self.__simpleBlock("def _OPAL_MAIN_FUNCTION_()", "main()", ("main", "fn"))(tokens, tabs, loop, objNames)
        
        if self.__cy:
            return self.__simpleBlock('if"_OPAL_RUN_AS_MAIN_"in _ENVIRON_', "main", (None, "conditional"))(tokens, tabs, loop, objNames)
        else:
            return self.__simpleBlock("if __name__=='__main__'", "main", (None, "conditional"))(tokens, tabs, loop, objNames)
    
    def __namespace(self, tokens : Tokens, tabs, loop, objNames):
        kw = tokens.last()
        next = tokens.next()
        self.newObj(objNames, next, "class")
        tmp = tokens.next()

        if self.nextUnchecked:
            self.nextUnchecked = False
            self.__error('"unchecked" flag is not effective on "namespace" statement', kw)

        if self.nextInline:
            self.nextInline = False
            self.__error('"inline" flag is not effective on "namespace" statement', kw)

        if self.nextCdef:
            self.nextCdef = False
            self.__error('$cdef is not effective on "namespace" statement', kw)

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error('cannot create abstract namespace', kw)

        if tmp.tok != "{":
            self.__error('invalid syntax: expecting "{" after namespace definition', tmp)
            return loop, objNames
        
        if not self.flags["namespace"]:
            self.flags["namespace"] = True
            self.out = "from libs._internals import OpalNamespace\n" + self.out

        if self.nextStatic:
            self.nextStatic = False

            backStatic = self.static
            self.static = True
            self.__block("class", content = [next, Token("(OpalNamespace)")], push = (next.tok, "class"))(tokens, tabs, loop, objNames)
            self.static = backStatic
        else:
            self.__block("class", content = [next, Token("(OpalNamespace)")], push = (next.tok, "class"))(tokens, tabs, loop, objNames)

        if self.nextGlobal:
            self.nextGlobal = False
            self.out += (" " * tabs) + f"globals()['{next.tok}']={next.tok}\n"

        return loop, objNames
    
    def __do(self, tokens : Tokens, tabs, loop, objNames):
        self.__flagsError("do", tokens.last())

        peek = tokens.peek()

        if peek.tok == "{":
            tokens.next()
            block = self.getSameLevelParenthesis("{", "}", tokens)

            next = tokens.peek()
            if next.tok != "while":
                self.__warning('expecting "while" after a do-while loop. ignoring', next)
            else: tokens.next()

            _, condition = self.getUntilNotInExpr(";", tokens, True, advance = False)
        else:
            _, condition = self.getUntilNotInExpr("{", tokens, True, advance = False)
            block = self.getSameLevelParenthesis("{", "}", tokens)

        check = f"if not({Tokens(condition).join()}):break\n"

        self.out += (" " * tabs) + "while True:\n"
        _, objNames = self.__compiler(Tokens(block), tabs + 1, CompLoop(check), objNames)
        self.out += (" " * (tabs + 1)) + check

        return loop, objNames
    
    def __repeat(self, tokens : Tokens, tabs, loop, objNames):
        kw = tokens.last()

        if self.nextStatic:
            self.nextStatic = False
            self.__error('"static" flag is not effective on "repeat" statement', kw)

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error('"abstract" flag is not effective on "repeat" statement', kw)

        if self.nextInline:
            self.nextInline = False
            self.__error('"inline" flag is not effective on "repeat" statement', kw)

        if self.nextGlobal:
            self.nextGlobal = False
            self.__error('"global" flag is not effective on "repeat" statement', kw)

        if self.nextCdef:
            self.nextCdef = False
            self.__error('$cdef is not effective on "repeat" statement', kw)

        _, valList = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)
        value = Tokens(valList).join()

        try:
            intVal = int(eval(value))
        except:
            self.out += " " * tabs

            if self.nextUnchecked:
                self.nextUnchecked = False
                self.out += f"for _ in range({value}):"
            else:
                self.out += f"for _ in range(abs(int({value}))):"
        else:
            if self.nextUnchecked:
                self.nextUnchecked = False

            if intVal == 0:
                warnTok = Token(
                    " " * (valList[-1].pos - valList[0].pos + 1), 
                    valList[0].line, valList[0].pos, valList[0].tokens
                )

                warnTok.maxline = valList[0].maxline
                
                self.__warning('a 0-times "repeat" statement is being used', warnTok)

                return loop, objNames
            
            self.out += " " * tabs
            
            if intVal > 0:
                self.out += f"for _ in range({value}):"
            else:
                self.out += f"for _ in range({value},1,-1):"

        if len(block) == 0:
            self.out += "pass\n"
            return loop, objNames
        
        self.out += "\n"

        _, objNames = self.__compiler(Tokens(block), tabs + 1, GenericLoop(), objNames)
        return loop, objNames
    
    def __matchLoop(self, tokens : Tokens, tabs, loop, objNames, value, op, nocheck):
        if op: kw = "if"

        defaultMet = False
        foundMet   = False

        while tokens.isntFinished():
            next = tokens.next()
            
            if next.tok.startswith('"""') or next.tok.startswith("'''"):
                self.out += next.tok + "\n"
                continue

            match next.tok:
                case "case":
                    if foundMet:
                        self.__error('cannot use "case" after "found" in a "match" statement', next)

                    if op:
                        if defaultMet:
                            self.__error('cannot use "case" after "default" in an defined operator "match" statement', next)
                        
                        if nocheck:
                            loop, objNames = self.__block(
                                Tokens([Token(kw)] + value + op).join()
                            )(tokens, tabs, loop, objNames)
                        else:
                            loop, objNames = self.__block(
                                Tokens([Token(kw)] + value + op).join(),
                                after = f"_OPAL_MATCHED_{tabs}=True"
                            )(tokens, tabs, loop, objNames)

                        if kw == "if": kw = "elif"
                    else:
                        if nocheck:
                            loop, objNames = self.__block("case")(tokens, tabs + 1, loop, objNames)
                        else:
                            loop, objNames = self.__block(
                                "case", after = f"_OPAL_MATCHED_{tabs}=True"
                            )(tokens, tabs + 1, loop, objNames)
                case "default":
                    if foundMet:
                        self.__error('cannot use "default" after "found" in a "match" statement', next)

                    if op:
                        loop, objNames = self.__simpleBlock("else", "default")(tokens, tabs, loop, objNames)
                    else:
                        loop, objNames = self.__simpleBlock("case _", "default")(tokens, tabs + 1, loop, objNames)

                    defaultMet = True
                case "found":
                    loop, objNames = self.__simpleBlock(f"if _OPAL_MATCHED_{tabs}", "found")(tokens, tabs, loop, objNames)
                    foundMet = True
                case _:
                    self.__error('invalid identifier in "match" statement body', next)

        return loop, objNames
    
    def __needsChecks(self, tokens: Tokens):
        while tokens.isntFinished():
            next = tokens.next()
            
            if next.tok.startswith('"""') or next.tok.startswith("'''"):
                self.out += next.tok + "\n"
                continue

            match next.tok:
                case "case":
                    self.getUntilNotInExpr("{", tokens, True, advance = False)
                    self.getSameLevelParenthesis("{", "}", tokens)
                case "default":
                    self.checkDirectNext("{", '"default"', tokens)
                    self.getSameLevelParenthesis("{", "}", tokens)
                case "found": return True
                case _:
                    self.__error('invalid identifier in "match" statement body', next)

        return False
    
    def __match(self, tokens : Tokens, tabs, loop, objNames):
        self.__flagsError("match", tokens.last())

        next = tokens.peek()
        if next.tok == ":":
            idLine = next.line
            idPos  = next.pos
            tokens.next()

            next = tokens.next()
            if next.tok != "(":
                self.__error('invalid syntax: expecting "(" after "match:"', next)
            
            op = self.getSameLevelParenthesis("(", ")", tokens)

            if len(op) == 0:
                op = [Token("==", idLine, idPos, tokens)]
        elif self.__cy: op = [Token("==")]
        else:           op = None

        _, value = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)

        if len(block) == 0:
            return loop, objNames
        
        check = self.__needsChecks(Tokens(block))
        
        if check:
            matched = str(tabs)
            self.out += (" " * tabs) + f"_OPAL_MATCHED_{tabs}=False\n"
    
        if op is None:
            self.out += (" " * tabs) + Tokens([Token("match")] + value).join() +":\n"

        self.__nameStack.push((None, "conditional"))
        loop, objNames = self.__matchLoop(Tokens(block), tabs, loop, objNames, value, op, not check)
        self.__nameStack.pop()

        if check:
            self.out += (" " * tabs) + f"del _OPAL_MATCHED_{matched}\n"

        return loop, objNames
    
    @classmethod
    def __getType(self, type_):
        match type_:
            case "getter":
                return "get"
            case "setter":
                return "set"
            case "deleter":
                return "delete"
    
    def __modifier(self, type_, name = None):
        def fn(tokens : Tokens, tabs, loop, objNames):
            if name is None:
                next = tokens.peek()
                if next.tok != "<":
                    self.__error(f'expecting "<" after {type_} outside of a "property" statement', next)
                    localName = next
                else: 
                    tokens.next()
                    localName = Tokens(self.getSameLevelParenthesis("<", ">", tokens)).join()
            else: localName = name

            self.out += (" " * tabs) + Tokens([Token("@"), localName, Token("."), Token(type_)]).join() + "\n"

            if self.nextAbstract:
                self.out += (" " * tabs) + "@abstractmethod\n"

            intObjs = objNames.copy()
            self.newObj(intObjs, Token("this"), "dynamic")

            def_ = [Token("def"), localName, Token("("), Token("this")]

            if type_ == "setter":
                next = tokens.peek()
                if next.tok == "(":
                    tokens.next()
                    valName = self.getSameLevelParenthesis("(", ")", tokens)

                    if len(valName) > 1:
                        self.__error('only one argument should be passed to a setter', valName[0])
                else:
                    valName = [Token("value")]

                def_ += [Token(",")] + valName
                self.newObj(intObjs, valName[0], "dynamic")

            self.out += (" " * tabs) + Tokens(def_).join() + "):"

            if self.nextAbstract:
                self.nextAbstract = False

                self.checkDirectNext(";", "abstract property method definition", tokens)
                self.out += "pass\n"
                return loop, objNames
            
            self.checkDirectNext("{", "property method definition", tokens)
            block = self.getSameLevelParenthesis("{", "}", tokens)

            if len(block) == 0:
                self.out += "pass\n"
                return loop, objNames
            
            self.out += "\n"
            
            if name is None:
                self.__nameStack.push((f"{self.__getType(type_)}<{localName}>", "fn", "dynamic"))
            else:
                self.__nameStack.push((self.__getType(type_), "fn", "dynamic"))

            self.__compiler(Tokens(block), tabs + 1, loop, intObjs)
            self.__nameStack.pop()
            return loop, objNames
        
        return fn
    
    def __propertyLoop(self, tokens : Tokens, tabs, loop, objNames, name):
        while tokens.isntFinished():
            next = tokens.next()
            
            if next.tok.startswith('"""') or next.tok.startswith("'''"):
                self.out += next.tok + "\n"
                continue

            match next.tok:
                case "get":
                    self.__modifier("getter", name)(tokens, tabs, loop, objNames)
                case "set":
                    self.__modifier("setter", name)(tokens, tabs, loop, objNames)
                case "delete":
                    self.__modifier("deleter", name)(tokens, tabs, loop, objNames)
                case "abstract":
                    self.__abstract(tokens, tabs, loop, objNames)
                case _:
                    self.__error('invalid identifier in "property" statement body', next)
    
    def __property(self, tokens : Tokens, tabs, loop, objNames):
        kw = tokens.last()

        if self.nextUnchecked:
            self.nextUnchecked = False
            self.__error(f'"unchecked" flag is not effective on "property" statement', kw)

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error(f'"abstract" flag is not effective on "property" statement', kw)

        if self.nextInline:
            self.nextInline = False
            self.__error(f'"inline" flag is not effective on "property" statement', kw)

        if self.nextGlobal:
            self.nextGlobal = False
            self.__error(f'"global" flag is not effective on "property" statement', kw)

        if self.nextCdef:
            self.nextCdef = False
            self.__error('$cdef is not effective on "property" statement', kw)

        _, value = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)

        if len(value) > 1:
            self.__error('property name should contain only one token', value[0])
        
        self.newObj(objNames, value[0], "dynamic")

        if len(block) == 0:
            return loop, objNames
        
        self.out += (" " * tabs) + Tokens([value[0], Token("="), Token("property()")]).join() + "\n"

        self.__nameStack.push((value[0].tok, "property"))
        
        if self.nextStatic:
            self.nextStatic = False

            backStatic = self.static
            self.static = True
            self.__propertyLoop(Tokens(block), tabs, loop, objNames, value[0])
            self.static = backStatic
        else:
            self.__propertyLoop(Tokens(block), tabs, loop, objNames, value[0])        
        
        self.__nameStack.pop()

        return loop, objNames
    
    def __getInlineIncDec(self, variablesDef):
        i = 0
        while i < len(variablesDef):
            if   variablesDef[i].tok == "++":
                 variablesDef[i].tok = "+="
            elif variablesDef[i].tok == "--":
                 variablesDef[i].tok = "-="
            else:
                i += 1 
                continue

            if i + 1 < len(variablesDef):
                  variablesDef.insert(i + 1, Token("1"))
            else: variablesDef.append(Token("1"))

            i += 2

        return variablesDef
    
    def __handleAssignmentChain(self, tabs, objNames, variablesDef, saveObjs = True):
        buf  = ""
        objs = []

        if len(variablesDef) != 0:
            variablesDef = Tokens(self.__getInlineIncDec(variablesDef))
                    
            next = variablesDef.next()

            while True:
                name = next
                next = variablesDef.peek()

                if next is None or next.tok in SET_OPS + (",", ):
                    if saveObjs: 
                        self.newObj(objNames, name, "dynamic")
                    else:
                        objs += [name, Token(",")]

                    if next is None: break
                    else: variablesDef.next()
                else:
                    backPos = variablesDef.pos - 1
                    next, name = self.getUntilNotInExpr(",", variablesDef, True, False, False, SET_OPS)

                    if next == "":
                        variablesDef.pos = backPos
                        nameBuf = []
                        while variablesDef.isntFinished():
                            next = variablesDef.next()

                            if next.tok in SET_OPS:
                                break

                            nameBuf.append(next)

                        name = Token(Tokens(nameBuf).join())

                if not variablesDef.isntFinished(): break
                            
                if   next.tok in SET_OPS:
                    op = next.tok
                    next, value = self.getUntilNotInExpr(",", variablesDef, True, False)
                    value = Tokens(value).join()

                    buf += (" " * tabs) + name.tok + op + value + "\n"
                elif next.tok == ",": 
                    next = variablesDef.next()
                else:
                    self.__error('invalid syntax: expecting "," or any assignment operator', next) 

                if next == "": break

        if saveObjs: return objNames, buf
        else:        return objs[:-1], buf 
    
    def __for(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        self.__flagsError("for", keyw)
        cnt = [x.tok for x in self.getUntilNotInExpr("{", tokens.copy(), True)[1]].count(";")

        match cnt:
            case 2: # C-like for
                rndBracks = tokens.peek().tok == "("
                if rndBracks: tokens.next()

                if tokens.peek().tok == ";": tokens.next()
                else:
                    _, variablesDef = self.getUntilNotInExpr(";", tokens, True, advance = False)
                    objNames, buf = self.__handleAssignmentChain(tabs, objNames, variablesDef)
                    self.out += buf

                if tokens.peek().tok == ";": 
                    tokens.next()
                    condition = [Token("True")]
                else:
                    _, condition = self.getUntilNotInExpr(";", tokens, True, advance = False)
                    if len(condition) == 0: condition = [Token("True")]

                if tokens.peek().tok == "{":
                    tokens.next()
                    increments = ""
                else:
                    if rndBracks:
                        _, increments = self.getUntilNotInExpr(")", tokens, True, advance = False)
                        self.checkDirectNext("{", "for loop", tokens)
                    else:
                        _, increments = self.getUntilNotInExpr("{", tokens, True, advance = False)

                    objNames, increments = self.__handleAssignmentChain(tabs + 1, objNames, increments)

                statement = [Token("while")] + condition
            case 0: # Python for
                _, variablesDef = self.getUntilNotInExpr("in", tokens, True, advance = False)
                variablesDef = Tokens(variablesDef)

                if len(variablesDef.tokens) != 0:
                    while variablesDef.isntFinished():
                        name = variablesDef.next()
                        self.newObj(objNames, name, "dynamic")

                        next = variablesDef.peek()
                        if next is None: break

                        if next.tok != ",":
                            self.__error('invalid syntax: expecting "," after variable name in a for loop', next)
                        else: variablesDef.next()

                _, iterable = self.getUntilNotInExpr("{", tokens, True, advance = False)
                statement  = [Token("for")] + variablesDef.tokens + [Token("in")] + iterable
                increments = ""
            case _:
                self.__error('invalid syntax: using an unrecognized amount of semicolons in a for loop', keyw)
                return loop, objNames
            
        block = self.getSameLevelParenthesis("{", "}", tokens)

        self.out += (" " * tabs) + Tokens(statement).join() + ":"

        if len(block) == 0:
            if increments == "": self.out += "pass\n"
            else:                self.out += "\n" + increments

            return loop, objNames
        
        self.out += "\n"
        
        _, objNames = self.__compiler(Tokens(block), tabs + 1, CompLoop(increments.lstrip()), objNames)

        if increments != "": self.out += increments
            
        return loop, objNames
    
    def __enum(self, tokens : Tokens, tabs, loop, objNames):
        if self.nextUnchecked:
            self.nextUnchecked = False
            self.__error(f'"unchecked" flag is not effective on "enum" statement', tokens.last())

        if self.nextStatic:
            self.nextStatic = False
            self.__error(f'"static" flag is not effective on "enum" statement', tokens.last())

        if self.nextAbstract:
            self.nextAbstract = False
            self.__error(f'"abstract" flag is not effective on "enum" statement', tokens.last())

        if self.nextInline:
            self.nextInline = False
            self.__error(f'"inline" flag is not effective on "enum" statement', tokens.last())

        if self.nextCdef:
            self.nextCdef = False
            self.__error(f'$cdef is not effective on "enum" statement', tokens.last())

        _, value = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)

        if len(value) == 0:
            if len(block) == 0:
                return loop, objNames
            
            inTabs = tabs
        else:
            if len(value) > 1:
                self.__error('enum name should contain only one token', value[0])

            if not self.flags["enum"]:
                self.flags["enum"] = True
                self.out = "from enum import IntEnum\n" + self.out

            self.out += (" " * tabs) + Tokens([Token("class"), value[0], Token("(IntEnum)")]).join() + ":"

            if len(block) == 0:
                self.out += "pass\n"
                return loop, objNames
            
            self.out += "\n"

            self.newObj(objNames, value[0], "dynamic")

            inTabs = tabs + 1

        objs, assignments = self.__handleAssignmentChain(inTabs, objNames, block, False)
        self.out += (" " * inTabs) + Tokens(objs).join() + f"=range({str(len([x for x in objs if x.tok != ',']))})\n" + assignments

        if self.nextGlobal:
            self.nextGlobal = False
            self.out += (" " * tabs) + f"globals()['{value[0].tok}']={value[0].tok}\n"
        
        return loop, objNames
    
    def __dynamicStepOne(self, tokens : Tokens, tabs, objNames):
        _, expr = self.getUntilNotInExpr(";", tokens, True, advance = False)
        expr = Tokens(self.__getInlineIncDec(expr))

        names = []
        while expr.isntFinished():
            backPos = expr.pos
            next, name = self.getUntilNotInExpr(",", expr, True, False, False, SET_OPS)

            if next == "":
                expr.pos = backPos
                buf = []
                while expr.isntFinished():
                    next = expr.next()

                    if next.tok in SET_OPS:
                        break

                    buf.append(next)

                names.append(Tokens(buf).join())
                break
                
            names.append(Tokens(name).join())

        if self.nextUnchecked:
            self.nextUnchecked = False
            self.out += (" " * tabs) + expr.join() + "\n"
            
            for name in names:
                if name in objNames and objNames[name] == "auto" and name in self.autoTypes:
                    del self.autoTypes[name]

            return None, None
        
        return names, expr
    
    def __init__(self):
        self.reset()

        self.preConsts   = {}
        self.__nameStack = NameStack()

        self.static      = False
        self.__cy        = False
        self.noCompile   = False
        self.compileOnly = False
        self.notes       = True
        self.module      = False
        self.typeMode    = "hybrid"

        self.statementHandlers = {
            "new":                 self.__new,
            "property":            self.__property,
            "get":                 self.__modifier("getter"), 
            "set":                 self.__modifier("setter"),
            "delete":              self.__modifier("deleter"),
            "namespace":           self.__namespace,
            "package":             self.__package,
            "import":              self.__import,
            "async":               self.__asyncGen("async"),
            "await":               self.__asyncGen("await"),
            "use":                 self.__use,
            "unchecked":           self.__unchecked,
            "return":              self.__return,
            "break":               self.__break,
            "continue":            self.__continue,
            "@":                   self.__untilEnd("@"),
            "throw":               self.__untilEnd("raise"),
            "super":               self.__untilEnd("super"),
            "del":                 self.__untilEnd("del"),
            "assert":              self.__untilEnd("assert"),
            "yield":               self.__untilEnd("yield"),
            "external":            self.__untilEnd("nonlocal"),
            "global":              self.__global,
            "_OPAL_PRINT_RETURN_": self.__printReturn,
            "not":                 self.__not,
            "++":                  self.__incDec("+"),
            "--":                  self.__incDec("-"),
            "main":                self.__main,
            "try":                 self.__simpleBlock("try", "try"),
            "catch":               self.__block("except"),
            "success":             self.__simpleBlock("else", "success"),
            "else":                self.__simpleBlock("else", "else", (None, "conditional")),
            "if":                  self.__block("if", push = (None, "conditional")),
            "elif":                self.__block("elif", push = (None, "conditional")),
            "while":               self.__block("while", GenericLoop()),
            "with":                self.__block("with"),
            "do":                  self.__do,
            "for":                 self.__for,
            "repeat":              self.__repeat,
            "match":               self.__match,
            "enum":                self.__enum,
            "abstract":            self.__abstract,
            "ignore":              self.__ignore,
            "static":              self.__static,
            "inline":              self.__inline
        }

    def initMain(self):
        self.comptimeCompiler = Compiler()
        return self

    def __lineWarn(self, msg, line):
        print(f"warning (line {str(line + 1)}):", msg)

    def __lineErr(self, msg, line):
        self.hadError = True
        print(f"error (line {str(line + 1)}):", msg)

    def __error(self, msg, token : Token):
        self.hadError = True
        token.error(msg, self.__nameStack.getCurrentLocation())

    def __warning(self, msg, token : Token):
        token.warning(msg, self.__nameStack.getCurrentLocation())

    def __note(self, msg, token : Token):
        if self.notes: token.note(msg, self.__nameStack.getCurrentLocation())

    def __resetFlags(self):
        self.flags = {
            "abstract":          False,
            "mainfn":            False,
            "OPAL_PRINT_RETURN": False,
            "namespace":         False,
            "object":            False,
            "enum":              False
        }

    def newObj(self, objNames, nameToken : Token, type_):
        if not nameToken.tok.isidentifier():
            self.__error(f'invalid identifier name "{nameToken.tok}"', nameToken)
            return

        if type_ == "auto" and nameToken.tok in self.autoTypes:
            del self.autoTypes[nameToken.tok]

        if self.typeMode == "none":
              objNames[nameToken.tok] = "dynamic"
        else: objNames[nameToken.tok] = type_

    def checkDirectNext(self, ch, msg, tokens : Tokens):
        next = tokens.next()
        if next.tok != ch:
            self.__error(f'invalid syntax: expecting "{ch}" directly after {msg}', next)
            next = self.getUntil(ch, tokens)

        return next
    
    def getUntil(self, ch, tokens : Tokens, buffer = False):
        buf = []
        while tokens.isntFinished():
            next = tokens.next()

            if next.tok == "\\":
                tokens.next()
                continue

            if next.tok == ch:
                if buffer: return next, buf
                else:      return next

            buf.append(next)

        self.__error(f'expecting character "{ch}"', next)

        if buffer: return "", buf
        else:      return ""
    
    def getUntilNotInExpr(self, ch, tokens : Tokens, buffer = False, errorNotFound = True, advance = True, unallowed = []):
        if type(ch) is str:
            ch = (ch, )

        rdBrack = 0
        sqBrack = 0
        crBrack = 0
        lastRdBrack = tokens.peek()
        lastSqBrack = tokens.peek()
        lastCrBrack = tokens.peek()
        next = tokens.peek()

        buf = []
        while tokens.isntFinished():
            next = tokens.next()

            match next.tok:
                case "(":
                    lastRdBrack = next
                    rdBrack += 1
                case ")":
                    lastRdBrack = next
                    rdBrack -= 1
                case "[":
                    lastSqBrack = next
                    sqBrack += 1
                case "]":
                    lastSqBrack = next
                    sqBrack -= 1
                case "{":
                    if "{" not in ch:
                        lastCrBrack = next
                        crBrack += 1
                case "}":
                    if "{" not in ch:
                        lastCrBrack = next
                        crBrack -= 1
                case "\\":
                    if tokens.isntFinished():
                        next = tokens.next()
                    else:
                        self.__error("cannot escape here", next)

                        if buffer: return next, buf
                        else:      return next

                    continue

            if next.tok in unallowed:
                if advance and tokens.isntFinished():
                    next = tokens.next()

                if buffer: return "", buf
                else:      return ""

            if rdBrack == 0 and sqBrack == 0 and crBrack == 0:
                if next.tok in ch:
                    if advance and tokens.isntFinished():
                        next = tokens.next()

                    if buffer: return next, buf
                    else:      return next
                
            buf.append(next)
                
        if rdBrack != 0:
            if lastRdBrack is None:
                self.__error("unbalanced brackets ()", tokens.tokens[-1])
            else:
                self.__error("unbalanced brackets ()", lastRdBrack)
            
        if sqBrack != 0:
            if lastSqBrack is None:
                self.__error("unbalanced brackets []", tokens.tokens[-1])
            else:
                self.__error("unbalanced brackets []", lastSqBrack)

        if crBrack != 0:
            if lastCrBrack is None:
                self.__error("unbalanced brackets {}", tokens.tokens[-1])
            else:
                self.__error("unbalanced brackets {}", lastCrBrack)

        if errorNotFound:
            if next is None:
                self.__error(f'expecting character(s) {ch}', Token(""))
            else:
                self.__error(f'expecting character(s) {ch}', next)

        if buffer: return "", buf
        else:      return ""

    def getSameLevelParenthesis(self, openCh, closeCh, tokens : Tokens):
        pCount = 1
        buf = []
        lastParen = tokens.peek()
        if lastParen is None:
            self.__error('unbalanced parenthesis "' + openCh + closeCh + '"', tokens.tokens[-1])
            return []

        while tokens.isntFinished():
            next = tokens.next()

            if   next.tok == openCh:
                lastParen = next
                pCount += 1
            elif next.tok == closeCh:
                lastParen = next
                pCount -= 1

            if pCount == 0:
                return buf
            
            buf.append(next)

        self.__error('unbalanced parenthesis "' + openCh + closeCh + '"', lastParen)
        return buf
    
    def __variablesHandler(self, tokens : Tokens, tabs, objNames, autoCheck = True):
        names, expr = self.__dynamicStepOne(tokens, tabs, objNames)
        if names is None: return

        for name in names:
            if autoCheck and name in objNames and objNames[name] == "auto" and name not in self.autoTypes:
                self.out += (" " * tabs) + f"_OPAL_AUTOMATIC_TYPE_{name}=type({name})\n"
                self.autoTypes[name] = None

        self.out += (" " * tabs) + expr.join() + "\n"

        for name in names:
            if name in objNames and objNames[name] != "dynamic":
                if objNames[name] == "auto":
                    if autoCheck:
                        self.out += (" " * tabs) + f"{name}=_OPAL_CHECK_TYPE_({name},_OPAL_AUTOMATIC_TYPE_{name})\n"
                else:
                    self.out += (" " * tabs) + f"{name}=_OPAL_CHECK_TYPE_({name},{objNames[name]})\n"
    
    def __compiler(self, tokens : Tokens, tabs, loop, objNames):  
        while tokens.isntFinished():
            next = tokens.next()

            if next.tok.startswith('"""') or next.tok.startswith("'''"):
                self.out += next.tok + "\n"
                continue

            if   next.tok in self.statementHandlers:
                loop, objNames = self.statementHandlers[next.tok](tokens, tabs, loop, objNames)
            elif next.tok in objNames:
                tokens.pos -= 1
                self.__variablesHandler(tokens, tabs, objNames)
            elif next.tok == "__OPALSIG":
                kw = tokens.last()

                if self.__manualSig:
                    self.__warning('"__OPALSIG" is meant for internal use. please do not use it in production', next)

                next = tokens.next()
                if next.tok != "[":
                    self.__error('invalid syntax: expecting "[" after "__OPALSIG"', next)

                signal = Tokens(self.getSameLevelParenthesis("[", "]", tokens)).join()

                next = tokens.next()
                if next.tok != "(":
                    self.__error(f'invalid syntax: expecting "(" after "__OPALSIG[{signal}]"', next)

                args = Tokens(self.getSameLevelParenthesis("(", ")", tokens)).join()

                match signal:
                    case "EMBED_INFER":
                        try:
                            args = int(args)
                        except:
                            self.__error(f'expecting an integer for "{signal}" signal', kw)
                            args = 0
                        
                        next = tokens.peek()
                        if next.tok != ".":
                            self.__error(f'invalid syntax: expecting "." after "__OPALSIG[{signal}]({args})"', next)
                        else: tokens.next()

                        _, code = self.getUntil(";", tokens, True)

                        self.out += (" " * (args + tabs)) + Tokens(code).join() + "\n"
                    case "PUSH_NAME":
                        try:
                            self.__nameStack.push(eval(f"({args})"))
                        except:
                            self.__error('invalid arguments for "PUSH_NAME" signal', kw)
                    case "POP_NAME":
                        self.__nameStack.pop()
                    case "TABS_ADD":
                        try:
                            args = int(args)
                        except:
                            self.__error(f'expecting an integer for "{signal}" signal', kw)
                            args = 0

                        tabs += args
                    case "CDEF":
                        self.nextCdef = True
            else:
                first  = next
                if next.tok == "(":
                    type_ = Tokens(self.getSameLevelParenthesis("(", ")", tokens)).join()
                else:
                    type_ = next.tok
                        
                next = tokens.next()
                if next is None or next.tok != "<-":
                    self.__error('unknown statement or identifier', first)
                    continue

                names, _ = self.__dynamicStepOne(tokens.copy(), tabs, objNames)
                if names is None: 
                    self.__warning("cannot find any variables to convert. it is recommended to remove the type conversion", next)
                    continue

                for name in names:
                    if name in objNames:
                        objNames[name] = type_

                        if   type_ == "auto":
                            del self.autoTypes[name]
                        elif type_ != "dynamic":
                            self.out += (" " * tabs) + name + ":" + type_ + "\n"

                self.__variablesHandler(tokens, tabs, objNames, False)

        return loop, objNames

    def replaceConsts(self, expr, consts):
        res = ""
        for line in expr.split("\n"):
            expr  = Tokens(line)
            found = False
            for i in range(len(expr.tokens)):
                if expr.tokens[i].tok in consts:
                    found = True
                    expr.tokens[i].tok = consts[expr.tokens[i].tok]

            if found:
                  res += expr.join() + "\n"
            else: res += line + "\n"

        return res

    def getDir(self, expr):
        return eval(self.replaceConsts(expr.strip(), self.preConsts | self.consts))

    def readFile(self, fileName, rep = False):
        with open(fileName, "r") as txt:
            content = txt.read()
        return content.replace("\t", " " if rep else "")

    def __readEmbed(self, fileDir):
        self.__manualSig = False

        result = ""
        for line in self.readFile(fileDir).split("\n"):
            strippedLine = line.lstrip()
            tabs = len(line) - len(strippedLine)
            result += f"__OPALSIG[EMBED_INFER]({tabs})." + strippedLine.rstrip() + ";\n"

        return result
    
    def __include(self, result, file):
        self.__manualSig = False
        result += f'__OPALSIG[PUSH_NAME]("{os.path.basename(file)}","file")\n'
        if file.endswith(".py") or file.endswith(".pyx"):
            result += self.__readEmbed(file)
        else:
            result += self.__preCompiler(self.readFile(file)) + "\n"
        return result + "__OPALSIG[POP_NAME]()\n"

    def __preCompiler(self, source):
        result = ""
        savingMacro = None
        compTime = None
        export = None
        inPy = False

        for i, line in enumerate(source.split("\n")):
            noSpaceLine = line.replace(" ", "")
            if noSpaceLine == "": 
                result += "\n"
                continue

            if noSpaceLine[0] != "$":
                if inPy:
                    self.__manualSig = False

                    strippedLine = line.lstrip()
                    tabs = len(line) - len(strippedLine)
                    line = f"__OPALSIG[EMBED_INFER]({tabs})." + strippedLine.rstrip() + ";\n"

                if savingMacro is None and compTime is None and export is None:
                    result += line + "\n"
                else:
                    result += "\n" 

                    if savingMacro is not None:
                        savingMacro.add(line + "\n")
                    elif export is not None:
                        export += line + "\n"
                    else:
                        compTime += line + "\n"

                continue

            result += "\n"

            tokenizedLine = Tokens(line)
            tokenizedLine.next()

            next = tokenizedLine.next()
            match next.tok:
                case "include":
                    self.__manualSig = False
                        
                    fileDir = self.getDir(Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join())
                        
                    result += f'__OPALSIG[PUSH_NAME]("{os.path.basename(fileDir)}","file")\n'
                    pyx = fileDir.endswith(".pyx")
                    if fileDir.endswith(".py") or pyx:
                        if pyx and not self.__cy: continue
                        result += self.__readEmbed(fileDir)
                    else:
                        result += self.__preCompiler(self.readFile(fileDir))
                    result += "__OPALSIG[POP_NAME]()\n"
                case "includeDirectory":
                    fileDir = self.getDir(Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join())

                    for file in [os.path.join(fileDir, f) for f in os.listdir(fileDir) if f.endswith(".opal") or f.endswith(".py") or (self.__cy and f.endswith(".pyx"))]:
                        result = self.__include(result, file)
                case "define":
                    name    = tokenizedLine.next().tok
                    content = Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()
                        
                    self.consts[name] = content
                case "pdefine":
                    name    = tokenizedLine.next().tok
                    content = Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()

                    self.preConsts[name] = content
                case "macro":
                    if savingMacro is not None:
                        self.__lineErr("found recursive macro definition", i)
                        continue

                    name = tokenizedLine.next().tok

                    next = tokenizedLine.peek()
                    if next is not None and next.tok == "(":
                        tokenizedLine.next()
                        args = self.getSameLevelParenthesis("(", ")", tokenizedLine)

                        if len(args) != 0:
                            savingMacro = Macro(name, Tokens(args).join())
                            continue
            
                    savingMacro = Macro(name)
                case "comptime":
                    if compTime is not None:
                        self.__lineErr("cannot use comptime block inside another comptime block", i)
                        continue

                    compTime = ""
                case "export":
                    if compTime is None:
                        self.__lineErr("cannot use $export outside of a comptime block", i)
                        continue

                    compTime += 'return "' + encode(Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()) + '";\n'
                case "exportBlock":
                    if compTime is None:
                        self.__lineErr("cannot use $exportBlock outside of a comptime block", i)
                        continue

                    export = ""
                case "end":
                    if savingMacro is None and compTime is None and export is None:
                        self.__lineErr("$end found with no macro definition, comptime block or export block", i)
                        continue

                    if savingMacro is not None:
                        if savingMacro.code == "":
                            self.__lineWarn(f'the "{savingMacro.name}" macro is being saved as empty', i)
                            
                        self.macros[savingMacro.name] = savingMacro
                        savingMacro = None        
                    elif export is not None:
                        if export == "":
                            self.__lineWarn("empty export block", i)
                            continue

                        compTime += 'return "' + encode(self.replaceConsts(export.strip(), self.preConsts | self.consts)) + '";\n'
                        export = None
                    else:
                        if compTime == "":
                            self.__lineWarn("empty comptime block", i)
                            continue

                        res = self.comptimeCompiler.compile(
                            "global:new function _OPAL_COMPTIME_BLOCK_(){\n" + 
                            self.replaceConsts(compTime.strip(), self.preConsts | self.consts) + 
                            "}\n", precomp = False
                        )
                        compTime = None
                        if res == "":
                            self.hadError = True
                            continue

                        try:
                            exec(res)
                            exportCode = eval("_OPAL_COMPTIME_BLOCK_()")
                        except Exception as e:
                            self.__lineErr("comptime block threw an exception:\n" + ''.join(format_exception(e)), i)
                        else:
                            if exportCode is not None:
                                result += str(exportCode) + "\n" 
                case "call":
                    name = tokenizedLine.next().tok

                    if name not in self.macros:
                        self.__lineErr(f'trying to call undefined macro "{name}"', i)
                        continue

                    macro = self.macros[name]

                    self.__manualSig = False
                    buf = f'__OPALSIG[PUSH_NAME]("{name}","macro")\n'
                    next = tokenizedLine.peek()
                    if next is not None and next.tok == "(":
                        tokenizedLine.next()
                        args = self.getSameLevelParenthesis("(", ")", tokenizedLine)

                        if len(args) != 0:
                            if macro.args == args:
                                buf += f"new dynamic {macro.args};"
                            else:
                                buf += f"new dynamic {macro.args};{macro.args}={Tokens(args).join()};"
                                
                    buf += macro.code
                    buf += "__OPALSIG[POP_NAME]()\n"
                    
                    if savingMacro is None:
                        result += buf
                    else:
                        savingMacro.add(buf)
                case "nocompile":
                    inPy = True
                case "restore":
                    inPy = False
                case "args":
                    self.handleArgs(eval(Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()))
                case "cy":
                    if not self.__cy: continue

                    arg = tokenizedLine.next().tok
                    val = tokenizedLine.next().tok

                    result += "@cython." + arg + f"({val});\n"
                case "tabcontext":
                    qty = Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()
                    self.__manualSig = False

                    buf = f"__OPALSIG[TABS_ADD]({qty})\n"

                    if savingMacro is None:
                        result += buf
                    else:
                        savingMacro.add(buf)
                case "embed":
                    self.__manualSig = False

                    buf = f"__OPALSIG[EMBED_INFER](0)." + Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join() + ";\n"

                    if savingMacro is None:
                        result += buf
                    else:
                        savingMacro.add(buf)
                case "cdef":
                    self.__manualSig = False

                    if savingMacro is None:
                        result += "__OPALSIG[CDEF]()\n"
                    else:
                        savingMacro.add("__OPALSIG[CDEF]()\n")
                case _:
                    self.__lineErr("unknown or incomplete precompiler instruction", i)

        return self.replaceConsts(result, self.consts)
    
    def reset(self):
        self.macros    = {}
        self.consts    = {}
        self.autoTypes = {}
        self.imports   = []

        self.out      = ""
        self.hadError = False

        self.__manualSig   = True
        self.nextAbstract  = False
        self.nextUnchecked = False
        self.nextStatic    = False
        self.nextInline    = False
        self.nextCdef      = False
        self.nextGlobal    = False
        self.lastPackage   = ""

        self.__resetFlags()

    def compile(self, section, top = None, precomp = True):
        self.reset()

        if top is not None:
            self.out += top + "\n"

        match self.typeMode:
            case "hybrid":
                self.out += "from libs._internals import _OPAL_CHECK_TYPE_\n"
            case "check":
                self.out += "from typeguard import check_type as _OPAL_CHECK_TYPE_\n"
            case "force":
                self.out += "from libs._internals import _OPAL_FORCE_TYPE_ as _OPAL_CHECK_TYPE_\n"

        if len(self.__nameStack.array) == 0:
            self.__nameStack.push(("<main>", "file"))

        if precomp: section = self.__preCompiler(section)
        self.tokens = Tokens(section)

        if self.__cy:
            if self.noCompile:
                print('This program cannot be compiled. Use the "pycompile" command or run it directly.')
                quit()
        else:
            if self.compileOnly:
                print('This program cannot be ran directly or compiled in Python mode. Use the "pyxcompile" or "compile" commands.')
                quit()

        if "_OPAL_PRINT_RETURN_" in [x.tok for x in self.tokens.tokens]:
            self.flags["OPAL_PRINT_RETURN"] = True
            self.out += "from libs._internals import _OPAL_PRINT_RETURN_\n"

        self.__compiler(self.tokens, 0, None, {})
        self.imports = list(set(self.imports))

        if self.flags["mainfn"]:
            if self.__cy:
                self.out += 'if"_OPAL_RUN_AS_MAIN_"in _ENVIRON_:_OPAL_MAIN_FUNCTION_()\n'
            else:
                self.out += 'if __name__=="__main__":_OPAL_MAIN_FUNCTION_()\n'

        if self.hadError: return ""
        else:             return self.out

    def compileFile(self, fileIn, top = "", pyTop = None):
        self.__nameStack.push((fileIn, "file"))
        return self.compile(top + "\n" + self.readFile(fileIn), pyTop)

    def __compileWrite(self, fileIn, fileOut, top, pyTop = None):
        result = self.compileFile(fileIn, top, pyTop)

        if result != "":
            with open(fileOut, "w") as txt:
                txt.write(result)
    
    def compileToPY(self, fileIn, fileOut, top = ""):
        self.__cy = False
        self.__compileWrite(fileIn, fileOut, top)

    def compileToPYX(self, fileIn, fileOut, top = ""):
        self.__cy = True
        self.__compileWrite(fileIn, fileOut, top, "cimport cython\nfrom os import environ as _ENVIRON_")

    def handleArgs(self, args: list):
        if "--static" in args:
            self.static = True
            args.remove("--static")

        if "--disable-notes" in args:
            self.notes = False
            args.remove("--disable-notes")

        if "--require" in args:
            idx = args.index("--require")
            args.pop(idx)

            version = tuple([int(x) for x in args.pop(idx).split(".")])
            if VERSION < version:
                print(f'This program requires opal v{".".join([str(x) for x in version])} or newer, but an older version is installed ({".".join([str(x) for x in VERSION])})')
                quit()

        if "--nostatic" in args:
            args.remove("--nostatic")

            if self.static:
                print('This program cannot be compiled with the "--static" flag.')
                quit()

        if "--nocompile" in args:
            args.remove("--nocompile")
            self.noCompile = True

        if "--compile-only" in args:
            args.remove("--compile-only")
            self.compileOnly = True

        if "--module" in args:
            args.remove("--module")
            self.module = True

        if "--type-mode" in args:
            idx = args.index("--type-mode")
            args.pop(idx)

            mode = args.pop(idx).lower()
            if mode in ("hybrid", "check", "force", "none"):
                self.typeMode = mode
            else:
                print(f'invalid type mode "{mode}". supported types are hybrid, check, force, none')