"""This is the soap-pkbox module 

It allow to sign documents using a pkbox server via SOAP interface 
"""

import datetime
import logging
import urllib3
import requests
from zeep import Client
from zeep.transports import Transport
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class PkBoxSOAP:
    """wrapper class to sign documents using SOAP call to PkBox"""

    def __init__(self, conf=dict()):
        """initizalization with configuration data and predefined values
        
        Keyword arguments:
        conf -- the configuration dictionary of pkbox parameters
        """
        if 'hostname' in conf:
            self.hostname = conf['hostname']
        else:
            self.hostname = 'localhost:8443'
   

    def envelope(self, pathname, filetype, signer, pin, otp):
        """signature method
        
        Keyword arguments:
        pathname -- the complete pathname to document
        signer -- a string named "alias" that identify univocally the certificate to use
        pin -- the user PIN to unlock the certificate usage on the remote side
        otp -- the OTP provided by the user strong authentication device
        """
        # service strings composition
        service_wsdl = 'https://' + self.hostname + '/pkserver/services/Envelope?wsdl'
        service_binding = '{http://soap.remote.pkserver.it}EnvelopeSoap11Binding'
        service_endpoint = 'https://' + self.hostname \
                           + '/pkserver/services/Envelope.EnvelopeHttpSoap11Endpoint/'

        # suppress ssl server cert verify
        session = requests.Session()
        session.verify = False
        transport = Transport(session=session)
        # suppress ssl related warning for pkbox selfsigned certificate
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # create service
        client = Client(service_wsdl, transport=transport)
        # rewrite binding
        service = client.create_service(service_binding, service_endpoint)
        # read file
        try:
            with open(pathname, 'rb') as f: document = f.read()
        except:
            ret_val = 'read_error'
            logging.warning("failed pkbox fileread: " + pathname)
        # detect file format
        ret_val = 'ok'
        if filetype == 'pdf':
            try:
                result = service.pdfsign(environment="default", signer=signer, pin=pin, signerPin=otp, 
                                         date=datetime.date.today(), customerinfo=None,
                                         document=document, 
                                         fieldName=None, image=None, page=-1, position=0, x=0, y=0)
            except:
                ret_val = 'pdfsign_error'
                logging.warning("failed pkbox pdfsign: " + pathname)
        else:
            try:
                result = service.sign(environment="default", signer=signer, pin=pin, signerPin=otp, 
                                      date=datetime.date.today(), customerinfo=None,
                                      data=document, mode=1, encoding=1 )
            except:
                ret_val = 'sign_error'
                logging.warning("failed pkbox sign: " + pathname)
        # file overwrite with signed one
        if ret_val == 'ok': 
            try:
                with open(pathname,'wb+') as f: f.write(result)
            except:
                ret_val = 'overwrite_error'
                logging.warning("failed pkbox filewrite: " + pathname)
        # return filetype to manage new filename
        return ret_val
