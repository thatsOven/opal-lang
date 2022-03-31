from PyInstaller.__main__ import run
from distutils.dir_util   import copy_tree
from shutil               import rmtree
from pathlib              import Path
from os                   import chdir, path, getcwd, remove

spath = str(Path(__file__).parent.absolute())
chdir(spath)

with open("run.py", "w") as script:
    script.write("from subprocess import run\nfrom sys import argv\n")
    chdir("..")
    p = path.join(getcwd(), 'opalc.py').replace("\\", "\\\\")
    script.write(f"run(['python', '{p}'] + argv[1:])")

chdir(spath)

run((
    "--onefile",
    "--icon=icon.ico",
    "--workpath=tmp",
    "--distpath=run",
    "--clean",
    "run.py"
))

rmtree("tmp")
rmtree("__pycache__")
remove("run.spec")
remove("run.py")

chdir("..")
copy_tree(path.join(spath, "run"), getcwd())

chdir(spath)
rmtree("run")
