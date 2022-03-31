from PyInstaller.__main__ import run
from distutils.dir_util   import copy_tree
from shutil               import rmtree
from pathlib              import Path
from os                   import chdir, path, getcwd, remove

spath = str(Path(__file__).parent.absolute())
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

chdir("..")
copy_tree(path.join(spath, "run"), getcwd())

chdir(spath)
rmtree("run")