#!/usr/bin/env bash

export SFONT_NAME="$GC_DATA_DIR/sf/$1"
export OUTFILE_DIR="$GC_DATA_DIR/sf_info"
export SF_CMD_FILE="$GC_BASE_DIR/scripts/print_instruments.fs"


#echo "$GC_BIN_DIR/fluidsynth -if $SF_CMD_FILE $SFONT_NAME > $OUTFILE"
$GC_BIN_DIR/fluidsynth -if $SF_CMD_FILE $SFONT_NAME 
