#!/bin/bash

tag="V0.1.5"

docker build --platform linux/amd64 -t wenjin27/egh:$tag -t wenjin27/egh:latest  ./

docker tag wenjin27/egh:latest 174329956306.dkr.ecr.us-east-1.amazonaws.com/egh:latest
docker tag wenjin27/egh:latest 174329956306.dkr.ecr.us-east-1.amazonaws.com/egh:$tag

docker push 174329956306.dkr.ecr.us-east-1.amazonaws.com/egh:latest
docker push 174329956306.dkr.ecr.us-east-1.amazonaws.com/egh:$tag

#docker push wenjin27/egh:$tag
#docker push wenjin27/egh:latest

# docker run -p 10981:10981 wenjin27/egh

