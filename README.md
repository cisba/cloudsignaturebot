# Cloud Signature Bot

This is a simple proof of concept implementing electronic signature within a bot.

The project rely on:
* Time4Mind (a platform of trust services for e-signature and strong authentication)
* Telegram (a chat service provider)
* Python language

## Requirements and Installation

* Python3 >= 3.4.2
* $pip install PyYaml requests flask python-telegram-bot Zeep python-magic
* a PkBox server to process document signatures locally
* Time4Mind ssl-client certificates to use webapi for strong authentication
* signature certificates issued for your users on the Time4Mind platform

This document assumes you are working on a Linux Box, but obviously you can adapt everything to your preferred python enabled OS.

Libraries can be installed via `pip3 install` command.

The PkBox server, Time4Mind ssl certificates and the  end-user signature certificates are provided by [Intesi Group S.p.A.](http://www.intesigroup.com) as part of the services agreement, or requiring a trial license for developing purpose. This document assumes you already have a PkBox server installed and running. For the PkBox server installation see the product documentation. 

Time4Mind ssl certificates are provided as PKCS12 files. You have to extract from them the key and the certificate as two distinct files to use from python http library requests. To accomplish this use the following commands:
```
openssl pkcs12 -nodes -nocerts -in time4id.p12 -out time4id.key
openssl pkcs12 -nokeys -in time4id.p12 -out time4id.crt
openssl pkcs12 -nodes -nocerts -in time4user.p12 -out time4user.key
openssl pkcs12 -nokeys -in time4user.p12 -out time4user.crt
```
End user signature certificates will be soon available at the [Intesi Group Store](https://www.intesigroup.com).

## Usage

Edit config.yml to configure your bot.

Run the command `python3 cloudsignaturebot.py time4mind.yml`

## Known Issues

This is just a proof of concept, to incentivate building a real project, so the main limitation and isuues are: 
* It should be possible to sign the same document by two or more users in a group chat
* It should be possible to sign a set of documents in one shot 
* Management by user of more than one e-sign certificate is missing
* Data permanence on DB or cloud services
* Python exposed api for callback should be secured
* Privacy of documents cannot be fully granted because Telegram does not support end-to-end chat encryption for bots

## Credits

* [python-telegram-bot](https://python-telegram-bot.org/)
* [Flask](http://flask.pocoo.org/)
* [Zeep](http://flask.pocoo.org/)
* [Designing a RESTful API with Python and Flask](https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask)


##License

You may copy, distribute and modify the software provided that modifications are described and licensed for free under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html). Derivatives works (including modifications or anything statically linked to the library) can only be redistributed under LGPL-3, but applications that use the library don't have to be.
