## NMRPack

NMRPack is is a collection of installers and tools based on [Spack](https://spack.io) which helps with installing Biological NMR Software on unix like platforms (MacOS in the future Linux and Windows WSL).

Packages that are currently supported include

* NMRPipe
* SMILE
* ARIA2 (including GUI components)
* Xplor-NIH
* TALOS
* MARS 
* Pales (32 bit only)
* CNS (@1.21 including ARIA patches)

# Installing NMRPack

---
**NOTE**

This is an early version of NMRPack and it is still rough round the edges

---

1. Download the installer file https://raw.githubusercontent.com/varioustoxins/nmrpack/master/installer/installer.sh
2. if need be make it exceutable 
   ```bash
   chmod u+x  Downloads/installer.sh
   ```
3. run it 
   ```bash
   Downloads/installer.sh
   ```
4. If you are happy with the questions answer y
5. Install something
    ```bash
    spack install nmrpipe
    ```
6. Check NMRPipe runs
    ```bash
    spack load nmpipe
    nmrPipe
    ```
    should give
    ```bash
    ** NMRPipe System Version 10.9 Rev 2020.219.15.07 64-bit **
    ```
# Installing software

* To list installable software from nmr pac ktype 

```bash
spack list -d nmrpack
```
if you fon't include the -d nmrpack it will list all the other installable software provided by spack

* To install software type

```bash
spack install <PACKAGE-NAME>
```

where <PACKAGE-NAME> can be something like nmrpipe or xplor
   
* To use a package after installing it

before using a package you need to load it
 
```bash
   spack load <PACKAGE-NAME>
   ```
   
where <PACKAGE-NAME> can be something like xplor or mars
   
this process needs to be repeated each time you use the software, but you can add it to you .cshsrc or .bash_profile or .zashenv file
   
* to unload a package 

```bash
   spack unload <PACKAGE-NAME>
   ```

* to uninstall a package

   ```bash
   spack uninstall <PACKAGE-NAME>
   ```

where <PACKAGE-NAME> can be something like pales
   
# Information for specific packages

Some packages need extra information to install them b ecause they live on password proitected sites. This process will improve in future versions.
This includes ARIA2 CNS and xplor-nih. For these packages you need to register and get a username and password. Then fill in your username and password in the file file login_data_template.yml, replacing <YOUR-USERNAME> and <YOUR-PASSWORD> with the usernames and passwords sent to youand save its as login_data.yaml. You should end up with something like the following ~[not real usernames and passwords!]~.

```yaml

aria:
  user_name: varioustoxins
  password: wibble1

cns:
  user_name: varioustoxins
  password: wobble2

xplor:
  user_name: varioustoxins
  password: toodlypip3
```

then when installing xplor, cns or aria add the extra parameter configuration=login_data.yaml

so for xplor you would use

```bash
   spack install xplor configuration=login_data.yaml
   ```

   be aware that the CNS password runs out every week on saturday pm!


