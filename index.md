## NMRPack

NMRPack is is a collection of installers based on [Spack](https://spack.io) which helps with installing Biological NMR Software currently on unix like platforms (Linux, MacOS  and Windows WSL).

Packages that are currently supported include

* NMRPipe
* SMILE
* TALOS

# Using NMRPack

1. Download Spack [using this link](https://github.com/spack/spack/archive/develop.zip) 
2. Make a place to keep it (I use ~/programs/spack), move it there and expand it

```bash
cd ~/programs
mv ~/Downloads/spack-develop.zip .
unzip spack-develop.zip
rm spack-develop.zip
. spack/share/spack/setup-env.sh
```
3. it should now be possible to run spack
```bash
(base) major:programs gst9$ spack
usage: spack [-hkV] [--color {always,never,auto}] COMMAND ...

A flexible package manager that supports multiple versions,
configurations, platforms, and compilers.

These are common spack commands:

query packages:
  list                  list and search available packages
  ...
```
4. Download NMRPack [using this link](https://github.com/varioustoxins/nmrpack/archive/master.zip)

4. Move the NMRPack installation file to where you want to save it (I use ~/programs/NMRPack) and expand it 
```bash
 mv ~/Downloads/nmrpack-master.zip .
 unzip nmrpack-master.zip
 mv nmrpack-master nmrpack
 rm nmrpack-master.zip
```
5. Add NMRPack as a spack repo
```bash
spack repo add ~/programs/NMRPack
```
6. Check you have added NMRPack to spack
```bash
$ spack repo list
==> 2 package repositories.
nmrpack    /Users/gst9/Dropbox/git/nmrpack
builtin    /Users/gst9/programs/spack-test/var/spack/repos/builtin
```
7. Install the modules system
```bash
spack install environment-modules
```
8. Load environment-modules
```bash
. ~/programs/spack/share/spack/setup-env.sh
```
9.Install something
```bash
spack install nmrpipe
```
10. Use modules to load the installed program
```bash
  eval   "`${HOME}/programs/spack/bin/spack  module tcl loads nmrpipe`"
```
11. Check NMRPipe runs
```bash
$ nmrPipe
** NMRPipe System Version 10.9 Rev 2020.219.15.07 64-bit **
```
12. Unload NMRPipe
```bash
$ module list

Currently Loaded Modulefiles:
 1) nmrpipe-2020.219.15.07-apple-clang-12.0.0-qk4fw2b
 
$ module list
Currently Loaded Modulefiles:
 1) nmrpipe-2020.219.15.07-apple-clang-12.0.0-qk4fw2b
 
$ module unload nmrpipe-2020.219.15.07-apple-clang-12.0.0-qk4fw2b

$ nmrPipe
-bash: nmrPipe: command not found
```
