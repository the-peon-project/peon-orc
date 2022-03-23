#!/bin/bash
version=$1
if [[ $version ]];
then
    docker build -t umlatt/peon.orc:$version .
else
    printf "Version number required.\ne.g.\t$0 1.0.2\n"
fi