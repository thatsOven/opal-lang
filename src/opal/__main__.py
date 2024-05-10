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

import os, sys, shutil, numpy, subprocess
from timeit              import default_timer
from pathlib             import Path
from setuptools          import setup
from Cython.Build        import cythonize
from Cython.Compiler     import Options

from opal.components.Compiler import *

RELEASE_COLLECT = ["__future__", "typeguard", "pygame", "unittest", "numpy", "json"]
PY_STDLIB       = set(sys.stdlib_module_names) | {"opal"} - {"antigravity"} # fun, but i don't wanna open the xkcd page every time i compile something
NO_INSTALL      = set(RELEASE_COLLECT) | PY_STDLIB

def build(file, debug = False):
    Options.annotate = debug

    oldArgs = sys.argv
    sys.argv = [sys.argv[0], "build_ext", "--inplace"]

    try:
        setup(
            name         = os.path.basename(file).split(".")[0],
            include_dirs = [numpy.get_include()], 
            ext_modules  = cythonize(file, compiler_directives = {
                "language_level": "3"
            }),
            zip_safe = False
        )
    except:
        ok = False
    else:
        ok = True

    sys.argv = oldArgs

    return ok

def compileBase(compiler, filename, name, top, time):
    compiler.compileToPYX(filename, f"{name}.pyx", top)
    if compiler.hadError: return False

    print("opal -> Cython: Done in " + str(round(default_timer() - time, 4)) + " seconds")

    ok = build(f"{name}.pyx", debug)
                    
    if os.path.exists(f"{name}.pyx"): os.remove(f"{name}.pyx")
    if os.path.exists(f"{name}.c"):   os.remove(f"{name}.c")

    return ok

def compilePy(compiler, filename, _, endName, top, time, _0):
    compiler.compileToPY(filename, f"{endName}.py", top)
    if compiler.hadError: return None

    print("opal -> Python: Done in " + str(round(default_timer() - time, 4)) + " seconds")
    return f"{endName}.py"

def compileNormal(compiler, fileInput, name, endName, top, time, noModule):
    if compileBase(compiler, fileInput, name, top, time):
        if os.path.exists("build"): shutil.rmtree("build")
        if (not compiler.module) or noModule:
            if len(sys.argv) == 3:
                filename = f"{endName}.py"
            else:
                filename = sys.argv[3]
                name = os.path.basename(filename).split(".")[0]

            with open(filename, "w") as py:
                py.write(f"from os import environ\nenviron['_OPAL_RUN_AS_MAIN_']=''\nimport {name}\ndel environ['_OPAL_RUN_AS_MAIN_']")
        return filename

def compileOne(libs, file, compiler):
    time = default_timer()

    filename = os.path.join(libs, file)
    name     = file.split(".")[0]

    compiler.preConsts["HOME_DIR"] = f'r"{libs}"'
    top = 'new dynamic HOME_DIR=r"' + libs + '";'

    return compileBase(compiler, filename, name, top, time)

def getHomeDirFromFile(file):
    return str(Path(file).parent.absolute())

def release(fn):
    time = default_timer()

    if findDir:
        drt = getHomeDirFromFile(sys.argv[2])
        compiler.preConsts["HOME_DIR"] = f'r"{drt}"'
        top = 'package pathlib:import Path;new dynamic HOME_DIR=str(Path(__file__).parent.absolute());del Path;'

    from ianthe import Ianthe
    ianthe = Ianthe(sys.argv[2])
    try:    _ = ianthe.config
    except: quit()

    name = os.path.basename(os.path.basename(ianthe.config["source"])).split(".")[0]
    for char in ILLEGAL_CHARS:
        name = name.replace(char, "_")

    ianthe.config["source"] = os.path.abspath(ianthe.config["source"])

    if "destination" in ianthe.config:
          ianthe.config["destination"] = os.path.abspath(ianthe.config["destination"])
    else: ianthe.config["destination"] = getHomeDirFromFile(ianthe.config["source"])
    dst = ianthe.config["destination"]

    curr = getHomeDirFromFile(__file__)
    os.chdir(curr)
    before = set(os.listdir(curr))

    compiler.preConsts["RELEASE_MODE"] = "True"

    filename = fn(compiler, ianthe.config["source"], "opal_program", name, top, time, True)
    if filename is not None:
        if "hidden-imports" in ianthe.config:
              ianthe.config["hidden-imports"] = list(set(ianthe.config["hidden-imports"]) | PY_STDLIB)
        else: ianthe.config["hidden-imports"] = list(PY_STDLIB)

        if "keep" in ianthe.config:
              ianthe.config["keep"] = list(set(ianthe.config["keep"]) | PY_STDLIB)
        else: ianthe.config["keep"] = list(PY_STDLIB)

        if "collect" in ianthe.config:
            if "all" in ianthe.config["collect"]:
                  ianthe.config["collect"]["all"]  = list(set(ianthe.config["collect"]["all"] + RELEASE_COLLECT) | PY_STDLIB)
            else: ianthe.config["collect"]["all"]  = list(set(RELEASE_COLLECT) | PY_STDLIB)
        else:     ianthe.config["collect"] = {"all": list(set(RELEASE_COLLECT) | PY_STDLIB)}

        if "icon" not in ianthe.config:
            ianthe.config["icon"] = str(os.path.join(curr, "runner", "icon.ico"))

        if fn is compilePy: ianthe.config["scan"] = False

        ianthe.config["source"] = os.path.abspath(filename)
        ianthe.execute()

        for module in compiler.imports:
            if module not in NO_INSTALL: subprocess.run([
                sys.executable, "-m", "pip", "install", "--isolated", "--exists-action", "w", 
                f"--target={str(os.path.join(dst, name))}", module, 
            ])

        os.chdir(curr) 
        for file in set(os.listdir(curr)) - before: 
            os.chmod(file, 0o777)
            os.remove(file)

        print("Compilation finished. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
        quit()
    print("Compilation failed.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"opal compiler v{'.'.join([str(x) for x in VERSION])} - thatsOven")
    else:
        compiler = Compiler().initMain()
        compiler.handleArgs(sys.argv)
        compiler.preConsts["RELEASE_MODE"] = "False"

        if "--debug" in sys.argv:
            debug = True
            sys.argv.remove("--debug")
        else: debug = False

        if "--dir" in sys.argv:
            findDir = False
            idx = sys.argv.index("--dir")
            sys.argv.pop(idx)

            drt = sys.argv.pop(idx)
            compiler.preConsts["HOME_DIR"] = f'r"{drt}"'
            top = 'new dynamic HOME_DIR=r"' + drt + '";'
        else:
            findDir = True

        if sys.argv[1] == "pyxcompile":
            if len(sys.argv) == 2:
                print('input file required for command "pyxcompile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = f'r"{drt}"'
                top = 'new dynamic HOME_DIR=r"' + drt + '";'

            name = os.path.basename(sys.argv[2]).split(".")[0]
            if len(sys.argv) == 3:
                compiler.compileToPYX(sys.argv[2], f"{name}.pyx", top)
            else:
                compiler.compileToPYX(sys.argv[2], sys.argv[3], top)

            if not compiler.hadError:
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
        elif sys.argv[1] == "pycompile":
            if len(sys.argv) == 2:
                print('input file required for command "pycompile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = f'r"{drt}"'
                top = 'new dynamic HOME_DIR=r"' + drt + '";'

            name = os.path.basename(sys.argv[2]).split(".")[0]
            if len(sys.argv) == 3:
                compiler.compileToPY(sys.argv[2], f"{name}.py", top)
            else:
                compiler.compileToPY(sys.argv[2], sys.argv[3], top)

            if not compiler.hadError:
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
        elif sys.argv[1] == "compile":
            if len(sys.argv) == 2:
                print('input file required for command "compile"')
                sys.exit(1)

            time = default_timer()

            if findDir:
                drt = getHomeDirFromFile(sys.argv[2])
                compiler.preConsts["HOME_DIR"] = f'r"{drt}"'
                top = 'new dynamic HOME_DIR=r"' + drt + '";'

            name = os.path.basename(sys.argv[2]).split(".")[0]
            for char in ILLEGAL_CHARS:
                name = name.replace(char, "_")

            if compileNormal(compiler, sys.argv[2], name, name, top, time, False):
                print("Compilation was successful. Elapsed time: " + str(round(default_timer() - time, 4)) + " seconds")
                quit()
            print("Compilation failed")
        elif sys.argv[1] == "build":
            libs = os.path.join(getHomeDirFromFile(__file__), "libs")
            os.chdir(libs)

            ok = compileOne(libs, "std.opal", compiler)
            if not ok:
                print("Compilation failed")
                quit()

            for file in os.listdir(libs):
                if file.endswith(".opal") and not file in ("helpers.opal", "std.opal"):
                    ok = compileOne(libs, file, compiler)

                    if not ok:
                        print("Compilation failed")
                        break

            if os.path.exists("build"): shutil.rmtree("build")

            if ok:
                os.chdir(os.path.join(getHomeDirFromFile(__file__), "runner"))
                import opal.runner.build
        elif sys.argv[1] == "release":
            if len(sys.argv) == 2:
                print('input file required for command "release"')
                sys.exit(1)

            release(compileNormal)
        elif sys.argv[1] == "pyrelease":
            if len(sys.argv) == 2:
                print('input file required for command "pyrelease"')
                sys.exit(1)

            release(compilePy)
        elif sys.argv[1] == "path":
            print(getHomeDirFromFile(__file__))
        else:
            sys.argv[1] = sys.argv[1]
            if not os.path.exists(sys.argv[1]):
                print('unknown command or nonexistent file "' + sys.argv[1] + '"')
                sys.exit(1)

            if findDir:
                drt = getHomeDirFromFile(sys.argv[1])
                compiler.preConsts["HOME_DIR"] = f'r"{drt}"'
                top = 'new dynamic HOME_DIR=r"' + drt + '";'

            result = compiler.compileFile(sys.argv[1], top)
            if not compiler.hadError: 
                sys.argv = sys.argv[1:]
                exec(result)
