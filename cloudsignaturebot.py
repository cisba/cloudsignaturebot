
import sys 
import yaml
import logging
import time4mind
from telegram.ext import Updater
from telegram.ext import CommandHandler
from flask import Flask, jsonify, abort, make_response, request

# read configuration
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)

# setup logger
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger()
#logger.setLevel(logging.INFO)

# define time4mind functions
time4user = time4mind.Time4UserRPC(cfg['time4user'])
time4id = time4mind.Time4IdRPC(cfg['time4id'])

def authorize(user):
    title = 'Welcome to Cloud Signature!'
    sender = cfg['bot']['username'] + ' (Telegram Bot)'
    message = 'Telegram user <b>' + user['display_name'] + '</b>'
    if user['username']:
        message += ' with username <b>' + user['username'] + '</b>'
    message += ' requests to use ' + cfg['bot']['username'] + ' with your Valid account <b>' + user['time4mind_account'] + '</b>.'
    restHook = cfg['time4id']['restHook'] + '/authorize/' + str(user['id'])
    r = time4id.authorizeMobile(user['cred']['otpId'],user['cred']['otpProvider'],
        title,sender,message,restHook)
    return r

# define telegram functions
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, 
    text="To use this bot you should have:\n* an e-sign certficate\n* the Valid mobile app installed with the e-sign OTP enabled\n\nLink your Valid account with the command /link followed by the username (usually the email)\n\nAn authorization request will be sent to your Valid mobile app.")

# poor man data persistence on yaml
def save_acl(user_data):
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        acl = dict()
    if user_data['id'] not in acl:
        acl[user_data['id']] = dict()
    for k in user_data:
        acl[user_data['id']][k] = user_data[k]
    try:
        with open(cfg['acl'], 'w+') as yml_file: yml_file.write(yaml.dump(acl))
    except:
        print("error writing acl")
 
 def get_acl_user_id(user_id):
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        return None
    if user_id not in acl:
        return None
    else:
        return acl[user_data[user_id]]['chat_id'] 
 
 def set_acl_status(user_id,status):
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        return None
    if user_id not in acl:
        return None
    acl[user_data[user_id]]['status'] = status 
    try:
        with open(cfg['acl'], 'w+') as yml_file: yml_file.write(yaml.dump(acl))
    except:
        print("error writing acl")
        
# link telegram user to time4mind account
def link(bot, update, args, user_data):
    # check arguments
    if len(args) != 1:
        text = 'Please, pass me only one string without spaces'
        bot.sendMessage(chat_id=update.message.chat_id, text=text)
        return
    # build telegram user data structure
    user_data['id'] = update.message.from_user.id
    user_data['time4mind_account'] = args[0]
    user_data['first_name'] = update.message.from_user.first_name
    user_data['last_name'] = update.message.from_user.last_name
    user_data['username'] = update.message.from_user.username
    user_data['chat_id'] = update.message.chat_id
    if user_data['last_name']:
        user_data['display_name'] = user_data['first_name'] + ' ' + user_data['last_name']
    else:
        user_data['display_name'] = user_data['first_name'] 
    # look for credentials
    c = time4user.getMobileActiveCredentials(user_data['time4mind_account'])
    if len(c) > 0:
        user_data['cred'] = c[0] 
    # save user data
    save_acl(user_data)
    # send request
    authorize(user_data)
    message = 'I sent an authorization request to your Valid app'
    bot.sendMessage(chat_id=update.message.chat_id, text=message+'\n\n'+str(user_data))

# webserver to handle callback

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api/v1.0/authorize/<int:user_id>', methods=['POST'])
def get_authorization(user_id):
    print(request.json)
    #if not request.json or not 'title' in request.json:
    if not request.json:
        abort(400)
    # process callback
    return jsonify({}), 201

#######################
# main section

# setup telegram updater and  dispatchers
updater = Updater(token=cfg['bot']['token'])
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

link_handler = CommandHandler('link', link, pass_args=True, 
        pass_user_data=True)
dispatcher.add_handler(link_handler)

if __name__ == '__main__':
    # start webserver
    app.run(debug=True)
    # start polling telegram
    updater.start_polling()


