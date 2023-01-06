#!/bin/bash

apt update
apt-get install -y libncurses-dev libbz2-dev liblzma-dev tabix
apt install chromium-chromedriver
apt-get install zip unzip


chmod -R 0777 ./
mkdir /data
chmod -R 0777 /data

mkdir /data/config

python fixenv.py
