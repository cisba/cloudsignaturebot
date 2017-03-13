import sys, magic, re
from pkboxsoap import PkBoxSOAP

sign_service = PkBoxSOAP()
pathname = str(sys.argv[1])
signer = str(sys.argv[2])
pin = str(sys.argv[3])
otp = str(sys.argv[4]) 

if re.match(r'PDF document.*', magic.from_file(pathname)):
    filetype = 'pdf'
else:
    filetype = 'p7m'
result = sign_service.envelope(pathname, filetype, signer, pin, otp)
print(result)

