#!/usr/bin/env bash

export GC_BASE_DIR=`pwd`
export GC_CODE_DIR="$GC_BASE_DIR/src"
export GC_DATA_DIR="$GC_BASE_DIR/data"
export GC_BIN_DIR="$GC_BASE_DIR/bin"

export LD_LIBRARY_PATH=$GC_BASE_DIR/lib64
export PYTHONPATH=$GC_CODE_DIR:$PYTHONPATH

export GCTIMER_LOG=on
export GCTIMER_LOGFILE="/tmp/gctimer.log"
