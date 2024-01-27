#!/usr/bin/env bash

#export LD_LIBRARY_PATH=/usr/local/lib64

export LD_LIBRARY_PATH=/home/david/proj/fluidsynth/build/src

gcc -g3 -O0  src/*.c -Isrc/ -o bin/gsynth `pkg-config --cflags fluidsynth` \
  /home/david/proj/fluidsynth/build/src/libfluidsynth.so
