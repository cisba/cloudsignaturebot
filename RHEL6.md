
## Easy setup with virtualenv on AWS RHEL 6

```
sudo yum install python34
sudo bash -c "curl https://bootstrap.pypa.io/get-pip.py | python3.4"
sudo pip3 install virtualenvwrapper

echo "export WORKON_HOME=~/Envs" >> ~/.bashrc
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
echo "source /usr/bin/virtualenvwrapper.sh" >> ~/.bashrc
source ~/.bashrc

git clone git@github.com:cisba/cloudsignaturebot 
```
