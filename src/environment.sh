#!/bin/bash

apt update
apt install chromium-chromedriver
apt-get install tabix

chmod -R 0777 ./
mkdir /data
chmod -R 0777 /data

mkdir /data/config

python fixenv.py
