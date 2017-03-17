import sys
import yaml
import logging
from pprint import pprint
from time4mind import Time4Mind
from time4mind import Time4IdRPC


# read configuration and setup time4mind class
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
time4mind = Time4Mind(cfg)
time4id = Time4IdRPC(cfg['time4id'])

# setup logger
logging.basicConfig(level=logging.INFO)

# build telegram user data structure
user_info = dict()
user_info['id'] = '000000000'
user_info['time4mind_account'] = sys.argv[2]
user_info['first_name'] = 'Neil'
user_info['last_name'] = 'Swaab'
user_info['username'] = 'Mr.Wiggles'
user_info['display_name'] = 'Mr.Wiggles'
user_info['chat_id'] = '0000000000'
user_info['status'] = 'waiting authorization'
# look for credentials
cred = time4mind.getMobileActiveCredentials(user_info['time4mind_account'])
if len(cred) > 0:
    for c in cred:
        print('---------------------------------------------')
        pprint(c)
        tokenInfo = time4id.getTokenInfo(c['otpId'],c['otpProvider'])
        pprint(tokenInfo)
        if tokenInfo:
            user_info['cred'] = c
            # send auth request
            result = time4mind.authorize(user_info,'/none/')
            if result:
                pprint(result)
            else:
                print('ERROR: authorize() call failed!')
        else:
            print('ERROR: getTokenInfo() call failed!')

