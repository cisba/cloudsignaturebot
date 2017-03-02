# Cloud Signature Bot

This is a simple proof of concept implementing electronic signature within a bot.

The project rely on:
* Time4Mind (a platform of trust services for e-signature and strong authentication)
* Telegram (a chat service provider)
* Python language

## Requirements and Installation

* Python3 >= 3.4.2
* libraries: PyYaml, requests, python-telegram-bot
* a PkBox server to process document signatures locally
* Time4Mind ssl-client certificates to use webapi for strong authentication
* signature certificates issued for your users on the Time4Mind platform

This document assumes you are working on a Linux Box.

Libraries can be installed via `pip3 install` command.

The PkBox server, Time4Mind ssl certificates and the  end-user signature certificates are provided by [Intesi Group S.p.A.](http://www.intesigroup.com) as part of the services agreement, or requiring a trial license for developing purpose. This document assumes you already have a PkBox server installed and running. For the PkBox server installation see the product documentation. 

Time4Mind ssl certificates are provided as PKCS12 files. You have to extract from them the key and the certificate as two distinct files to use from python http library requests. To accomplish this use the following commands:
```
openssl pkcs12 -nodes -nocerts -in time4id.p12 -out time4id.key
openssl pkcs12 -nokeys -in time4id.p12 -out time4id.crt
openssl pkcs12 -nodes -nocerts -in time4id.p12 -out time4id.key
openssl pkcs12 -nokeys -in time4id.p12 -out time4id.crt
```

End user signature certificates are available at the [Intesi Group Store](https://store.intesigroup.com).

## Usage

Just run the command `python3 cloudsignaturebot.py time4mind.yml`

## Known Issues

None yet.
