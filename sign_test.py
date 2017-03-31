import sys, magic, re, yaml
import logging
from pkboxsoap import PkBoxSOAP

if len(sys.argv) != 6 :
    print("usage: python sign_test.py <config.yml> <file2sign.pdf> <signer_alias> <pin> <otp>")
    sys.exit()

with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
sign_service = PkBoxSOAP(cfg['pkbox'])
pathname = str(sys.argv[2])
signer = str(sys.argv[3])
pin = str(sys.argv[4])
otp = str(sys.argv[5]) 

logging.basicConfig(level=logging.DEBUG,
                    filename=cfg['logfile'],
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

fileformat = magic.from_file(pathname)
print("fileformat is: "+fileformat)
if re.match(r'PDF document.*', fileformat):
    filetype = 'pdf'
else:
    filetype = 'p7m'
result = sign_service.envelope(pathname, filetype, signer, pin, otp)
print(result)

