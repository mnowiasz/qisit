# Installation
:warning: Be warned - currently Qisit is not exactly production ready. I'm using it myself productively, but I *strongly* 
recommend backing up Qisit's db regularly (I'm doing it myself). Since it's
quite early in it's development stage there might be bugs.

There's also a very, *very* crude main function: The first time you start
the program it will create an initialize an empty database in your home directory ("qisit.db")

Having said that, the current - easiest way - to install it is using virtualenv (install it if if necessary):

### Linux and Mac OS X
1. Create a new virtualenv in the console: `virtualenv --system-site-packages qisit` (qisit is an example)
2. Enter the virtualenv: `cd qisit; source bin/activate`
3. clone the repo into it - something like `git clone https://github.com/mnowiasz/qisit.git` 
4. Switch branches if necessary
5. `cd qisit` (the directory you cloned into) and  `pip install src/`
6. After that you should be able to start qisit by entering `qisit`

### Windows
It's the same as described above, although you might have to install python, git and virtualenv somehow 
(I recommand doing it by using [chocolatey](https://www.chocolatey.org/chocolatey).
Use a shell (I myself prefer PowerShell in Windows Terminal):
1. Create a new virtualenv in the console: `virtualenv --system-site-packages qisit` (qisit is an example)
2. Enter the virtualenv: `cd qisit;  .\Scripts\activate`

3.-6.: See above

It will have a better installer, for the moment this works for Linux, Windows and Mac OS X using the virtualenv approach.
Eventually there will be an installer.

