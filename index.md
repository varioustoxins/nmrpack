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

4. move the NMRPack installation file to where you want to save it (I use ~/programs/NMRPack) and expand it 
```bash
 mv ~/Downloads/nmrpack-master.zip .
 unzip nmrpack-master.zip
 mv nmrpack-master nmrpack
 rm nmrpack-master.zip
```
5. 
