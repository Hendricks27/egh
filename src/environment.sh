#!/bin/bash

apt update
apt-get install -y libncurses-dev libbz2-dev liblzma-dev tabix
apt-get install zip
apt-get install unzip

chmod -R 0777 ./
mkdir /data
chmod -R 0777 /data

mkdir /data/config

python fixenv.py
