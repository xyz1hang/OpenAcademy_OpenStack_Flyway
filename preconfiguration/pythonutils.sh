#!/bin/sh
sudo wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python
sudo apt-get install unzip
sudo unzip setuptools*.zip
sudo rm setuptools*.zip
cd setuptools*
sudo python setup.py install --prefix=/opt/setuptools
sudo apt-get install python-pip
sudo apt-get install build-essential libssl-dev libffi-dev python-dev
sudo apt-get install python-mysqldb
