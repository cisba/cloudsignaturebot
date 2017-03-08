import sys, datetime
from requests import Session
from zeep import Client, xsd
from zeep.transports import Transport
from base64 import b64encode, b64decode
import re
import magic
import logging.config
import urllib3

urllib3.disable_warnings()


'''
# to debug soap
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            'level': 'DEBUG',
            'propagate': True,
            'handlers': ['console'],
        },
    }
})
'''

file_pathname = "sec/validsign.pdf"
signer = "[INTESI-NAMIRIAL-TEST]_CSBMNL66E25F205E"
pin = "12345678"
otp = str(sys.argv[1]) 

session = Session()
session.verify = False
transport = Transport(session=session)
client = Client('https://localhost:8443/pkserver/services/Envelope?wsdl', transport=transport)
service = client.create_service(
    '{http://soap.remote.pkserver.it}EnvelopeSoap11Binding',
    'https://localhost:8443/pkserver/services/Envelope.EnvelopeHttpSoap11Endpoint/'
    )

with open(file_pathname, 'rb') as f: buf = f.read()
#document = b64encode(buf)
#document = xmlrpclib.Binary( open('foo.pdf').read() )
#document = open('foo.pdf').read() 
#document=bytes("aaa", 'UTF-8')
#document=bytes(buf, 'UTF-8')
document=buf

#document = xmlrpclib.Binary( buf )

filetype = magic.from_file(file_pathname)
if re.match(r'PDF document.*',filetype):
    result = service.pdfsign(environment="default", signer=signer, pin=pin, signerPin=otp, 
                             date=datetime.date.today(), customerinfo="none",
                             document=document, 
                             fieldName=None, image=None, page=-1, position=0, x=0, y=0)
                             #document=document, fieldName="", image="", page="", position="")
    result_pathname = "sec/SIGNED_validsign.pdf"
else:
    result = service.sign(environment="default", signer=signer, pin=pin, signerPin=otp, 
                          date=datetime.date.today(), customerinfo="none",
                          data=document, mode=1, encoding=1 )
    result_pathname = "sec/validsign.pdf.p7m"

#signed_doc = b64decode(result)
signed_doc = result
with open(result_pathname,'wb+') as f: f.write(signed_doc)

'''
pdfsign(
    environment: xsd:string, 
    document: xsd:base64Binary, 
    fieldName: xsd:string, 
    reason: xsd:string, 
    location: xsd:string, 
    contact: xsd:string, 
    customerinfo: xsd:string, 
    signer: xsd:string, 
    pin: xsd:string, 
    signerPin: xsd:string, 
    date: xsd:dateTime, 
    image: xsd:base64Binary, 
    page: xsd:int, 
    position: xsd:int, 
    x: xsd:int, 
    y: xsd:int) -> xsd:base64Binary


sign(
    environment: xsd:string, 
    data: xsd:base64Binary, 
    customerinfo: xsd:string, 
    signer: xsd:string, 
    pin: xsd:string, 
    signerPin: xsd:string, 
    mode: xsd:int, 
    encoding: xsd:int, 
    date: xsd:dateTime) -> xsd:base64Binary


'''



'''
Example of a sign transaction APPROVED:

    {
    'result': ['@pin'], 
    'pin': 'xI1lhMbAiALTCZ3I71bQIQ==', 
    'otp': '{ 
            "SessionKey":"Z4NnyTUgUePgSNSAgPiiysY2yIB+lSZg1xXUArOK1zJq11JqqCJ3plTGysynjeu1uhHSM\\/4SvaBHqDjL6NIjmustOITo2dOf3DVzTyk3RIjCh9XWANNWFhgaMMmWI6B8NBA\\/tQ6+bztTt4PJ3OJwwdAI0u\\/EuDZLSCvdcUfohyg=",
            "KeyPIN":"BNcuQZWbdcpZeMESzTPfKA==",
            "Ciphered":true
            }', 
    'applicationId': None, 
    'approved': 1, 
    'transactionId': 'd6d76bdc-23ab-473d-b9c8-a9632c147656', 
    'antiFraud': '[]'
    }
'''
