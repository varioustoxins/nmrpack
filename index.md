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
        
# Information for specific packages

Some packages need extra information to install them b ecause they live on password proitected sites. This process will improve as the code base improves.
This includes ARIA2 CNS and xplor-nih. For these packages you need to register and get a username and password. Then fill in your username and password in the file file login_data_template.yml, replacing <YOUR-USERNAME> and <YOUR-PASSWORD> with the usernames and passwords sent to you. You should end up with something like the following [noot real data!].

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


