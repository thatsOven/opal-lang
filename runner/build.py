from PyInstaller.__main__ import run
from distutils.dir_util   import copy_tree
from shutil               import rmtree, copy
from pathlib              import Path
from os                   import chdir, path, getcwd, remove, mkdir

spath = str(Path(__file__).parent.absolute())
chdir(spath)

with open("run.py", "w") as script:
    script.write("from subprocess import run\nfrom sys import argv\n")
    chdir("..")
    p = path.join(getcwd(), 'opalc.py').replace("\\", "\\\\")
    script.write(f"run(['python', '{p}'] + argv[1:])")

chdir(spath)

mkdir("tmp")
copy("icon.ico", path.join("tmp", "icon.ico"))

run((
    "--onefile",
    "--icon=icon.ico",
    "--workpath=tmp",
    "--specpath=tmp",
    "--distpath=run",
    "--clean",
    "run.py"
))

remove("run.py")

rmtree("tmp")

if path.exists("__pycache__"):
    rmtree("__pycache__")

chdir("..")
copy_tree(path.join(spath, "run"), getcwd())

chdir(spath)
rmtree("run")
