#!/usr/bin/env bash

python ./setup.py build && python ./setup.py install && cd test &&  python ./test_gcsynth.py  && cd ../
