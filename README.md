![](https://cdn.discordapp.com/attachments/724718756713988187/814628164256137266/unknown.png)thanks to aphitorite for the beautiful logo!
    
# opal 
opal is a transcompiled programming language based on Python. 

NOTE: due to how the compiler works, it might not detect some syntax errors, especially in expressions.
# Compiler usage
[ ] = optional
* To compile to a `.py` file: `opalc.py pycompile input_file [output_file]`
* To compile to a `.pyc` file: `opalc.py compile input_file [output_file]`
* To directly run opal source: `opalc.py file_name`

# Command line arguments
- `--dynamic`
	- Ignores types in the compiled result. It gives a performance benefit, but it can break some programs that rely on type conversion.
	- **Usage**: --dynamic
- `--noeval`
	- Avoids evaluating constant expressions when defining new variables
	- **Usage**: --noeval
# Runner
if you are running Windows on your machine, and you'd like to double click on opal source to directly run it:

1) add the opal folder to `PATH`
2) build the runner using `runner\build.py`
3) set `opalrun.exe` as the default way of opening `.opal` files

# Hello World!
```
package opal: import *;

main {
    IO.out("Hello World!\n");
}
```

# Statements and keywords
## Defining new items - the `new` statement
The `new` statement uses the following syntax:
```
new itemType itemName
```
`new` will accept as types: 
- Python integrated types;
- Custom defined types;
- `dynamic`
- opal specific keywords.

Example:
```
# this defines the variable and assigns to it
new int aNumber = 2;

# this only defines the variable. note that 
# Python will not recognize this variable until
# it is assigned
new str name;

# var can accept any type
new dynamic var;

# putting type names in angular brackets tells the compiler
# not to force that type, and only check if assigments of the given
# type are made. it is recommended to use angular brackets whenever
# defining a variable that contains instances of a custom defined class
new <Vector> aVector = Vector(2, 3);
```

### opal specific keywords
#### `function`
Creates a function. Example:
```
new function functionName(arg0, arg1) {
	# your code here
}
```
The types of a function's parameter can be specified...
```
# typing in function parameters follow the same rules as 
# types in the new statement
new function functionName(arg0 : int, arg1 : <str>) {
	# your code here
}
```
... and default arguments can be defined.
```
new function functionName(arg0 : int = 2 + 2, arg1 = "hi") {
	# your code here
}
```
#### `class`
Creates a class. Example:
```
new class ClassName {
	# your code here
}
```
Classes can also inherit content from one or more parent classes:
```
new class ClassName : ParentClassA, ParentClassB {
	# your code here
}
```
#### `method`
Creates a method and passes it the `this` variable, which refers to the class the method is in. `this` is equivalent to Python's `self`. The syntax is the same as a normal function.
#### `staticmethod`
Creates a method with a `@staticmethod` decorator. The syntax is the same as a normal function.
#### `classmethod`
Creates a method with a `@classmethod` decorator, and passes it the `this` variable. The syntax is the same as a normal function.
#### `record`
Creates a basic class containing the specified properties. Example:
```
new record RecordName(arg0, arg1, arg2);
```

## Conditional statements
### `if`
`if` statements are equivalent to Python's:
```
if someCondition {
	# your code here
} elif someOtherCondition {
	# some other code here
} else {
	# do something else
}
```
### `match`
`match` statements have two implementations. The default one is equivalent to Python's `match` statement:
```
match aVariable {
	case aValue {
		# aVariable == aValue
	}
	case 2 {
		# aVariable == 2
	}
	default {
		# aVariable is not in any of the cases
		# the default statement should always be last
		# (or second to last in case a 
		# found statement is used)
	}
	found {
		# this code will execute if any of the cases is met
		# the found statement should always be last
	}
}
```
The other `match` implementation consists in an `elif` chain. It's accessible by specifying the operator to be used.
```
match:(!=) aVariable {
	# cases here
}
```
if no operator is specified (`match:()`), `==` will be used by default.
### Loops
#### `while`
```
while someCondition {
	# your code here
}
```
#### `do`
`do` statements implement a do-while loop:
```
do {
	# your code here
	
	# the condition will be checked at the end
	# of each iteration
} while someCondition;
```
This syntax is also valid and equivalent:
```
do someCondition {
	# your code here
}
```
#### `repeat`
Repeats code a certain amount of times. Can be either a constant or a variable.
```
repeat times {
	# repeating code
}
```
#### `for`
`for` loops can use either Python syntax...
```
for item in list {
	# do something
}

for i in range(0, 10) {
	# do something else
}
```
... or a C-like syntax:
```
for i = 0; i < 10; i++ {
	# do something
}
```
Variables in for loops don't have to be defined separately.

Any of these loops can use `break` and `continue` statements.
### Exception handling
opal's exception handling follows Python's syntax, with different keywords.
```
try {
	# something that might give an error
} 
# if a ValueError occurs, do nothing
ignore ValueError;
catch Exception as e {
	# something went wrong
} success {
	# no error occurred
	# you can also use the "else" keyword instead of "success"
}
```
To throw exceptions, you can use the `throw` statement, which is equivalent to Python's `raise`.
### Importing modules
```
import aModule;

package anotherModule: import item0 as myItem, item1;
# this is equivalent to:
# from anotherModule import item0 as myItem, item1

package aModule: import *;
# this is equivalent to:
# from aModule import *
```
### Classes
Class methods can be made abstract. if a class contains an abstract method, the class must be declared abstract as well:
```
abstract: new class AnAbstractClass {
	new method add(a, b) {
		return a + b;
	}
	
	abstract: new method anAbstractMethod();
}
```
#### `property`
You can create get-set methods for properties by creating a `property`:
```
new class MyClass {
	new method __init__(a) {
		this.a = a;
	}
	
	property myProperty {
		get {
			return this.a;
		}
		set {
			this.a = value;
	
			# the "value" variable name can be changed:
			# set(myValue) {
			#     this.a = myValue;
			# }
		}
		delete {
			del this.a;
		}
	}
}
```
Any of the methods can be omitted. For example, if the `set` method is not defined, the property will be read-only. Property methods can be set as abstract. A property method can also be defined outside of a `property` statement:
```
new class myClass {
	new method __init__(a) {
		this.a = a;
	}
	
	property myProperty {
		get {
			return this.a;
		}
		delete {
			del this.a;
		}
	}
	
	set<myProperty>(myValue) {
		this.a = myValue;
	}
}
```
### `main`
The `main` statement acts as syntax sugar for the form `if __name__ == "__main__":`.
```
main {
	# this code will only be executed if the script
	# is not imported
}

main() {
	# using brackets generates a main function.
	
	# defining one is not mandatory, but it's
	# generally good practice. only one main
	# function can be defined
}
```
### `unchecked`
The `unchecked` flag is used to ignore typing on an assignment or skip checks on other statements. Statements to which the `unchecked` flag can be applied are:
- `repeat`: skips the conversion to an absolute int;
- `match`: skips the steps necessary for the `found` clause to work.
Example:
```
new int a = 2 + 2;
unchecked: a += 2;

unchecked: repeat a {
	# your code here
}

unchecked: 
match a {
	case 6 {
		
	}
}
```
### `namespace`
Creates a namespace. Effectively just a class that can't inherit from other classes.
```
namespace MyNamespace {
	# your code here
}
```
### `enum`
Creates a set of variables contaning distinct constants:
```
enum MyEnum {
	CONST0, CONST1, CONST2
}

# MyEnum.CONST0 == 0
# MyEnum.CONST1 == 1
# ...
```
The values of each constant can be chosen when defining the `enum`:
```
enum MyEnum {
	CONST0 = "hi", 
	CONST1 = 2,
	CONST2 = 3.14
}
```
`enum`s can also be defined with no name. In that case, the constants get created as actual variables hidden behind no namespace:
```
enum {
	CONST0, CONST1, CONST2
}

# you can now access the variables directly
# for example:
new int myVariable = CONST0 + CONST1;
```
### Python equivalents
Some statements are direct equivalents of Python statements or functions. Here's a list of opal statements that haven't been mentioned yet and their Python equivalents:
```
  opal   | Python
--------------------
async    | async
await    | await
with     | with
quit     | quit()
super    | super()
del      | del
assert   | assert
yield    | yield
global   | global
external | nonlocal
```
opal supports decorators, using the same syntax as Python:
```
@myDecorator;
new function myFunction() {}
```
# Precompiler
## Comments
Comments are marked with the `#` symbol and extend until a newline is found.
## Statements
### `$define`
Defines a constant.
```
$define constantName constantContent
```
### `$pdefine`
Defines a constant that is only visible to the precompiler.
```
$pdefine constantName constantContent
```
opal will automatically create a `HOME_DIR` "pconstant" (and variable) that points to the base directory of the given file.
### `$include`
Includes a Python or opal file inside an opal file. Expects a `str` or path-like argument (it gets evaluated using Python's `eval`). Usage of the `os` module is allowed and recommended, especially to join directories and filenames.
```
$include os.path.join(HOME_DIR, "myFile.opal")
```
### `$includeDirectory`
Includes every `.py` and `.opal` file in a given directory. Expects a `str` or path-like argument.
```
$includeDirectory os.path.join(HOME_DIR, "myFolder")
```
### `$macro`
Defines a macro. A macro is a basic function that gets called with no overhead, since its body is copy-pasted into calls. Avoid using this too often since it can quickly increase the result file size. The body of the macro is anything between the `$macro` statement and an `$end` statement. Precompiler instructions cannot be used inside a macro definition. Macros can be defined with no arguments...
```
$macro sayHi
	IO.out("Hi!\n");
$end
```
... or with arguments. Arguments do not accept types and a default value cannot be set.
```
$macro add(a, b)
	new int result = a + b;
$end
```
Macros are called using the `$call` statement:
```
$call sayHi
$call add(2, 4)
```
### `$nocompile`
Tells the precompiler to directly transcribe code to the result until a `$restore` statement. In practice, it allows to use Python code inside opal. Python code in `$nocompile`-`$restore` blocks should be put on a "null indentation", for example:
```
if a != b {
	if a < b {
		$nocompile
		
for i in range(a, b):
	if i > 2:
		print(i)
		
		$restore
	}
}
```
This is needed because opal will add to the base indentation an inferred indentation, that is based on the code logic. This allows to directly import Python source files with no syntax errors.

# Operators
Since opal directly passes expressions to Python, that is, it doesn't parse them, operators are almost identical to Python's, with
a few additions:
- `!`: Equivalent to Python's `not`. If used at the beginning of a line with a variable name, it will invert the state of that variable:
```
!variable;

# is equivalent to:
# variable = !variable;
```

- `||`: Equivalent to Python's `or`;
- `&&`: Equivalent to Python's `and`;
- `?`: It's used for debugging purposes. It prints the given expression and returns it:
```
myFunction(a, ?(b), c); 
# the content of b will be printed

?c; 
# the content of c will be printed
```
- `<-`: It's used to convert variables to a type during an assignment:
```
new int a = 2;
# type of a is int

float <- a = 3;
# type of a is float

<str> <- a = str(a);
# type of a is str, and will now only be checked instead of forced

dynamic <- a = Vector(2, 3);
# type of a is dynamic
```
Typing used with the arrow operator follows the same rules as types in the new statement.
- `++` and `--`: They work as increments (respectively `+= 1` and `-= 1`). They are only allowed as statements, that is, 
they can't be used inside expressions. They can be used inside the first and last parts of a C-like for statement, and 
inside an inline type conversion (arrow operator). These syntaxes are all valid:
```
new int var = 0;
var++;
var--:

--var; # this "operator-first" syntax is only allowed as a statement alone, 
# that is, for example, it won't work in a for loop.
++var;

float <- var++;
```