from subprocess import run
from sys        import argv

run(["python", "opalc.py"] + argv[1:])