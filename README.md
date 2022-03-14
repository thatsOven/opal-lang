![](https://cdn.discordapp.com/attachments/724718756713988187/814628164256137266/unknown.png)thanks to aphitorite for the beautiful logo!
    
# opal 
opal is a WIP transcompiled programming language based on Python. 
NOTE: It doesn't work perfectly, it still has some problems.
# Compiler usage
[ ] = optional
* To compile to a `.py` file: `opalc.py pycompile input_file [output_file]`
* To compile to a `.pyc` file: `opalc.py compile input_file [output_file]`
* To directly run opal source: `opalc.py file_name`

add `--dynamic` to the arguments to ignore types in the compiled result (results in better performance)

# Hello World!
```
package opal: import *;

main {
    IO.out("Hello World!\n");
}
```
