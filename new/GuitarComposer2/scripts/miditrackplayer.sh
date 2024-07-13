#!/usr/bin/env bash

export PORT=$1
export SF_FILE=$2

exec fluidsynth -a alsa -i -s \
    -o synth.ladspa.active=1 \
    -o synth.effects-groups=6 \
    -o "shell.port=$PORT" \
    $SF_FILE 
