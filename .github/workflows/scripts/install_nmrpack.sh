
SPACK_VERSION=$(<.github/workflows/spack_version.txt)

curl -L https://github.com/spack/spack/releases/download/v${SPACK_VERSION}/spack-${SPACK_VERSION}.tar.gz -o spack.tar.gz
mkdir spack
tar --strip-components=1  -C spack -zxvf spack.tar.gz

. .github/workflows/install_spack.sh

curl -L https://github.com/varioustoxins/nmrpack/archive/master.zip -o nmrpack-master.zip
unzip nmrpack-master.zip
mv nmrpack-master nmrpack
. spack/share/spack/setup-env.sh
spack repo add nmrpack


