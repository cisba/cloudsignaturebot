
import sys, yaml
from pprint import pprint
import time4mind

def test_credenziali(l):
    for i in l: 
        pprint("--- " + i + " ---")
        cred = time4user.getMobileActiveCredentials(i)
        for c in cred:
            pprint(c)
            #tokenInfo = time4id.getTokenInfo(c['otpId'],c['otpProvider'])
            #pprint(tokenInfo)

def authorize(user):
    title = "Welcome to Cloud Signature!"
    sender = "@CloudSignature_Bot (Telegram Bot)"
    message = "Telegram user with nick name <b>"+user['nick']+"</b> and phone number <b>"+user['mobile']+"</b> request to use @CloudSignature_Bot with your Valid account <b>"+user['account']+"</b>."
    r = time4id.authorizeMobile(user['cred']['otpId'],user['cred']['otpProvider'],
        title,sender,message)
    return r

def sign(user,docs):
        title = "Signature Request"
        sender = "@CloudSignature_Bot"
        lista=""
        for d in docs:
            lista +="<li><a href='"+docs[d]+"'>"+d+"</a></li>"
        message = "Documents to sign:"+lista
        restHook = "http://www.tttt.it"
        r = time4id.signMobile(user['cred']['otpId'],user['cred']['otpProvider'],title,sender,message,
            cred['label'],restHook=restHook)

# Main

# read cfg and setup endpoints
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
time4user = time4mind.Time4UserRPC(cfg['time4user'])
time4id = time4mind.Time4IdRPC(cfg['time4id'])

# retrive user credential
user = { 'account': "ecisbani@intesigroup.com", 'nick': "@cisba", 'mobile': "3485115925", 'cred': None }
cred = time4user.getMobileActiveCredentials(user['account'])
pprint(cred)
if not cred[0]:
    pprint("no credential suitable found")
    sys.exit(1)
else:
    user['cred']=cred[0]
pprint(user)

#handler = authorize(user)
docs={'documento_1.pdf': 'http://tttt.it/documento_1.pdf'}
handler = sign(cred,docs)
pprint(handler)


