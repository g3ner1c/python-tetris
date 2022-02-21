#!/bin/sh

PATH_DOCS=$(realpath $(dirname $0))
PATH_PROJ=$(realpath $PATH_DOCS/..)

rm -r $PATH_DOCS/build
mkdir $PATH_DOCS/build

cp $PATH_DOCS/logo.png $PATH_DOCS/build
cp $PATH_DOCS/favicon.ico $PATH_DOCS/build

pdoc -o $PATH_DOCS/build \
     -t $PATH_DOCS \
     -d numpy \
     --logo /logo.png \
     $PATH_PROJ/tetris
