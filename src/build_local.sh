#!/bin/bash

tag="V0.1.7"

# --platform linux/amd64
# --platform linux/arm64/v8
docker build -t wenjin27/egh:$tag -t wenjin27/egh:latest -f DockerfileLocal --platform linux/amd64 ./


docker push wenjin27/egh:$tag
docker push wenjin27/egh:latest

# docker run -p 10981:10981 wenjin27/egh

