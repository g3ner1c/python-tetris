#!/bin/sh

PATH_DOCS=$(realpath $(dirname $0))
PATH_PROJ=$(realpath $PATH_DOCS/..)

rm -r $PATH_DOCS/build
pdoc -o $PATH_DOCS/build -d numpy $PATH_PROJ/tetris
