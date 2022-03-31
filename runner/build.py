from PyInstaller.__main__ import run
from distutils.dir_util   import copy_tree
from shutil               import rmtree
from pathlib              import Path
from os                   import chdir, path, getcwd, sep, pardir

run((
    "--onefile",
    "--icon=icon.ico",
    "--workpath=tmp",
    "--distpath=run",
    "--specpath=tmp",
    "--clean",
    "run.py"
))

rmtree("tmp")
rmtree("__pycache__")

spath = str(Path(__file__).parent.absolute())
cwd   = getcwd()

chdir(path.normpath(cwd + sep + pardir))
copy_tree(path.join(spath, "run"), cwd)

chdir(spath)
rmtree("run")