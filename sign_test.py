import sys
from pkboxsoap import PkBoxSOAP

sign_service = PkBoxSOAP()
pathname = "sec/validsign.pdf"
signer = str(sys.argv[1])
pin = str(sys.argv[2])
otp = str(sys.argv[3]) 

file_format = sign_service.envelope(pathname, signer, pin, otp)
print(file_format)

