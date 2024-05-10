from distutils.dir_util   import copy_tree
from shutil               import rmtree
from os                   import chdir, path, getcwd, remove
from ianthe               import Ianthe

spath = getcwd()

with open("opal.py", "w") as script:
    script.write("from subprocess import run\nfrom sys import argv\n")
    chdir("..")
    p = path.join(getcwd(), '__main__.py').replace("\\", "\\\\")
    script.write(f"run([sys.executable, '{p}'] + argv[1:])")

chdir(spath)

ianthe = Ianthe()
ianthe.config = {
    "source"     : "opal.py",
    "destination": "run",
    "onefile"    : True,
    "icon"       : "icon.ico"
}

ianthe.execute()

remove("opal.py")

chdir("..")
copy_tree(path.join(spath, "run"), getcwd())

chdir(spath)
rmtree("run")
