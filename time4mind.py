# TODO
# * use logger instead of  print 

import requests,json
from pprint import pprint 

class Time4MindRPC:
    'Common base class for all Time4Mind RPC call'

    def __init__(self, conf):
        self.endpoint = conf['endpoint']
        self.cert = (conf['cert'], conf['key'])
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
   
    def call(self, method, params=None):
        self.payload['method'] = method
        if params: self.payload['params'] = params
        j_payload = self.payload
        #j_payload = json.dumps(self.payload)
        #print(j_payload)
        resp = requests.post(self.endpoint, cert=self.cert, json=j_payload, headers=self.headers)
        #pprint(resp.content)
        if resp.status_code != 200: resp.raise_for_status()
        try:    
            return resp.json()['result']
        except:
            print('Got 200.. but not result!')
            return None

class Time4UserRPC(Time4MindRPC):
    'class for all Time4User RPC call'

    def getCredentials(self,user):
        method = 'listCredentials'
        params = {'account': user, 'credentialType': 1 }
        return self.call(method, params)

    def getMobileActiveCredentials(self,user):
        credentials = self.getCredentials(user)
        result = []
        if credentials:
            # Now clean the list
            for todo_item in credentials['credentialsData']:
                # remove status not ACTIVE
                if todo_item['status'] != 'ACTIVE' : continue
                # remove not having any OTP
                if todo_item['otpDetails'] == None : continue
                # remove OTP not on app Time4ID 
                if todo_item['otpDetails']['otpMode'] != 1 : continue
                # now concatenate only relevant elements
                c = dict((k, todo_item[k]) for k in ('alias','domain','label'))
                c['otpId'] = todo_item['otpDetails']['otpId'] 
                c['otpProvider'] = todo_item['otpDetails']['otpProvider'] 
                # 0=sms, 1=app, 2=email
                c['otpMode'] = todo_item['otpDetails']['otpMode'] 
                result += [c]
        return result

class Time4IdRPC(Time4MindRPC):
    'class for all Time4User RPC call'

    def getTokenInfo(self,otpId,otpProvider):
        params = {'otpId': otpId, 'otpProvider': otpProvider }
        return self.call('getTokenInfo', params)

    def authorizeMobile(self,otpId,otpProvider,title,sender,message,restHook,
        opType=0,authType=0,wizard=None):
        # opType: 0=internal, 1=external, 2=signature 
        # authType: 0=none, 1=content, 2=result, 3=content+result
        content = '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <?xml-stylesheet type=\"text/xml\" href=\"#stylesheet\"?> <!DOCTYPE catalog [<!ATTLIST xsl:stylesheet id ID #REQUIRED> ]> <catalog> <xsl:stylesheet id=\"stylesheet\" version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\"> <xsl:template match=\"/\"> <html> <body> ' + message + ' </body> </html> </xsl:template> </xsl:stylesheet> </catalog>'
        params = {'otpId': otpId, 'otpProvider': otpProvider, 
            'header': { 'title': title, 'sender': sender }, 
            'data': { 'contentType': 'application/xml', 'content': content }, 
            'opType': opType, 'authType': authType }
        params['restHook'] = self.restHook
        if wizard: params['param'] = wizard
        return self.call('submitOOB', params)

    def signMobile(self,otpId,otpProvider,title,sender,message,label,restHook):
        wizard = [ { 
            'tag': 'Sign PIN',
            'name': 'Certificate PIN',
            'description': 'Insert your PIN to sign with ' + label,
            'type': 'PIN'
            } ]
        return self.authorizeMobile(otpId,otpProvider,title,sender,message,restHook,
            opType=2,authType=3,wizard=wizard)


