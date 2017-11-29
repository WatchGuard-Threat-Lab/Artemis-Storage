Artemis-Storage
===============
Artemis is a python-based honeypot system built using several open source tools.
Artemis-Storage uses the hpfeeds protocol to receive files from honeypot servers
and honeyclients. Artemis-Storage is based on mnemosyne
(https://github.com/johnnykv/mnemosyne)

Artemis has been released uner the GNU GPLv3, as published by the FSF.

Installation
============
Artemis-Storage requires a MySQL database for metadata storage, either locally or network-accessible.
```
apt-get install python python-dev mysql-client libmysqlclient-dev libev-dev build-essential libssl-dev libffi-dev curl ca-certificates python-pip

update-ca-certificates

cd opt
git clone https://github.com/WatchGuard-Threat-Lab/Artemis-Storage.git
cd Artemis-Storage
python setup.py install
```

Setup
=====
Edit data/prototype/config/config.conf to configure MySQL settings and broker credentials
```
python artemis.py start
```

