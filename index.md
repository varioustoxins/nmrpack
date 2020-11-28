## NMRPack

NMRPack is is a collection of installers based on [Spack](https://spack.io) which helps with installing Biological NMR Software currently on unix like platforms (Linux, MacOS  and Windows WSL).

Packages that are currently supported include

* NMRPipe
* SMILE
* TALOS
* CNS (@1.21 including ARIA patches)

# Using NMRPack

---
**NOTE**

This is a very early version of NMRPack and this is all *very* rough round the edges

---

1. Download Spack [using this link](https://github.com/spack/spack/archive/develop.zip) or

   or alternatively using curl
   
   ```bash
   curl -L https://github.com/spack/spack/archive/develop.zip -o ~/Downloads/develop.zip
   ```
   or using wget

   ```bash
   wget  -O ~/Downloads/develop.zip  https://github.com/spack/spack/archive/develop.zip 
   ```
   
2. Make a place to keep it (I use ~/programs/spack), move it there and expand it

   ```bash
   cd ~/programs
   mv ~/Downloads/develop.zip spack-develop.zip
   unzip spack-develop.zip
   mv spack-develop spack
   rm spack-develop.zip
   ```

3. setup spack in this terminal after which it should now be possible to run spack

   in bash / zsh
   ```bash 
   $ . ~/programs/spack/share/spack/setup-env.sh
   ````
   in csh
   ```tcsh
   $ source ~/programs/spack/share/spack/setup-env.csh
   ```
   now test it works
   ```bash
    $ spack
   ```
   this should now give
   ```bash
   usage: spack [-hkV] [--color {always,never,auto}] COMMAND ...

       A flexible package manager that supports multiple versions,
       configurations, platforms, and compilers.

       These are common spack commands:

       query packages:
       list                  list and search available packages
       ...
   
   ```
       

4. Download NMRPack [using this link](https://github.com/varioustoxins/nmrpack/archive/master.zip)
   
    or alternatively using curl
    
    ```bash
    curl -L https://github.com/varioustoxins/nmrpack/archive/master.zip -o ~/Downloads/master.zip
    ```
    or using wget
    
    ```bash
    wget  -O ~/Downloads/master.zip https://github.com/varioustoxins/nmrpack/archive/master.zip  
    ```
5. Move the NMRPack installation file to where you want to save it (I use ~/programs/NMRPack) and expand it 
    
    ```bash
    mv ~/Downloads/master.zip nmrpack-master.zip
    unzip nmrpack-master.zip
    mv nmrpack-master nmrpack
    rm nmrpack-master.zip
    ```

6. Add NMRPack as a spack repo
   ```bash
   spack repo add ~/programs/nmrpack
   ```
 
7. Check you have added NMRPack to spack
   ```bash
   $ spack repo list
        ==> 2 package repositories.
        nmrpack    /Users/gst9/Dropbox/git/nmrpack
        builtin    /Users/gst9/programs/spack-test/var/spack/repos/builtin
   ```
        

8. Install the modules system
    ```bash
    spack install environment-modules
   ```
   this may take a while as it has to compile Tcl


9. Load environment-modules
    ```bash
    . ~/programs/spack/share/spack/setup-env.sh
    spack load environment-modules
    ```

10. Install something
    ```bash
    spack install nmrpipe
    ```
 
11. Use modules to load the installed program
    ```bash
    eval   "`${HOME}/programs/spack/bin/spack  module tcl loads nmrpipe`"
    ```

12. Check NMRPipe runs
    ```bash
    $ nmrPipe
    ```
    should give
    ```bash
    ** NMRPipe System Version 10.9 Rev 2020.219.15.07 64-bit **
    ```
        

13. Unload NMRPipe
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
        
