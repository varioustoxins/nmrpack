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
        
        
