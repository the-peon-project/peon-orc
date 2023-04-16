#!/bin/bash
function do_docker_build(){
    cd $dockerfile_path
    if [[ $version ]];
    then
        sed -i "18s/.*/                         ┃                  version: $version                  ┃/" $dockerfile_path/media/banner
        docker build --build-arg VERSION="$version" -t $container_tag:$version .
        docker tag $container_tag:$version $container_tag:latest
    else
        printf "Version number required.\n\te.g.\t$0 1.0.2\n"
        printf "Exisiting images are:\n"
        docker image list | grep $container_tag
    fi
}
version=$1
dockerfile_path="$(dirname "$(dirname $0)")"
container_tag="umlatt/peon.orc"
do_docker_build