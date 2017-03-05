
import sys 
import yaml
import logging
import time
from threading import Thread
from queue import Queue
from time4mind import Time4Mind
from telegram.ext import Updater
from telegram.ext import CommandHandler
from flask import Flask, jsonify, abort, make_response, request

# setup logger
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger()
#logger.setLevel(logging.INFO)

# queue consumer
def do_stuff(q):
    while True:
        transaction = q.get()
        try:
            message = 'You have been authorized'
            bot.sendMessage(chat_id=transaction['chat_id'], text=message)
        except:
            print('error sending auth confirmation for transaction: ' \
                  + str(transaction) )
        q.task_done()

# define telegram functions
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, 
    text="To use this bot you should have:\n* an e-sign certficate\n* the Valid mobile app installed with the e-sign OTP enabled\n\nLink your Valid account with the command /link followed by the username (usually the email)\n\nAn authorization request will be sent to your Valid mobile app.")

# poor man data persistence on yaml
def acl_save(user_data):
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
        print(yaml.dump(acl))
    except:
        print("error writing acl")
 
def acl_get_chat_id(user_id):
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        return None
    if user_id not in acl:
        return None
    else:
        return acl[user_data[user_id]]['chat_id'] 
 
def acl_set_status(user_id,status):
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        print('error opening acl file:' + str(cfg['acl']))
        return None
    if user_id not in acl:
        print('user_id ' + str(user_id) + 'not found in acl file:' + str(cfg['acl']))
        return None
    acl[user_data[user_id]]['status'] = status 
    try:
        with open(cfg['acl'], 'w+') as yml_file: yml_file.write(yaml.dump(acl))
        print(yaml.dump(acl))
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
    user_data['status'] = 'waiting approval'
    if user_data['last_name']:
        user_data['display_name'] = user_data['first_name'] + ' ' + user_data['last_name']
    else:
        user_data['display_name'] = user_data['first_name'] 
    # look for credentials
    cred = time4mind.getMobileActiveCredentials(user_data['time4mind_account'])
    if len(cred) > 0:
        user_data['cred'] = cred[0] 
    # send request
    route = '/api/v1.0/authorize/' + str(user_data['id']) \
            + '/' + str(user_data['chat_id'])
    user_data['last_transaction'] = time4mind.authorize(user_data,route)
    # save user data
    acl_save(user_data)
    # message user
    message = 'I sent an authorization request to your Valid app'
    #message += '\n\n'+str(user_data)
    bot.sendMessage(chat_id=update.message.chat_id, text=message)

# webserver to handle callback

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api/v1.0/authorize/<int:user_id>/<int:chat_id>', methods=['POST'])
def get_authorization(user_id,chat_id):
    print(request.json)
    #if not request.json or not 'title' in request.json:
    if not request.json:
        abort(400)
    # process callback
    try:
        for transaction in request.json:
            if transaction['approved'] == 1:
                transaction['user_id'] = user_id
                transaction['chat_id'] = chat_id
                q.put(transaction)
    except:
        print("failed processing transaction callback")
    return jsonify({'authorization': 'received'}), 200

# [{'approved': 2, 'applicationId': None, 'transactionId': '8f52c58f-9f69-44e9-b716-d7dc1c69a6b4'}]

# [{'pin': '', 'result': [], 'applicationId': None, 'transactionId': '954593fc-3162-4077-9731-af8aab27dda5', 'approved': 1, 'otp': 'E77337B8CC3FD9C5DB805B123259149BC9313A169D9319157187D91205214CFC', 'antiFraud': '[]'}] 

#######################
# main section

# read configuration and setup time4mind class
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
time4mind = Time4Mind(cfg)

# setup telegram updater and  dispatchers
updater = Updater(token=cfg['bot']['token'])
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

link_handler = CommandHandler('link', link, pass_args=True, 
        pass_user_data=True)
dispatcher.add_handler(link_handler)

updater_thread = Thread(target=updater.start_polling, name='updater')

# dummy queue
q = Queue(maxsize=100)
num_threads = 1
for i in range(num_threads):
    worker = Thread(target=do_stuff, args=(q,))
    worker.setDaemon(True)
    worker.start()

if __name__ == '__main__':
    # start polling telegram
    #updater.start_polling()
    updater_thread.start()
    # start webserver
    app.run(debug=True, use_reloader=False)


