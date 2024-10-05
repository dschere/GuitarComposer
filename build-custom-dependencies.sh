#!/usr/bin/env bash

set -e

# builds custom dependencies 
#   fluidsynth gives me 95% of what I want but I needed a clean way to setup a filter chain
#   on a per channel basis. I created a modified version of fluidsynth to accomplish this.

# build and install our version of fluidsynth
cd ./dep
rm -rf gc_fluidsynth
git clone git@github.com:dschere/gc_fluidsynth.git
cd ./gc_fluidsynth
mkdir build
cd build
cmake --install-prefix=`pwd`/../../../    ../
make
make install
cd ../../
#rm -rf ./gc_fluidsynth
cd ../
