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

import re, os, sys, py_compile
from importlib import import_module
from timeit    import default_timer
from pathlib   import Path

SET_OPS = ("+=", "-=", "**=", "//=", "*=", "/=", "%=", "&=", "|=", "^=", ">>=", "<<=", "=")

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

class Token:
    def __init__(self, tok, line = 0, pos = 0, tokens = None):
        self.tok  : str = tok
        self.line : int = line
        self.pos  : int = pos

        self.tokens : Tokens = tokens

    def error(self, msg):
        if self.tokens is None: print(f"error:", msg)
        else:
            strippedText = self.tokens.source[self.line - 1].lstrip()
            diff = len(self.tokens.source[self.line - 1]) - len(strippedText)
            print(
                f"error (line {self.line - 1}):", msg, "\n  " + 
                strippedText.rstrip() + "\n" + 
                (" " * (self.pos - diff + 2)) + ("^" * len(self.tok))
            )

    def warning(self, msg):
        strippedText = self.tokens.source[self.line - 1].lstrip()
        diff = len(self.tokens.source[self.line - 1]) - len(strippedText)
        print(
            f"warning (line {self.line - 1}):", msg, "\n  " + 
            strippedText.rstrip() + "\n" + 
            (" " * (self.pos - diff + 2)) + ("^" * len(self.tok))
        )

class Tokens:
    def __init__(self, source):
        if   type(source) is str:
            self.tokens = self.tokenize(source)
            self.source = source.split("\n")
        elif type(source) is list:
            self.tokens = source
            self.source = []

        self.pos = 0

    def copy(self):
        tmp = Tokens(self.tokens)
        tmp.pos    = self.pos
        tmp.source = self.source

        return tmp

    def isntFinished(self):
        return self.pos < len(self.tokens)

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]

    def next(self) -> Token:
        if self.pos < len(self.tokens):
            tmp = self.tokens[self.pos]
            self.pos += 1
            return tmp
        
        self.tokens[self.pos - 1].error("invalid syntax: the expression wasn't properly closed. no tokens remaining")
    
    def last(self) -> Token:
        return self.tokens[self.pos - 1]
    
    @classmethod
    def replaceTokens(self, tokens):
        i = 0
        while i < len(tokens):
            match tokens[i].tok:
                case "||":
                    tokens[i].tok = "or"
                case "&&":
                    tokens[i].tok = "and"
                case "!":
                    tokens[i].tok = "not"
                case "?":
                    tokens[i].tok = "_OPAL_PRINT_RETURN_"
                case "super":
                    if i + 1 < len(tokens) and tokens[i + 1].tok != "(":
                        tokens.insert(i + 1, Token("()"))
                        i += 1
            i += 1

        return tokens

    @classmethod
    def verifyTok(self, tokens : list, first : Token, next : Token, opts):
        if next.tok in opts:
            first.tok += next.tok
            tokens.append(first)
            return True
        
        tokens.append(first)
        return False
    
    def join(self):
        buf = ""
        lastIsIdentifier = False
        lastIdentifier   = None
        for token in self.tokens:
            if token.tok.isidentifier():
                if lastIsIdentifier:
                    buf += " " + token.tok
                    lastIdentifier = token.tok
                    continue

                lastIsIdentifier = True
            else:
                lastIsIdentifier = token.tok.isdigit()

                if lastIdentifier is not None and (lastIdentifier + token.tok).isidentifier():
                    buf += " " + token.tok
                    lastIdentifier = token.tok
                    continue

            lastIdentifier = token.tok
            buf += token.tok

        return buf

    def tokenize(self, source):
        line = 1
        pos  = 0
        tmp         = [Token("", line, pos, self)]
        inString    = False
        inStringAlt = False
        lastSym     = False
        
        for ch in source:
            match ch:
                case " ":
                    if inString or inStringAlt: tmp[-1].tok += ch
                    else:        
                        tmp.append(Token("", line, pos + 1, self))
                case "\n":
                    if inString or inStringAlt: tmp[-1].tok += ch
                    else:
                        line += 1
                        pos = 0
                        tmp.append(Token("", line, pos, self))
                        continue
                case '"':
                    if inString:
                        tmp[-1].tok += ch
                        inString = False
                    elif inStringAlt:
                        tmp[-1].tok += ch
                    else:
                        tmp.append(Token(ch, line, pos, self))
                        inString = True
                case "'":
                    if inStringAlt:
                        tmp[-1].tok += ch
                        inStringAlt = False
                    elif inString:
                        tmp[-1].tok += ch
                    else:
                        tmp.append(Token(ch, line, pos, self))
                        inStringAlt = True
                case _:
                    if inString or inStringAlt:
                        tmp[-1].tok += ch
                    elif ch.isalnum() or ch == "_":
                        if lastSym:
                            lastSym = False
                            tmp.append(Token(ch, line, pos, self))
                        else:
                            tmp[-1].tok += ch
                    else:                            
                        lastSym = True
                        tmp.append(Token(ch, line, pos, self))

            pos += 1

        i = 0
        while i < len(tmp):
            if tmp[i].tok == "":
                tmp.pop(i)
            else: i += 1

        tokens = []
        i = 0
        while i < len(tmp) - 1:
            token = tmp[i]
            i += 1

            match token.tok:
                case "+":
                    if self.verifyTok(tokens, token, tmp[i], ("+", "=")): i += 1
                    continue
                case "-":
                    if self.verifyTok(tokens, token, tmp[i], ("-", "=")): i += 1
                    continue
                case "!":
                    if self.verifyTok(tokens, token, tmp[i], ("=",)): i += 1
                    continue
                case "|":
                    if self.verifyTok(tokens, token, tmp[i], ("|", "=")): i += 1
                    continue
                case "&":
                    if self.verifyTok(tokens, token, tmp[i], ("&", "=")): i += 1
                    continue
                case "f" | "r" | "b" | "fr" | "br" | "rf" | "rb":
                    if tmp[i].tok.startswith('"') or tmp[i].tok.startswith("'"):
                        token.tok += tmp[i].tok
                        i += 1
                case ":" | "^" | "%" | "=":
                    if tmp[i].tok == "=":
                        token.tok += tmp[i].tok
                        i += 1
                case "*":
                    if tmp[i].tok in ("*", "="):
                        if tmp[i].tok == "*":
                            next = tmp[i]
                            i += 1

                            if tmp[i].tok == "=":
                                token.tok += next.tok + tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case "/":
                    if tmp[i].tok in ("/", "="):
                        if tmp[i].tok == "/":
                            next = tmp[i]
                            i += 1

                            if tmp[i].tok == "=":
                                token.tok += next.tok + tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case ">":
                    if tmp[i].tok in (">", "="):
                        if tmp[i].tok == ">":
                            next = tmp[i]
                            i += 1

                            if tmp[i].tok == "=":
                                token.tok += next.tok + tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case "<":
                    if tmp[i].tok in ("<", "=", "-"):
                        if tmp[i].tok == "<":
                            next = tmp[i]
                            i += 1

                            if tmp[i].tok == "=":
                                token.tok += next.tok + tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case '""':
                    if tmp[i].tok.startswith('"'):
                        token.tok += tmp[i].tok
                        i += 1
                    elif len(tokens) > 0 and tokens[-1].tok.endswith('"'):
                        tokens[-1].tok += token.tok
                        continue
                case "''":
                    if tmp[i].tok.startswith("'"):
                        token.tok += tmp[i].tok
                        i += 1
                    elif len(tokens) > 0 and tokens[-1].tok.endswith("'"):
                        tokens[-1].tok += token.tok
                        continue

            tokens.append(token)

        if i < len(tmp):
            lastTok = tmp[len(tmp) - 1]

            match lastTok.tok:
                case '""':
                    if tokens[-1].tok.endswith('"'):
                        tokens[-1].tok += lastTok.tok
                case "''":
                    if tokens[-1].tok.endswith("'"):
                        tokens[-1].tok += lastTok.tok
                case _:
                    tokens.append(lastTok)

        return self.replaceTokens(tokens)
    
class TypeCheckMode:
    CHECK, FORCE, NOCHECK = 0, 1, 2

class Compiler:
    def __new(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.next()

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
                    self.__error("cannot create abstract record", next)
                    return loop, objNames

                translates = "class"
                isRecord = True
            case "class":
                translates = "class"
            case _:
                return self.__newVar(tokens, tabs, loop, objNames)

        name = tokens.next()

        if translates != "class" or isRecord:
            next = tokens.peek()
            if next.tok != "(":
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
                    if next.tok in ("**", "*"):
                        next = args.next()

                    argName = next.tok

                    if not args.isntFinished():
                        internalVars.append((argName, "dynamic"))
                        break
                    
                    next = args.peek()
                    if next is not None and next.tok == ":":
                        args.next()
                        next  = args.next()
                        type_ = next.tok
                    else:
                        type_ = "dynamic"

                    internalVars.append((argName, type_))

                    if not args.isntFinished(): break

                    next = args.peek()

                    if next.tok == "=":
                        args.next()
                        tmp = self.getUntilNotInExpr(",", args, advance = False, errorNotFound = False)
                        
                        if tmp == "": break
                        else:         next = tmp
                    else:
                        if next.tok != ",":
                            self.__error("invalid syntax: arguments should be separated by commas", next)
                        else:
                            next = args.next()

                    if next is None: break
                
            argsString = args.join()

            if self.nextAbstract:
                self.nextAbstract = False

                self.newObj(objNames, name, "untyped")

                next = self.checkDirectNext(";", "abstract object definition", tokens)

                self.out += (" " * tabs) + translates + " " + name.tok + f"({argsString}):pass\n"
                return loop, objNames
            
            if isRecord:
                self.newObj(objNames, name, "class")

                next = self.checkDirectNext(";", "record definition", tokens)

                self.out += (
                    (" " * tabs) + "class " + name.tok + ":\n" +
                    (" " * (tabs + 1)) + f"def __init__(this,{argsString}):\n"
                )

                for var in internalVars:
                    self.out += (" " * (tabs + 2)) + f"this.{var}={var}\n"

                return loop, objNames
            
            self.newObj(objNames, name, "untyped")
        
            next = self.checkDirectNext("{", "function definition", tokens)
        else:
            argsString = ""
            
            next = tokens.peek()
            if next.tok == ":":
                next = tokens.next()
                next, args = self.getUntil("{", tokens, True)
                argsString = Tokens(args).join()
                
                if self.nextAbstract:
                    self.nextAbstract = False
                    argsString += ",_ABSTRACT_BASE_CLASS_"
            else:
                next = self.checkDirectNext("{", "class definition", tokens)

                if self.nextAbstract:
                    self.nextAbstract = False
                    argsString = "_ABSTRACT_BASE_CLASS_"

            self.newObj(objNames, name, "class")

        if translates == "class" and argsString == "":
              self.out += (" " * tabs) + translates + " " + name.tok + ":"
        else: self.out += (" " * tabs) + translates + " " + name.tok + "(" + argsString + "):"

        block = self.getSameLevelParenthesis("{", "}", tokens)
        if len(block) == 0:
            self.out += "pass\n"
            return loop, objNames
        
        self.out += "\n"
        
        block = Tokens(block)
        
        if translates == "class":
            self.__compiler(block, tabs + 1, loop, objNames)
            return loop, objNames

        intObjs = objNames.copy()
        for var in internalVars:
            intObjs[var[0]] = (var[1], TypeCheckMode.NOCHECK if var[1] == "dynamic" else TypeCheckMode.CHECK)

        self.__compiler(block, tabs + 1, loop, intObjs)
        return loop, objNames
    
    def __newVar(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.last()

        if next.tok == "<":
            if not self.flags["OPAL_ASSERT_CLASSVAR"]:
                self.out = "from libs.std import _OPAL_ASSERT_CLASSVAR_TYPE_\n" + self.out
                self.flags["OPAL_ASSERT_CLASSVAR"] = True

            next = tokens.next()
            type_ = next.tok

            next = tokens.next()
            if next.tok != ">":
                next.warning("invalid syntax: type angular brackets should be closed. ignoring")
                next = tokens.next()

            mode = TypeCheckMode.CHECK
        else:
            type_ = next.tok

            if type_ == "dynamic":
                  mode = TypeCheckMode.NOCHECK
            else: mode = TypeCheckMode.FORCE

        _, variablesDef = self.getUntilNotInExpr(";", tokens, True, advance = False)
        variablesDef = Tokens(variablesDef)
        
        next = variablesDef.next()

        while True:
            name = next
            self.newObj(objNames, name, type_, mode)

            if not variablesDef.isntFinished(): 
                if type_ == "auto":
                    self.__error(f'auto-typed variables cannot be defined without being assigned', name) 

                break
                
            next = variablesDef.next()
            if   next.tok == "=":
                next, value = self.getUntilNotInExpr(",", variablesDef, True, False)
                value = Tokens(value).join()

                if mode == TypeCheckMode.CHECK:
                    self.out += (" " * tabs) + name.tok + f"=_OPAL_ASSERT_CLASSVAR_TYPE_({type_},{value})\n"
                elif type_ in ("auto", "dynamic"): 
                    self.out += (" " * tabs) + name.tok + "=" + value + "\n"
                else:
                    self.out += (" " * tabs) + name.tok + "=" + type_ + f"({value})\n"
            elif next.tok == ",": 
                next = variablesDef.next()

                if type_ == "auto":
                    self.__error(f'auto-typed variables cannot be defined without being assigned', name) 
            else:
                self.__error('invalid syntax: expecting "," or "="', next) 

            if next == "": break
        
        return loop, objNames
    
    def __not(self, tokens : Tokens, tabs, loop, objNames):
        _, var = self.getUntilNotInExpr(";", tokens, True, advance = False)
    
        self.out += (" " * tabs) + Tokens(var + [Token("="), Token("not")] + var).join() + "\n"

        return loop, objNames
    
    def __asyncGen(self, keyw):
        def fn(tokens : Tokens, tabs, loop, objNames):
            next = tokens.peek()
            if next.tok != ":":
                next.warning(f'expecting ":" after "{keyw}". ignoring')
            else: tokens.next()

            self.out += (" " * tabs) + keyw + " "

            return loop, objNames
        
        return fn
    
    def __quit(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.peek()
        if next.tok != ";":
            next.warning(f'expecting ";" after "quit". ignoring')
        else: tokens.next()

        self.out += (" " * tabs) + "quit()\n"

        return loop, objNames
    
    def __return(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.peek()
        if next.tok == ";":
            tokens.next()
            self.out += (" " * tabs) + "return\n"
            return loop, objNames
        
        _, val = self.getUntilNotInExpr(";", tokens, True, advance = False)

        self.out += (" " * tabs) + Tokens([Token("return")] + val).join() + "\n"

        return loop, objNames
    
    def __break(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        next = tokens.peek()
        if next.tok != ";":
            next.warning(f'expecting ";" after "break". ignoring')
        else: tokens.next()

        if loop is None:
            self.__error('cannot use "break" outside of a loop', keyw)
            return loop, objNames

        self.out += (" " * tabs) + "break\n"

        return loop, objNames
    
    def __continue(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        next = tokens.peek()

        if next is None:
            keyw.warning(f'expecting ";" after "continue". ignoring')
        elif next.tok != ";":
            next.warning(f'expecting ";" after "continue". ignoring')
        else: tokens.next()

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
    
    def __unchecked(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.peek()
        if next.tok != ":":
            next.warning(f'expecting ":" after "unchecked". ignoring')
        else: tokens.next()

        self.nextUnchecked = True

        return loop, objNames
    
    def __abstract(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.peek()
        if next.tok != ":":
            next.warning(f'expecting ":" after "abstract". ignoring')
        else: tokens.next()

        self.nextAbstract = True

        if not self.flags["abstract"]:
            self.flags["abstract"] = True
            self.out = "from abc import abstractmethod\nfrom abc import ABC as _ABSTRACT_BASE_CLASS_\n" + self.out

        return loop, objNames
    
    def __printReturn(self, tokens : Tokens, tabs, loop, objNames):
        _, val = self.getUntilNotInExpr(";", tokens, True, advance = False)
        strVal = Tokens(val).join()

        self.out += (" " * tabs) + "_OPAL_PRINT_RETURN_(" + strVal + ")\n"

        return loop, objNames
    
    def __package(self, tokens : Tokens, tabs, loop, objNames):
        _, name = self.getUntilNotInExpr(":", tokens, True, advance = False)
        strName = Tokens(name).join()

        self.lastPackage = strName

        self.out += (" " * tabs) + "from " + strName + " "

        return loop, objNames
    
    def __import(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()
        _, imports = self.getUntilNotInExpr(";", tokens, True, advance = False)
        
        if len(imports) == 1 and imports[0].tok == "*":
            if self.lastPackage == "":
                self.__error('cannot use "import *" if no package is defined', keyw)
                return loop, objNames
            
            modl = import_module(self.lastPackage)
            for name in dir(modl):
                if callable(getattr(modl, name)):
                    self.newObj(objNames, Token(name), "untyped")

            self.lastPackage = ""
            self.out += "import *\n"

            return loop, objNames
        
        imports = Tokens(imports)
        
        while imports.isntFinished():
            next = imports.next()
            if next == "": break

            name = next

            if not imports.isntFinished():
                self.newObj(objNames, name, "untyped")
                break
                    
            next = imports.next()
            if next.tok == "as":
                next = imports.next()
                name = next

                if imports.isntFinished():
                    next = imports.next()

            self.newObj(objNames, name, "untyped")

            if not imports.isntFinished(): break

            if next.tok != ",":
                self.__error("invalid syntax: modules should be separated by commas", next)

        self.lastPackage = ""

        self.out += (" " * tabs) + "import " + imports.join() + "\n"

        return loop, objNames
    
    def __incDec(self, op):
        def fn(tokens : Tokens, tabs, loop, objNames):
            _, var = self.getUntilNotInExpr(";", tokens, True, advance = False)
            strVar = Tokens(var).join()

            self.out += (" " * tabs) + strVar + op +"=1\n"

            return loop, objNames
            
        return fn
    
    def __use(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.next()

        peek = tokens.peek()
        if peek is not None and peek.tok == "as":
            translates = next
            next = tokens.next()

            if not tokens.isntFinished():
                self.__error('invalid syntax: expecting an identifier name after "as"', next)
                return loop, objNames
            
            self.newIdentifier(tokens.next(), translates.tok)
        else:
            self.newIdentifier(next, "::py")

        peek = tokens.peek()
        if peek is None or peek.tok != ";":
            next.warning(f'expecting ";" after use identifier definition. ignoring')
        else: tokens.next()

        return loop, objNames
    
    def __simpleBlock(self, keyw, kwname):
        def fn(tokens : Tokens, tabs, loop, objNames):
            self.checkDirectNext("{", f'"{kwname}"', tokens)
            block = self.getSameLevelParenthesis("{", "}", tokens)

            self.out += (" " * tabs) + keyw

            if len(block) == 0:
                self.out += ":pass\n"
            else: 
                self.out += ":\n"
                loop, objNames = self.__compiler(Tokens(block), tabs + 1, loop, objNames)

            return loop, objNames
        
        return fn
    
    def __block(self, keyw, inLoop = None, content = None, after = None):
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

            tmp, objNames = self.__compiler(Tokens(block), tabs + 1, internalLoop, objNames)
            if loopNotDef: loop = tmp

            return loop, objNames
        
        return fn
    
    def __main(self, tokens : Tokens, tabs, loop, objNames):
        keyw = tokens.last()

        next = tokens.peek()
        if next.tok == "(":
            tokens.next()
            next = tokens.next()
            if next.tok != ")":
                next.warning("invalid syntax: brackets should be closed. ignoring")

            if self.flags["mainfn"]:
                self.__error("main function can only be defined once", keyw)
                return loop, objNames
            
            self.flags["mainfn"] = True

            return self.__simpleBlock("def _OPAL_MAIN_FUNCTION_()", "main()")(tokens, tabs, loop, objNames)
        
        return self.__simpleBlock("if __name__=='__main__'", "main")(tokens, tabs, loop, objNames)
    
    def __namespace(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.next()
        self.newObj(objNames, next, "class")
        tmp = tokens.next()

        if tmp.tok != "{":
            self.__error('invalid syntax: expecting "{" after namespace definition')
            return loop, objNames

        return self.__block("class", content = [next])(tokens, tabs, loop, objNames)
    
    def __do(self, tokens : Tokens, tabs, loop, objNames):
        peek = tokens.peek()

        if peek.tok == "{":
            tokens.next()
            block = self.getSameLevelParenthesis("{", "}", tokens)

            next = tokens.peek()
            if next.tok != "while":
                next.warning('invalid syntax: expecting "while" after a do-while loop. ignoring')
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
            if intVal == 0:
                Token(
                    " " * (valList[-1].pos - valList[0].pos + 1), 
                    valList[0].line, valList[0].pos, valList[0].tokens
                ).warning('a 0-times "repeat" statement is being used')

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
    
    def __matchLoop(self, tokens : Tokens, tabs, loop, objNames, value, op, unchecked):
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
                        
                        if unchecked:
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
                        if unchecked:
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
                    if unchecked:
                        self.__error('cannot use "found" in unchecked "match" statement body', next)

                    loop, objNames = self.__simpleBlock(f"if _OPAL_MATCHED_{tabs}", "found")(tokens, tabs, loop, objNames)

                    foundMet = True
                case _:
                    self.__error('invalid identifier in "match" statement body', next)

        return loop, objNames
    
    def __match(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.peek()
        if next.tok == ":":
            idLine = next.line
            idPos  = next.pos
            tokens.next()

            next = tokens.next()
            if next.tok != "(":
                self.__error('invalid syntax: expecting "(" after "match:"')
                return loop, objNames
            
            op = self.getSameLevelParenthesis("(", ")", tokens)

            if len(op) == 0:
                op = [Token("==", idLine, idPos, tokens)]
        else: op = None

        _, value = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)

        if len(block) == 0:
            return loop, objNames
        
        unchecked = self.nextUnchecked

        if unchecked: 
            self.nextUnchecked = False
        else:
            matched = str(tabs)
            self.out += (" " * tabs) + f"_OPAL_MATCHED_{tabs}=False\n"
    
        if op is None:
            self.out += (" " * tabs) + Tokens([Token("match")] + value).join() +":\n"

        loop, objNames = self.__matchLoop(Tokens(block), tabs, loop, objNames, value, op, unchecked)

        if not unchecked:
            self.out += (" " * tabs) + f"del _OPAL_MATCHED_{matched}\n"

        return loop, objNames
    
    def __modifier(self, type_, name = None):
        def fn(tokens : Tokens, tabs, loop, objNames):
            if name is None:
                next = tokens.peek()
                if next.tok != "<":
                    next.warning(f'expecting "<" after {type_} outside of a "property" statement. ignoring')
                    localName = next
                else: 
                    tokens.next()
                    localName = tokens.next()

                next = tokens.peek()
                if next.tok != ">":
                    next.warning("invalid syntax: property angular brackets should be closed. ignoring")
                else: tokens.next()
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
                        valName[0].warning('only one argument should be passed to a setter. using first')
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
            
            self.__compiler(Tokens(block), tabs + 1, loop, intObjs)
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
        _, value = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)

        if len(value) > 1:
            value[0].warning('property name should contain only one token. using first')
        
        self.newObj(objNames, value[0], "untyped")

        if len(block) == 0:
            return loop, objNames
        
        self.out += (" " * tabs) + Tokens([value[0], Token("="), Token("property()")]).join() + "\n"

        self.__propertyLoop(Tokens(block), tabs, loop, objNames, value[0])

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
                    backPos = variablesDef.pos
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
        cnt = [x.tok for x in self.getUntilNotInExpr("{", tokens.copy(), True)[1]].count(";")

        match cnt:
            case 2: # C-like for
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
                            next.warning('invalid syntax: expecting "," after variable name in a for loop. ignoring')
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
        
        _, objNames = self.__compiler(Tokens(block), tabs + 1, CompLoop(increments), objNames)

        if increments != "": self.out += increments
            
        return loop, objNames
    
    def __enum(self, tokens : Tokens, tabs, loop, objNames):
        _, value = self.getUntilNotInExpr("{", tokens, True, advance = False)
        block = self.getSameLevelParenthesis("{", "}", tokens)

        if len(value) == 0:
            if len(block) == 0:
                return loop, objNames
            
            inTabs = tabs
        else:
            if len(value) > 1:
                value[0].warning('enum name should contain only one token. using first')

            self.out += (" " * tabs) + Tokens([Token("class"), value[0]]).join() + ":"

            if len(block) == 0:
                self.out += "pass\n"
                return loop, objNames
            
            self.out += "\n"

            self.newObj(objNames, value[0], "untyped")

            inTabs = tabs + 1

        objs, assignments = self.__handleAssignmentChain(inTabs, objNames, block, False)
        self.out += (" " * inTabs) + Tokens(objs).join() + f"=range({str(len([x for x in objs if x.tok != ',']))})\n" + assignments
        
        return loop, objNames
    
    def __dynamicStepOne(self, tokens : Tokens, tabs):
        _, expr = self.getUntilNotInExpr(";", tokens, True, advance = False)
        expr = Tokens(self.__getInlineIncDec(expr))

        if self.nextUnchecked:
            self.nextUnchecked = False
            self.out += (" " * tabs) + expr.join() + "\n"
            return None, None

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
        
        return names, expr
            
    def __dynamic(self, tokens : Tokens, tabs, loop, objNames):
        next = tokens.next()
        if next.tok == "<-":
            names, expr = self.__dynamicStepOne(tokens, tabs)
            if names is None: return loop, objNames

            for name in names:
                if name in objNames:
                    objNames[name] = ("dynamic", TypeCheckMode.NOCHECK)

            self.out += (" " * tabs) + expr.join() + "\n"

            return loop, objNames
        
        self.__error('invalid syntax: expected "<-" after "dynamic"', next)
        return loop, objNames
    
    def __init__(self):
        self.out = ""
        self.useIdentifiers = {}

        self.macros = {}
        self.consts = {}
        self.preConsts = {}

        self.hadError  = False
        self.asDynamic = False
        self.__resetFlags()

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
            "quit":                self.__quit,
            "return":              self.__return,
            "break":               self.__break,
            "continue":            self.__continue,
            "@":                   self.__untilEnd("@"),
            "throw":               self.__untilEnd("raise"),
            "super":               self.__untilEnd("super"),
            "del":                 self.__untilEnd("del"),
            "assert":              self.__untilEnd("assert"),
            "yield":               self.__untilEnd("yield"),
            "global":              self.__untilEnd("global"),
            "external":            self.__untilEnd("nonlocal"),
            "_OPAL_PRINT_RETURN_": self.__printReturn,
            "not":                 self.__not,
            "++":                  self.__incDec("+"),
            "--":                  self.__incDec("-"),
            "main":                self.__main,
            "try":                 self.__simpleBlock("try", "try"),
            "catch":               self.__block("except", "catch"),
            "success":             self.__simpleBlock("else", "success"),
            "else":                self.__simpleBlock("else", "else"),
            "if":                  self.__block("if"),
            "elif":                self.__block("elif"),
            "while":               self.__block("while", GenericLoop()),
            "with":                self.__block("with"),
            "do":                  self.__do,
            "for":                 self.__for,
            "repeat":              self.__repeat,
            "match":               self.__match,
            "enum":                self.__enum,
            "dynamic":             self.__dynamic,
            "abstract":            self.__abstract,
        }

    def __warning(self, msg, line):
        print(f"warning (line {str(line + 1)}):", msg)

    def __lineErr(self, msg, line):
        self.hadError = True
        print(f"error (line {str(line + 1)}):", msg)

    def __error(self, msg, token : Token):
        self.hadError = True
        token.error(msg)

    def __resetFlags(self):
        self.flags = {
            "OPAL_ASSERT_CLASSVAR": False,
            "abstract": False,
            "mainfn": False,
            "OPAL_PRINT_RETURN": False
        }

    def newObj(self, objNames, nameToken : Token, type_, checkPolicy = TypeCheckMode.NOCHECK):
        if not nameToken.tok.isidentifier():
            self.__error(f'invalid identifier name "{nameToken.tok}"', nameToken)
            return

        if self.asDynamic and type_ != "untyped":
            objNames[nameToken.tok] = ("dynamic", checkPolicy)
        else: objNames[nameToken.tok] = (type_, checkPolicy)

    def newIdentifier(self, nameToken : Token, translatesTo):
        if not nameToken.tok.isidentifier():
            self.__error(f'invalid identifier name "{nameToken.tok}"', nameToken)
            return
        
        self.useIdentifiers[nameToken.tok] = translatesTo

    def checkDirectNext(self, ch, msg, tokens : Tokens):
        next = tokens.next()
        if next.tok != ch:
            next.warning(f'invalid syntax: expecting "{ch}" directly after {msg}. ignoring.')
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
                    if ch != "{":
                        lastCrBrack = next
                        crBrack += 1
                case "}":
                    if ch != "{":
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
                if next.tok == ch:
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
                self.__error(f'expecting character "{ch}"', Token(""))
            else:
                self.__error(f'expecting character "{ch}"', next)

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
                names, expr = self.__dynamicStepOne(tokens, tabs)
                if names is None: continue

                for name in names:
                    if name in objNames and objNames[name][0] == "auto":
                        self.out += (" " * tabs) + f"_OPAL_AUTOMATIC_TYPE_{name}=type({name})\n"

                self.out += (" " * tabs) + expr.join() + "\n"

                for name in names:
                    if name in objNames and objNames[name][1] != TypeCheckMode.NOCHECK:
                        if objNames[name][0] == "auto":
                            self.out += (
                                (" " * tabs) + f"{name}=_OPAL_AUTOMATIC_TYPE_{name}({name})\n" + 
                                (" " * tabs) + "del _OPAL_AUTOMATIC_TYPE_" + name
                            )
                        elif objNames[name][1] == TypeCheckMode.CHECK:
                            self.out += (" " * tabs) + f"{name}=_OPAL_ASSERT_CLASSVAR_TYPE_({objNames[name][0]},{name})\n"
                        elif objNames[name][1] == TypeCheckMode.FORCE:
                            self.out += (" " * tabs) + f"{name}={objNames[name][0]}({name})\n"
            elif next.tok in self.useIdentifiers:
                if self.useIdentifiers[next.tok] == "::py":
                    next = tokens.next()
                    if next.tok != ".":
                        self.__error('expecting "." after custom identifier', next)
                        continue
                else:
                    tokens.pos -= 1

                _, expr = self.getUntilNotInExpr(";", tokens, True, advance = False)
                self.out += (" " * tabs) + Tokens(expr).join() + "\n"
            elif next.tok == "__OPAL_PYTHON_EMBED":
                if self.__manualEmbed:
                    next.warning('avoid manually using "__OPAL_PYTHON_EMBED" for readability purposes. prefer the $nocompile-$restore syntax')

                next = tokens.next()
                if next.tok != "-":
                    next.warning('invalid syntax: expecting "-" after "__OPAL_PYTHON_EMBED". ignoring')
                else: next = tokens.next()

                try:
                    embedTabs = int(next.tok)
                except ValueError:
                    next.warning('expecting an integer after "__OPAL_PYTHON_EMBED-". using 0')
                    embedTabs = 0

                next = tokens.peek()
                if next.tok != ".":
                    next.warning(f'invalid syntax: expecting "." after "__OPAL_PYTHON_EMBED-{embedTabs}". ignoring')
                else: tokens.next()

                _, code = self.getUntilNotInExpr(";", tokens, True, advance = False)

                self.out += (" " * embedTabs) + Tokens(code).join() + "\n"
            else:
                self.__error(f'unknown statement', next)

        return loop, objNames

    def replaceConsts(self, expr, consts):
        for const in consts:
            expr = re.sub(rf"{const}", str(consts[const]), expr)
        return expr

    def getDir(self, expr):
        return eval(self.replaceConsts(expr, self.preConsts | self.consts))

    def readFile(self, fileName, rep = False):
        with open(fileName, "r") as txt:
            content = txt.read()
        return content.replace("\t", " " if rep else "")

    def __readPy(self, fileDir):
        self.__manualEmbed = False

        result = ""
        for line in self.readFile(fileDir).split("\n"):
            strippedLine = line.lstrip()
            tabs = len(line) - len(strippedLine)
            result += f"__OPAL_PYTHON_EMBED-{tabs}." + line + ";\n"

        return result

    def __preCompiler(self, source):
        result = ""
        savingMacro = None
        inPy = False

        for i, line in enumerate(source.split("\n")):
            noSpaceLine = line.replace(" ", "")
            if noSpaceLine == "": 
                result += "\n"
                continue

            if not noSpaceLine[0] in ("$", "#"):
                if inPy:
                    self.__manualEmbed = False

                    strippedLine = line.lstrip()
                    tabs = len(line) - len(strippedLine)
                    line = f"__OPAL_PYTHON_EMBED-{tabs}." + line + ";"

                if savingMacro is None:
                    result += line + "\n"
                else:
                    result += "\n" 
                    savingMacro.addLine(line)

                continue

            if noSpaceLine[0] == "#":
                result += "\n"
                continue

            if noSpaceLine[0] == "$":
                result += "\n"

                tokenizedLine = Tokens(line)
                tokenizedLine.next()

                next = tokenizedLine.next()
                match next.tok:
                    case "include":
                        if savingMacro is not None:
                            self.__warning("precompiler instruction (include) found inside macro definition. ignoring line", i)
                            continue
                        
                        fileDir = self.getDir(Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join())
                        
                        if fileDir.endswith(".py"):
                            result += self.__readPy(fileDir)
                        else:
                            result += self.__preCompiler(self.readFile(fileDir))
                    case "includeDirectory":
                        if savingMacro is not None:
                            self.__warning("precompiler instruction (includeDirectory) found inside macro definition. ignoring line", i)
                            continue

                        fileDir = self.getDir(Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join())

                        included = ""
                        for file in [os.path.join(fileDir, f) for f in os.listdir(fileDir) if f.endswith(".opal") or f.endswith(".py")]:
                            if file.endswith(".py"):
                                result += self.__readPy(file)
                            else:
                                included += self.readFile(file) + "\n"

                        result += self.__preCompiler(included)
                    case "define":
                        if savingMacro is not None:
                            self.__warning("precompiler instruction (define) found inside macro definition. ignoring line", i)
                            continue

                        name    = tokenizedLine.next().tok
                        content = Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()
                        
                        self.consts[name] = content
                    case "pdefine":
                        if savingMacro is not None:
                            self.__warning("precompiler instruction (pdefine) found inside macro definition. ignoring line", i)
                            continue

                        name    = tokenizedLine.next().tok
                        content = Tokens(tokenizedLine.tokens[tokenizedLine.pos:]).join()

                        self.preConsts[name] = content
                    case "macro":
                        if savingMacro is not None:
                            self.__warning("precompiler instruction (macro) found inside macro definition. ignoring line", i)
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
                    case "end":
                        if savingMacro is None:
                            self.__warning("end of macro found with no macro definition. ignoring line", i)
                            continue

                        if savingMacro.code == "":
                            self.__warning(f'the "{savingMacro.name}" macro is being saved as empty', i)
                        
                        self.macros[savingMacro.name] = savingMacro
                        savingMacro = None
                    case "call":
                        if savingMacro is not None:
                            self.__warning("precompiler instruction (call) found inside macro definition. ignoring line", i)
                            continue

                        name = tokenizedLine.next().tok

                        if name not in self.macros:
                            self.__lineErr(f'trying to call undefined macro "{name}"', i)
                            continue

                        macro = self.macros[name]

                        next = tokenizedLine.peek()
                        if next is not None and next.tok == "(":
                            tokenizedLine.next()
                            args = self.getSameLevelParenthesis("(", ")", tokenizedLine)

                            if len(args) != 0:
                                if macro.args == args:
                                    result += f"new dynamic {macro.args};"
                                else:
                                    result += f"new dynamic {macro.args};{macro.args}={args};"
                                
                        result += macro.code
                    case "nocompile":
                        inPy = True
                    case "restore":
                        inPy = False
                    case _:
                        self.__warning("unknown or incomplete precompiler instruction. ignoring line", i)

        return self.replaceConsts(result, self.consts)

    def compile(self, section):
        self.__resetFlags()
        self.useIdentifiers = {}
        self.macros = {}
        self.out = ""
        self.hadError = False

        self.__manualEmbed = True
        self.nextAbstract  = False
        self.nextUnchecked = False
        self.lastPackage   = ""

        self.tokens = Tokens(self.__preCompiler(section))

        if "_OPAL_PRINT_RETURN_" in [x.tok for x in self.tokens.tokens]:
            self.flags["OPAL_PRINT_RETURN"] = True
            self.out += "from libs.std import _OPAL_PRINT_RETURN_\n"

        self.__compiler(self.tokens, 0, None, {})

        if self.flags["mainfn"]:
            self.out += 'if __name__=="__main__":_OPAL_MAIN_FUNCTION_()\n'

        self.asDynamic = False
        self.consts = {}
        self.preConsts = {}

        if self.hadError: return ""
        else: return self.out

    def compileFile(self, fileIn, top = ""):
        return self.compile(top + "\n" + self.readFile(fileIn))

    def compileToPY(self, fileIn, fileOut, top = ""):
        result = self.compileFile(fileIn, top)

        if result != "":
            with open(fileOut, "w") as txt:
                txt.write(result)

def getHomeDirFromFile(file):
    return str(Path(file).parent.absolute()).replace("\\", "\\\\\\\\")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("opal compiler v2023.2.21 - thatsOven")
    else:
        compiler = Compiler()

        if "--dynamic" in sys.argv:
            compiler.asDynamic = True
            sys.argv.remove("--dynamic")

        if "--dir" in sys.argv:
            findDir = False
            idx = sys.argv.index("--dir")
            sys.argv.pop(idx)

            drt = sys.argv.pop(idx).replace("\\", "\\\\")
            compiler.preConsts["HOME_DIR"] = drt
            top = 'new dynamic HOME_DIR="' + drt + '";'
        else:
            findDir = True

        if sys.argv[1] == "pycompile":
            if len(sys.argv) == 2:
                print('input file required for command "pycompile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = drt
                top = 'new dynamic HOME_DIR="' + drt + '";'

            if len(sys.argv) == 3:
                compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), "output.py", top)
            else:
                compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), sys.argv[3].replace("\\", "\\\\"), top)

            if not compiler.hadError:
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")

        elif sys.argv[1] == "compile":
            if len(sys.argv) == 2:
                print('input file required for command "compile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = drt
                top = 'new dynamic HOME_DIR="' + drt + '";'

            compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), "tmp.py", top)

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
                drt = getHomeDirFromFile(sys.argv[1])
                compiler.preConsts["HOME_DIR"] = drt
                top = 'new dynamic HOME_DIR="' + drt + '";'

            result = compiler.compileFile(sys.argv[1], top)
            if not compiler.hadError: 
                sys.argv = sys.argv[1:]
                exec(result)
