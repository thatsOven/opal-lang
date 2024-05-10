![](logo.png)thanks to aphitorite for the beautiful logo!
    
# opal 
opal is a transcompiled programming language based on Python and Cython. 

# Installation
To install opal on your machine, execute these commands:
```
pip install opal-lang
python -m opal build
```

Note that you might need to install a C compiler, as Cython will be installed as a dependency.

On Windows, after the building process is complete, it's possible to add the opal folder to PATH to have a global `opal` executable.

# Compiler usage
[ ] = optional
* To compile to a Python `.py` file: `opal pycompile input_file [output_file]`
* To compile to a Cython `.pyx` file: `opal pyxcompile input_file [output_file]`
* To compile to a Cython module: `opal compile input_file [output_file]`
* To compile to an executable: `opal release build_file` or `opal pyrelease build_file` (if the program is `--nocompile`). Note that this requires an internet connection to fetch and install dependencies to the target. An opal build file is structured like a [ianthe project file](https://github.com/thatsOven/ianthe);
* To directly run opal source: `opal file_name`
# Command line arguments
- `--type-mode`
	- Selects a default typing mode for the file. Options are:
		- `hybrid`: The default one. Forces the type when it doesn't create problems, checks otherwise;
		- `check`: Checks types. Some conversions won't be automatic (for example, assigning a `tuple` to a `list` typed variable won't convert it automatically);
		- `force`: Always forces types. Can break programs as forced typing can't always be performed;
		- `none`: Uses dynamic typing for all variables.
	- **Usage**: --type-mode mode
- `--disable-notes`
	- Disables notes during compilation
	- **Usage**: --disable-notes
- `--dir`
	- Specifies a custom `HOME_DIR` variable.
	- **Usage**: --dir path
- `--static`
	- Treats every variable as it cannot change types. Useful for optimization purposes.
	- **Usage**: --static
- `--nostatic`
	- Specifies that a program cannot be compiled with the `--static` flag. It's not meant to be used via terminal.
- `--nocompile`
	- Specifies that a program cannot be compiled. Useful for programs that use Python features that are not included in Cython. It's not meant to be used via terminal.
- `--require`
	- Specifies a minimum version of opal that the program requires to run. It's not meant to be used via terminal.
- `--compile-only`
	- Specifies that a program can only be compiled. Useful for programs that use Cython instructions or features. It's not meant to be used via terminal.
- `--module`
	- Specifies that a program is a module. It's not meant to be used via terminal.
- `--debug`
	- Saves the Cython annotations file when compiling for debugging purposes.
	- **Usage**: --debug
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

# this only defines the variable
new str name;

# var can accept any type
new dynamic var;
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
new function functionName(arg0: int, arg1: str) {
	# your code here
}
```
... default arguments can be defined...
```
new function functionName(arg0: int = 2 + 2, arg1 = "hi") {
	# your code here
}
```
... and return types can be specified.
```
new function add(a: int, b: int) int {
	return a + b;
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
Records can also inherit from classes, using the following syntax:
```
new class ParentClass {}

new record RecordName(arg0, arg1, arg2) <- ParentClass;
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

NOTE: since Cython doesn't support Python's `match` statement, opal will always fall back to the `elif` chain implementation when compiling.
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
### `use`
Creates an identifier. This is necessary as every identifier mentioned at the beginning of an expression statement must be known at compile-time.
For example:
```
new function a(x) {
	b(x - 1);
}

new function b(x) {
	if x < 2 {
		a(x);
	}
}
```
Here, the compiler will give us an error:
```
error (in test.opal: a(), line 2, pos 4): unknown statement or identifier
 1 | new function a(x) {
 2 |     b(x - 1);
   |     ^
 3 | }
 4 | 
 5 | new function b(x) {
```
To solve this, we can create the identifier ourselves:
```
use b;

new function a(x) {
	b(x - 1);
}

new function b(x) {
	if x < 2 {
		a(x);
	}
}
```
### `namespace`
Creates a namespace. Effectively just a class that can't inherit from other classes and can't be instantiated.
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
### `unchecked`
The `unchecked` flag is used to ignore typing on an assignment or skip checks on other statements. Statements to which the `unchecked` flag can be applied are:
- `repeat`: skips the conversion to an absolute int;
- `return`: ignores type checking.
Example:
```
new int a = 2 + 2;
unchecked: a += 2;

unchecked: repeat a {
	# your code here
}

new function add(a: int, b: str | int) int {
	if type(b) is int {
		unchecked: return a + b;
	}

	return str(a) + b;
}
```
### `static`
The `static` flag is used to indicate whether a variable or a block of variables will not change type. This is used to apply optimizations during compilation. Example:
```
static {
	new int a;
	new float b = 2.0;
}

static: new int c = 3;

static:
new function myFunction() {
	# every variable here will be static
}

static:
namespace Test {
	# every variable here will be static
}
```
### `inline`
The `inline` flag tries to inline an optimizable function during compilation. The compiler will throw an error if the function to be inlined is not optimizable.
```
inline:
new function add(a: int, b: int) int {
	return a + b;
}
```
### `global`
The `global` flag is used to declare an object in the global scope. 
```
new function aFunction() {
	global: new int a = 2, b = 3;

	global:
	new function anotherFunction() {
		# do something
	}
}

# a, b, and anotherFunction will be visible here with a "use" statement
```
### Python equivalents
Some statements are direct equivalents of Python statements or functions. Here's a list of opal statements that haven't been mentioned yet and their Python equivalents:
```
  opal   | Python
--------------------
async    | async
await    | await
with     | with
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
opal will automatically create some "pconstants" you can use:
- `HOME_DIR`: points to the base directory of the given file;
- `CY_COMPILING`: a `bool` that indicates whether the compiler is compiling in Cython mode;
- `RELEASE_MODE`: a `bool` that indicates whether the compiler is compiling in release mode;
- `TARGET_FILE`: a `str` that points to the file opal is generating. It's `None` when opal is directly running code.
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
Defines a macro. A macro is a basic function that gets called with no overhead, since its body is copy-pasted into calls. Avoid using this too often since it can quickly increase the result file size. The body of the macro is anything between the `$macro` statement and an `$end` statement. Macros can be defined with no arguments...
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
### `$if`
Exports a block of code (all the way until an `$end` statement) if a condition is `True`.
```
package opal: import *;

$define GREET_USER True
$if GREET_USER
	IO.out("Hi, user!\n");
$end
```
An `$else` statement is also available:
```
package opal: import *;

$define GREET_USER True
$if GREET_USER
	IO.out("Hi, user!\n");
$else
	IO.out("Sorry, user. No greeting this time :(\n");
$end
```

The same action can also be performed through the `comptime` statement, though it's much slower. `$if` is useful for both simplicity and faster compile times, especially when working with large blocks of code.
### `$comptime`
Defines a block of code (all the way until an `$end` statement) that will run during compilation. If an exception is thrown during this stage, the compiler will throw an error. In combination with the `$export` and `$exportBlock` statements, it can be used for conditional code generation. Example:
```
$define USE_CUPY False

$comptime
	if USE_CUPY {
		$export import cupy as numpy;
	} else {
		$exportBlock
			import numpy;
			?"running with numpy";
		$end
	}
$end
```

The `COMPTIME_EXPORT_VARS` global dictionary can be used to create variables that can be read by export blocks. For example:
```
$define ADDING_WATER_DROPLETS True

$comptime
	if ADDING_WATER_DROPLETS {
		$export new int ONE_PLUS_ONE = 1;
	} else {
		COMPTIME_EXPORT_VARS["onePlusOneResult"] = str(1 + 1);
		$export new int ONE_PLUS_ONE = onePlusOneResult;
	}
$end
```
### `$nocompile`
Tells the precompiler to directly transcribe code to the result until a `$restore` statement. In practice, it allows to use Python or Cython code inside opal. Code in `$nocompile`-`$restore` blocks should be put on a "null indentation", for example:
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
This is needed because opal will add to the base indentation an inferred indentation, that is based on the code logic. This allows to directly import Python or Cython source files with no syntax errors.
### `$embed`
Directly transcribes a line of code to the compiled result. Useful to avoid the `$nocompile`-`$restore` syntax for one-liners.
```
if a != b {
	if a < b {
		for i in range(a, b) {
			if i > 2 {
				$embed print(i)
			}
		}
	}
}
```
### `$args`
Passes the compiler some default arguments. Supported arguments are:
```
--static, --nostatic, --nocompile, --compile-only, --type-mode, --require
```
Example:
```
$args ["--static", "--type-mode", "check", "--require", "2023.11.9"]
```
### `$cy`
Creates Cython decorators if the compiler is transcompiling to Cython. Avoids errors when running a program in "Python mode". It uses the following syntax:
```
$cy flag_name value
```
and translates to:
```
@cython.flag_name(value)
```
... For example:
```
$cy nonecheck False
$cy cdivision True
inline:
new function divide(a: float, b: float) float {
	return a / b;
}
```
### `$cdef`
Applies the Cython `cdef` keyword to the next element when possible or forces a C definition on unknown types. For example:
```
$cdef
new function add(a: int, b: int) int {
	return a + b;
}

$embed from cpython.mem cimport PyMem_Malloc, PyMem_Free
new function mallocTest() {
	use PyMem_Malloc, PyMem_Free;

	$cdef
	new (int*) memory = <int*>PyMem_Malloc(20 * sizeof(int));
	
	memory[0] = 2;
	PyMem_Free(memory);
}
```
# Operators
Since opal directly passes expressions to Python, that is, it doesn't parse them, Python operators are all usable, with
a few additions:
- `!`: Equivalent to Python's `not`. If used at the beginning of a line with a variable name, it will invert the state of that variable:
```
!variable; # is equivalent to variable = !variable;

not variable; # this also produces the same result
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
