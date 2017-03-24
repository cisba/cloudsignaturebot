"""This is the time4mind module 

It allow to manage users' electronic identities on the Time4Mind cloud PaaS
"""

import requests,json, logging

class Time4MindRPC:
    """Common base class for all Time4Mind RPC call"""

    def __init__(self, conf):
        """initizalization with configuration data and predefined headers and payload
        
        Keyword arguments:
        conf -- the configuration dictionary
        """
        self.endpoint = conf['endpoint']
        if 'cert' in conf and 'key' in conf:
            self.cert = (conf['cert'], conf['key'])
        else:
            self.cert = None
        if 'restHook' in conf:
            self.restHook = conf['restHook']
        else:
            self.restHook = None
        self.payload = {
            'jsonrpc': '2.0',
            'id': 1
            }
        self.headers= {
            'user-agent': 'JSON-RPC Python Client/1.0',
            'content-type': 'application/json',
            'connection': 'close',
            'accept': 'application/json'
            }
   
    def postRPC(self, method, params=None):
        """simple function to call any RPC method with a POST RPC request
        
        Keyword arguments:
        method -- a string with the method name
        params -- a dictionary containing parameters
        """
        self.payload['method'] = method
        if params: self.payload['params'] = params
        j_payload = self.payload
        logging.debug('postRPC call payload: ' + json.dumps(self.payload))
        resp = requests.post(self.endpoint, cert=self.cert, 
                             json=j_payload, headers=self.headers)
        if resp.status_code != 200: resp.raise_for_status()
        try:    
            logging.debug('postRPC response: ' + repr(resp.json()['result']))
            return resp.json()['result']
        except:
            logging.warning('Got 200.. but not result! resp.content is: ' \
                            +str(resp.content))
            return None


class Time4UserRPC(Time4MindRPC):
    """class for Time4User RPC call derived from Time4MindRPC"""
        
    def listSignCredentials(self,user):
        """map to Time4User listCredentials method, 
           requiring only signature flavour
        
        Keyword arguments:
        user -- a dictionary with user attributes
        """
        method = 'listCredentials'
        params = {'account': user, 'credentialType': 1 }
        return self.postRPC(method, params)


class Time4IdRPC(Time4MindRPC):
    """class for Time4Id RPC call derived from Time4MindRPC"""

    def authorizeMobile(self,otpId,otpProvider,title,sender,message,restHook,
        opType=0,authType=0,wizard=None):
        """ map to Time4Id submitOOB method, for simple authorization

        Keyword arguments:
        otpId -- a propery of credential object
        otpProvider -- a propery of credential object
        title -- the title of the message displayed on the mobile notification view
        sender -- the sender of the message displayed on the mobile notification view
        message -- the body of the message displayed on the mobile notification view
        restHook -- the URL of the listener receiving authorization responses
        opType -- the operation type: 0=internal, 1=external, 2=signature 
        authType -- define exchanged data that will be authenticated via otp-signature: 
                    0=none, 1=content, 2=result, 3=content+result
        """
        body = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>' \
                + '<?xml-stylesheet type=\"text/xml\" href=\"#stylesheet\"?>' \
                + '<!DOCTYPE catalog [<!ATTLIST xsl:stylesheet id ID #REQUIRED> ]>' \
                + '<catalog> <xsl:stylesheet id=\"stylesheet\" version=\"1.0\" ' \
                + 'xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\"> ' \
                + '<xsl:template match=\"/\"> <html> <body> ' \
                + message + ' </body> </html> </xsl:template> ' \
                + '</xsl:stylesheet> </catalog>'
        params = {
            'otpId': otpId, 'otpProvider': otpProvider, 
            'opType': opType, 'authType': authType,
            'restHook': restHook,
            'header': 
                { 'title': title, 'sender': sender }, 
            'data': 
                { 'contentType': 'application/xml', 'content': body } 
            }
        if wizard: params['param'] = wizard
        return self.postRPC('submitOOB', params)

    def getTokenInfo(self,otpId,otpProvider):
        params = {'otpId': otpId, 'otpProvider': otpProvider }
        return self.postRPC('getTokenInfo', params)


class Time4Mind():
    """the high level class used from others applications

    Keyword arguments:
    None
    """

    def __init__(self, config):
        """aquire configuration and instance subclasses Time4UserRPC and Time4IdRPC

        Keyword arguments:
        config -- a dictionary of configuration parameters
        """
        self.cfg = config
        self.time4user = Time4UserRPC(self.cfg['time4user'])
        self.time4id = Time4IdRPC(self.cfg['time4id'])

    def authorize(self,user,route):
        """send authorization request to Valid mobile app of time4mind user
        
        Keyword arguments:
        user -- a dictionary with user attributes
        route -- route to append to the webserver endpoint that will receive response 
        """
        title = 'Welcome to Cloud Signature!'
        sender = self.cfg['bot']['username'] + ' (Telegram Bot)'
        message = 'Telegram user <b>' + user['display_name'] + '</b>'
        if user['username']:
            message += ' with username <b>' + user['username'] + '</b>'
        message += ' requests to use ' + self.cfg['bot']['username'] \
                + ' with your Valid account <b>' + user['time4mind_account'] + '</b>.'
        restHook = self.cfg['webserver']['endpoint'] + route 
        return self.time4id.authorizeMobile(user['cred']['otpId'],
                                            user['cred']['otpProvider'],
                                            title,sender,message,restHook)

    def getMobileActiveCredentials(self,user):
        """get an array of credentials usable to send requests to the Valid mobile app
        
        Keyword arguments:
        user -- a dictionary with user attributes
        """
        credentials = self.time4user.listSignCredentials(user)
        result = []
        if 'credentialsData' in credentials and credentials['credentialsData']:
            # Now clean the list
            for todo_item in credentials['credentialsData']:
                logging.debug('found credential: ' + repr(todo_item))
                # remove status not ACTIVE
                if todo_item['status'] != 'ACTIVE' : continue
                if todo_item['certificateStatus'] != 'ATTIVO' : continue
                # remove not having any OTP
                if todo_item['otpDetails'] == None : continue
                # remove OTP not on app Time4ID 
                if todo_item['otpDetails']['otpMode'] != 1 : continue
                # now concatenate only relevant elements
                c = dict((k, todo_item[k]) for k in ('alias','domain','label'))
                c['otpId'] = todo_item['otpDetails']['otpId'] 
                c['otpProvider'] = todo_item['otpDetails']['otpProvider'] 
                # remove OTP not responding to Time4Id backend 
                if not self.time4id.getTokenInfo(c['otpId'],c['otpProvider']) : continue
                # 0=sms, 1=app, 2=email
                c['otpMode'] = todo_item['otpDetails']['otpMode'] 
                c['dump'] = todo_item 
                result += [c]
        return result

    def signMobile(self,otpId,otpProvider,title,sender,message,label,route):
        """map to Time4Id submitOOB method, for signature with PIN request

        Keyword arguments:
        otpId -- a propery of credential object
        otpProvider -- a propery of credential object
        title -- the title of the message displayed on the mobile notification view
        sender -- the sender of the message displayed on the mobile notification view
        message -- the body of the message displayed on the mobile notification view
        label -- the string used by the user to identify his credential
        restHook -- the URL of the listener receiving authorization responses
        """
        wizard = [ { 
            'tag': 'Sign PIN',
            'name': 'Certificate PIN',
            'description': 'Insert your PIN to sign with ' + label,
            'type': 'PIN'
            } ]
        restHook = self.cfg['webserver']['endpoint'] + route 
        return self.time4id.authorizeMobile(otpId,otpProvider,
                                            title,sender,message,restHook,
                                            opType=2,authType=0,wizard=wizard)


