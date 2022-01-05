#!/usr/bin/env sh
# copied from spack...
. spack/share/spack/setup-env.sh
mkdir -p spack/etc/spack
echo -e "config:\n  build_jobs: 2" > spack/etc/spack/config.yaml
spack config add "packages:all:target:[x86_64]"
# TODO: remove this explicit setting once apple-clang detection is fixed
cat <<EOF > spack/etc/spack/compilers.yaml
compilers:
- compiler:
    spec: apple-clang@11.0.3
    paths:
      cc: /usr/bin/clang
      cxx: /usr/bin/clang++
      f77: /usr/local/bin/gfortran-9
      fc: /usr/local/bin/gfortran-9
    modules: []
    operating_system: catalina
    target: x86_64
EOF
spack compiler info apple-clang
spack debug report