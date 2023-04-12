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

import os, sys, cythonbuilder, shutil
from timeit              import default_timer
from pathlib             import Path
from components.Compiler import *

def getHomeDirFromFile(file):
    return str(Path(file).parent.absolute()).replace("\\", "\\\\\\\\")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("opal compiler v2023.4.12 - thatsOven")
    else:
        compiler = Compiler()
        compiler.handleArgs(sys.argv)

        if "--debug" in sys.argv:
            debug = True
            sys.argv.remove("--debug")
        else: debug = False

        if "--dir" in sys.argv:
            findDir = False
            idx = sys.argv.index("--dir")
            sys.argv.pop(idx)

            drt = sys.argv.pop(idx).replace("\\", "\\\\")
            compiler.preConsts["HOME_DIR"] = f'"{drt}"'
            top = 'new dynamic HOME_DIR="' + drt + '";'
        else:
            findDir = True

        if sys.argv[1] == "pyxcompile":
            if len(sys.argv) == 2:
                print('input file required for command "pyxcompile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = f'"{drt}"'
                top = 'new dynamic HOME_DIR="' + drt + '";'

            name = os.path.basename(sys.argv[2]).split(".")[0]
            if len(sys.argv) == 3:
                compiler.compileToPYX(sys.argv[2].replace("\\", "\\\\"), f"{name}.pyx", top)
            else:
                compiler.compileToPYX(sys.argv[2].replace("\\", "\\\\"), sys.argv[3].replace("\\", "\\\\"), top)

            if not compiler.hadError:
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
        elif sys.argv[1] == "pycompile":
            if len(sys.argv) == 2:
                print('input file required for command "pycompile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = f'"{drt}"'
                top = 'new dynamic HOME_DIR="' + drt + '";'

            name = os.path.basename(sys.argv[2]).split(".")[0]
            if len(sys.argv) == 3:
                compiler.compileToPY(sys.argv[2].replace("\\", "\\\\"), f"{name}.py", top)
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
                compiler.preConsts["HOME_DIR"] = f'"{drt}"'
                top = 'new dynamic HOME_DIR="' + drt + '";'

            name = os.path.basename(sys.argv[2]).split(".")[0]
            for char in ILLEGAL_CHARS:
                name = name.replace(char, "_")

            compiler.compileToPYX(sys.argv[2].replace("\\", "\\\\"), f"{name}.pyx", top)

            if not compiler.hadError:
                print("opal -> Cython: Done in " + str(round(default_timer() - time, 4)) + " seconds")
                cythonbuilder.cy_init()

                try:
                    cythonbuilder.cy_build([f"{name}.pyx"], debug, True)
                except Exception as e:
                    print("Compilation failed.")
                    ok = False
                else:
                    ok = True

                if os.path.exists("ext"):   shutil.rmtree("ext")
                if os.path.exists("build"): shutil.rmtree("build")
                if os.path.exists(f"{name}.pyx"): os.remove(f"{name}.pyx")
                if os.path.exists(f"{name}.c"):   os.remove(f"{name}.c")

                if ok:
                    if len(sys.argv) == 3:
                        filename = f"{name}.py"
                    else:
                        filename = sys.argv[3].replace("\\", "\\\\")

                    with open(filename, "w") as py:
                        py.write(f"from os import environ\nenviron['_OPAL_RUN_AS_MAIN_']=''\nimport {name}\ndel environ['_OPAL_RUN_AS_MAIN_']")

                    print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
        else:
            sys.argv[1] = sys.argv[1].replace("\\", "\\\\")
            if not os.path.exists(sys.argv[1]):
                print('unknown command or nonexistent file "' + sys.argv[1] + '"')
                sys.exit(1)

            if findDir:
                drt = getHomeDirFromFile(sys.argv[1])
                compiler.preConsts["HOME_DIR"] = f'"{drt}"'
                top = 'new dynamic HOME_DIR="' + drt + '";'

            result = compiler.compileFile(sys.argv[1], top)
            if not compiler.hadError: 
                sys.argv = sys.argv[1:]
                exec(result)
