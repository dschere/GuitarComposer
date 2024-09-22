#!/usr/bin/env bash

source ./build.env
python ./setup.py build && python ./setup.py install && cd test &&  python ./test_gcsynth.py  && cd ../

# Uncomment to check linking
#ldd  build/lib.linux-x86_64-cpython-311/gcsynth.cpython-311-x86_64-linux-gnu.so  | grep fluid