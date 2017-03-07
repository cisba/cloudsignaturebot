import sys, datetime
from requests import Session
from zeep import Client, xsd
from zeep.transports import Transport
from base64 import b64encode, b64decode

file_pathname = "sec/validsign.pdf"
result_pathname = "sec/SIGNED_validsign.pdf"
signer = ""
pin = ""
otp = str(sys.argv[1]) 
#time = time.time() * 1000

session = Session()
session.verify = False
transport = Transport(session=session)
client = Client('https://localhost:8443/pkserver/services/Envelope?wsdl', transport=transport)

#with open(file_pathname, 'rb') as f: buf = f.read()
#document = b64encode(buf)
#document = xmlrpclib.Binary( open('foo.pdf').read() )

#sign_type = client.get_type('ns0:sign')
#sign = sign_type(mode=0, encoding=2, environment="default", data="aaa" )
#result = client.service.Envelope(sign=sign)
data=bytes("aaa", 'UTF-8')
otp="123456"
result = client.service.sign(mode=0, encoding=2, environment="default", data=data, signer=signer, pin=pin, signerPin=otp, date=datetime.date.today(), customerinfo="none")
#result = client.service.sign(signer=signer, pin=pin, signerPin=otp, data=document)
#result = client.service.pdfsign(signer=signer, pin=pin, signerPin=otp, document=document, fieldName="", image="")
#result = document
#print(repr(result))
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
