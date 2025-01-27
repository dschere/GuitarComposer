#!/usr/bin/env bash

source ./build.env
# gdb -batch -ex "run" --args <executable> <arg1> <arg2> ...
python ./setup.py build && python ./setup.py install && cd test && \
    gdb -batch -ex "run" --args python ./test_events.py  && cd ../

# Uncomment to check linking
#ldd  build/lib.linux-x86_64-cpython-311/gcsynth.cpython-311-x86_64-linux-gnu.so  | grep fluidpython ./test_gcsynth.py
