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


#echo "Please enter soure machine Password: "
#read -sr src_PASSWORD_INPUT
#export OS_PASSWORD=$src_PASSWORD_INPUT
#
#echo "Please enter destination machine Password: "
#read -sr dst_PASSWORD_INPUT
#export OS_PASSWORD=$dst_PASSWORD_INPUT

ssh-keygen -t -rsa -N ""
scp ~/.ssh/id_rsa.pub vagrant@192.168.50.4:~
ssh vagrant@192.168.50.4
# ssh into destination
cd $HOME
cat id_rsa.pub >> .ssh/authorized_keys
