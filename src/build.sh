#!/bin/bash

tag="V1.1.1"

docker build -t wenjin27/visfinal:$tag -t wenjin27/visfinal:latest ./

docker push wenjin27/visfinal:$tag
docker push wenjin27/visfinal:latest

# docker run -p 10981:10981 wenjin27/visfinal

