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

import colorama

from components.utils import MutableStringBuffer

class Token:
    def __init__(self, tok, line = 0, pos = 0, tokens = None):
        self.tok     : str = tok
        self.line    : int = line
        self.pos     : int = pos
        self.maxline : int = 1000

        self.tokens : Tokens = tokens

    def copy(self):
        tok = Token(self.tok, self.line, self.pos, self.tokens)
        tok.maxline = self.maxline
        return tok

    def __getlines(self):
        if self.line <= 3:
            return range(1, min(6, self.maxline))

        if self.line >= self.maxline - 3:
            return range(self.maxline - 5, self.maxline)
        
        return range(self.line - 3, self.line + 2)
    
    def __message(self, type_, color, msg, location):
        if self.tokens is None: print(color + f"{type_}{colorama.Style.RESET_ALL} {location[0]}:", msg)
        else:
            maxlineLen = len(str(self.maxline))

            print(color + f"{type_}{colorama.Style.RESET_ALL} ({location[0]}, line {self.line - location[1]}, pos {self.pos}):", msg)

            offs = int(bool(location[1] - 1))
            for line in self.__getlines():
                if line == self.line - 1:
                    print(
                        f"{str(line - location[1] + offs).rjust(maxlineLen)} | " + self.tokens.source[line].rstrip() + "\n" + 
                        (" " * maxlineLen) + " |" + (" " * (self.pos + 1)) + color + ("^" * len(self.tok)) + colorama.Style.RESET_ALL
                    )

                    continue
                
                print(f"{str(line - location[1] + offs).rjust(maxlineLen)} | " + self.tokens.source[line].rstrip())

    def error(self, msg, location):
        self.__message("error", colorama.Fore.RED, msg, location)

    def warning(self, msg, location):
        self.__message("warning", colorama.Fore.LIGHTYELLOW_EX, msg, location)

    def note(self, msg, location):
        self.__message("note", colorama.Fore.LIGHTBLUE_EX, msg, location)

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
        
        self.tokens[self.pos - 1].error("invalid syntax: the expression wasn't properly closed. no tokens remaining", "<main>")
    
    def last(self) -> Token:
        return self.tokens[self.pos - 1]
    
    @classmethod
    def replaceTokens(self, tokens):
        i = 0
        while i < len(tokens):
            match str(tokens[i].tok):
                case "||":
                    tokens[i].tok = "or"
                case "&&":
                    tokens[i].tok = "and"
                case "!":
                    tokens[i].tok = "not"
                case "?":
                    tokens[i].tok = "_OPAL_PRINT_RETURN_"
                case "super":
                    if i + 1 < len(tokens) and str(tokens[i + 1].tok) != "(":
                        tokens.insert(i + 1, Token("()"))
                        i += 1
            i += 1

        for token in tokens:
            if type(token.tok) is MutableStringBuffer:
                token.tok = str(token.tok)

        return tokens

    @classmethod
    def verifyTok(self, tokens: list, first: Token, next: Token, opts):
        if str(next.tok) in opts:
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
            if token.tok.isidentifier() or token.tok[0].isidentifier():
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
        tmp           = [Token(MutableStringBuffer(), line, pos, self)]
        inLineComment = False
        inString      = False
        inStringAlt   = False
        lastSym       = False
        
        for ch in source:
            if inLineComment:
                if ch == "\n":
                    inLineComment = False
                    line += 1
                    pos   = 0
                    tmp.append(Token(MutableStringBuffer(), line, pos, self))
                    continue
                
                pos += 1
                continue

            match ch:
                case " " | "\t":
                    if inString or inStringAlt: tmp[-1].tok += ch
                    else:        
                        tmp.append(Token(MutableStringBuffer(), line, pos + 1, self))
                case "#":
                    if inString or inStringAlt: tmp[-1].tok += ch
                    else:
                        inLineComment = True
                case "\n":
                    line += 1
                    pos   = 0

                    if inString or inStringAlt: tmp[-1].tok += ch
                    else:
                        tmp.append(Token(MutableStringBuffer(), line, pos, self))
                        continue
                case '"':
                    if inString:
                        tmp[-1].tok += ch
                        inString = False
                    elif inStringAlt:
                        tmp[-1].tok += ch
                    else:
                        tok = MutableStringBuffer()
                        tok += ch
                        tmp.append(Token(tok, line, pos, self))
                        inString = True
                case "'":
                    if inStringAlt:
                        tmp[-1].tok += ch
                        inStringAlt = False
                    elif inString:
                        tmp[-1].tok += ch
                    else:
                        tok = MutableStringBuffer()
                        tok += ch
                        tmp.append(Token(tok, line, pos, self))
                        inStringAlt = True
                case _:
                    if inString or inStringAlt:
                        tmp[-1].tok += ch
                    elif ch.isalnum() or ch == "_":
                        if lastSym:
                            lastSym = False
                            tok = MutableStringBuffer()
                            tok += ch
                            tmp.append(Token(tok, line, pos, self))
                        else:
                            tmp[-1].tok += ch
                    else:                            
                        lastSym = True
                        tok = MutableStringBuffer()
                        tok += ch
                        tmp.append(Token(tok, line, pos, self))

            pos += 1

        clean = []
        for token in tmp:
            if str(token.tok) != "":
                token.maxline = line
                clean.append(token)
        tmp = clean

        tokens = []
        i = 0
        while i < len(tmp) - 1:
            token = tmp[i]
            i += 1

            match str(token.tok):
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
                    strTok = str(tmp[i].tok)
                    if strTok.startswith('"') or strTok.startswith("'"):
                        token.tok += tmp[i].tok
                        i += 1
                case ":" | "^" | "%" | "=":
                    if str(tmp[i].tok) == "=":
                        token.tok += tmp[i].tok
                        i += 1
                case "*":
                    strTok = str(tmp[i].tok)
                    if strTok in ("*", "="):
                        if strTok == "*":
                            next = tmp[i]
                            i += 1

                            if i < len(tmp) and strTok == "=":
                                token.tok += next.tok
                                token.tok += tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case "/":
                    strTok = str(tmp[i].tok)
                    if strTok in ("/", "="):
                        if strTok == "/":
                            next = tmp[i]
                            i += 1

                            if i < len(tmp) and strTok == "=":
                                token.tok += next.tok
                                token.tok += tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case ">":
                    strTok = str(tmp[i].tok)
                    if strTok in (">", "="):
                        if strTok == ">":
                            next = tmp[i]
                            i += 1

                            if i < len(tmp) and strTok == "=":
                                token.tok += next.tok
                                token.tok += tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case "<":
                    strTok = str(tmp[i].tok)
                    if strTok in ("<", "=", "-"):
                        if strTok == "<":
                            next = tmp[i]
                            i += 1

                            if i < len(tmp) and strTok == "=":
                                token.tok += next.tok
                                token.tok += tmp[i].tok
                                i += 1
                            else: 
                                token.tok += next.tok
                        else:
                            token.tok += tmp[i].tok
                            i += 1
                case '""':
                    if str(tmp[i].tok).startswith('"'):
                        token.tok += tmp[i].tok
                        i += 1
                    elif len(tokens) > 0 and str(tokens[-1].tok).endswith('"'):
                        tokens[-1].tok += token.tok
                        continue
                case "''":
                    if str(tmp[i].tok).startswith("'"):
                        token.tok += tmp[i].tok
                        i += 1
                    elif len(tokens) > 0 and str(tokens[-1].tok).endswith("'"):
                        tokens[-1].tok += token.tok
                        continue

            tokens.append(token)

        if i < len(tmp):
            lastTok = tmp[len(tmp) - 1]

            match lastTok.tok:
                case '""':
                    if str(tokens[-1].tok).endswith('"'):
                        tokens[-1].tok += lastTok.tok
                case "''":
                    if str(tokens[-1].tok).endswith("'"):
                        tokens[-1].tok += lastTok.tok
                case _:
                    tokens.append(lastTok)

        return self.replaceTokens(tokens)