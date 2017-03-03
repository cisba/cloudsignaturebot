
import sys, yaml, time
from pprint import pprint
import time4mind

def test_credenziali(l):
    for i in l: 
        pprint('--- ' + i + ' ---')
        cred = time4user.getMobileActiveCredentials(i)
        for c in cred:
            pprint(c)
            #tokenInfo = time4id.getTokenInfo(c['otpId'],c['otpProvider'])
            #pprint(tokenInfo)

def authorize(user):
    title = 'Welcome to Cloud Signature!'
    sender = '@CloudSignature_Bot (Telegram Bot)'
    message = 'Telegram user with nick name <b>'+user['nick']+'</b> and phone number <b>'+user['mobile']+'</b> request to use @CloudSignature_Bot with your Valid account <b>'+user['account']+'</b>.'
    r = time4id.authorizeMobile(user['cred']['otpId'],user['cred']['otpProvider'],
        title,sender,message)
    return r

def sign(user,docs):
        title = 'Signature Request'
        sender = '@CloudSignature_Bot'
        lista=''
        for d in docs:
            lista +='<li><a href=\"'+docs[d]+'\">'+d+'</a></li>'
        message = 'Documents to sign:'+lista
        return time4id.signMobile(user['cred']['otpId'],user['cred']['otpProvider'],title,sender,message,
            user['cred']['label'])

# Main

# read cfg and setup endpoints
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
time4user = time4mind.Time4UserRPC(cfg['time4user'])
time4id = time4mind.Time4IdRPC(cfg['time4id'])

# retrive user credential
user = { 'account': 'ecisbani@intesigroup.com', 'nick': '@cisba', 'mobile': '3485115925', 'cred': None }
c = time4user.getMobileActiveCredentials(user['account'])
pprint(c)
if not c or not c[0]:
    pprint('no credential suitable found')
    sys.exit(1)
else:
    user['cred']=c[0]
pprint(user)

#handler = authorize(user)
docs={'documento_1.pdf': 'http://tttt.it/documento_1.pdf'}
handler = sign(user,docs)
pprint(handler)

