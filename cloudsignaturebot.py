
import sys 
import yaml
import logging
import time
from threading import Thread
from queue import Queue
from time4mind import Time4Mind
from telegram.ext import Updater, CommandHandler
from telegram import Bot
from flask import Flask, jsonify, abort, make_response, request


# poor man data persistence on yaml

def acl_load():
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        logging.warning("filed to read acl file: " + str(cfg['acl']))
        acl = dict()
    return acl

def acl_update(user_info):
    acl = acl_load()
    if user_info['id'] not in acl:
        acl[user_info['id']] = dict()
    for k in user_info:
        acl[user_info['id']][k] = user_info[k]
    acl_dump(acl)

def acl_dump(acl):
    try:
        with open(cfg['acl'], 'w+') as yml_file: yml_file.write(yaml.dump(acl))
        #logging.info(yaml.dump(acl))
    except:
        logging.critical("error writing acl file: " + str(cfg['acl']))
 
def acl_set_status(user_id,status):
    acl = acl_load()
    if user_id not in acl:
        logging.error('user_id ' + str(user_id) + 'not found in acl file:' \
                      + str(cfg['acl']))
        return None
    acl[user_id]['status'] = status 
    acl_dump(acl)
  
def acl_get_status(user_id):
    acl = acl_load()
    if user_id not in acl:
        return None
    return acl[user_id]
 
# define telegram functions
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, 
    text="To use this bot you should have:\n" \
         + "* an e-sign certficate\n" \
         + "* the Valid mobile app installed with the e-sign OTP enabled\n\n" \
         + "Link your Valid account with the command /link followed " \
         + "by the username (usually the email)\n\n" \
         + "An authorization request will be sent to your Valid mobile app.")

def status(bot, update):
    user_info = acl_get_status(update.message.from_user.id)
    if not user_info:
        return
    if user_info['status'] == "approved":
        text="You are already authorized to use Valid account *" \
             + str(user_info['time4mind_account']) +'*' 
    elif user_info['status'] == "waiting approval":
        text="I'm waiting your authorization from Valid app\n" + str(user_info) 
    else:
        text="You are not yet authorized"
    bot.sendMessage(chat_id=update.message.chat_id, text=text, parse_mode="Markdown") 
      
def link(bot, update, args):
    # check arguments
    if len(args) != 1:
        text = 'Please, pass me only one string without spaces'
        bot.sendMessage(chat_id=update.message.chat_id, text=text)
        return
    # build telegram user data structure
    user_info = dict()
    user_info['id'] = update.message.from_user.id
    user_info['time4mind_account'] = args[0]
    user_info['first_name'] = update.message.from_user.first_name
    user_info['last_name'] = update.message.from_user.last_name
    user_info['username'] = update.message.from_user.username
    user_info['chat_id'] = update.message.chat_id
    user_info['status'] = 'waiting approval'
    if user_info['last_name']:
        user_info['display_name'] = user_info['first_name'] + ' ' + user_info['last_name']
    else:
        user_info['display_name'] = user_info['first_name'] 
    # look for credentials
    cred = time4mind.getMobileActiveCredentials(user_info['time4mind_account'])
    if len(cred) > 0:
        user_info['cred'] = cred[0] 
    # send request
    route = '/api/v1.0/authorize/' + str(user_info['id']) \
            + '/' + str(user_info['chat_id'])
    user_info['last_transaction'] = time4mind.authorize(user_info,route)
    # save user data
    acl_update(user_info)
    # message user
    message = 'I sent an authorization request to your Valid app'
    #message += '\n\n'+str(user_info)
    #message += '\n\n'+str(bot)
    bot.sendMessage(chat_id=update.message.chat_id, text=message)

# queue consumer
def process_queue(args):
    (queue, bot, acl_set_status) = args
    while True:
        q_msg = queue.get()
        if q_msg['type'] == "approval":
            transaction = q_msg['content']
            try:
                acl_set_status(q_msg['chat_id'],"approved")
                message = 'You have been authorized'
                bot.sendMessage(chat_id=q_msg['chat_id'], text=message)
                logging.info('authorized user: ' + str(q_msg['user_id'])) 
            except:
                logging.warning('error sending auth confirmation for transaction ' \
                                + '\ncontent: ' + str(transaction) \
                                + '\nbot: ' + str(bot) \
                                + '\nchat_id: ' + str(q_msg['chat_id']) \
                                + '\nuser_id: ' + str(q_msg['user_id']) )
            q.task_done()

# webserver to handle callback

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api/v1.0/authorize/<int:user_id>/<int:chat_id>', methods=['POST'])
def get_authorization(user_id,chat_id):
    #if not request.json or not 'title' in request.json:
    if not request.json:
        logging.debug(request)
        abort(400)
    if not user_id or not chat_id :
        loggign.debug(request)
        abort(400)
    # process callback
    try:
        for transaction in request.json:
            if transaction['approved'] == 1:
                q_msg = dict()
                q_msg['user_id'] = user_id
                q_msg['chat_id'] = chat_id
                q_msg['type'] = "approval"
                q_msg['content'] = transaction
                q.put(q_msg)
    except:
        logging.error("failed processing transaction callback")
    return jsonify({'authorization': 'received'}), 200

# [{'approved': 2, 'applicationId': None, 'transactionId': '8f52c58f-9f69-44e9-b716-d7dc1c69a6b4'}]

# [{'pin': '', 'result': [], 'applicationId': None, 'transactionId': '954593fc-3162-4077-9731-af8aab27dda5', 'approved': 1, 'otp': 'E77337B8CC3FD9C5DB805B123259149BC9313A169D9319157187D91205214CFC', 'antiFraud': '[]'}] 

# start webserver
def flask_thread():
    app.run(debug=True, use_reloader=False)


###############
# Main section

# read configuration and setup time4mind class
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
time4mind = Time4Mind(cfg)

# setup logger
logging.basicConfig(level=logging.INFO,
                    filename=cfg['logfile'], filemode='w',
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

# setup telegram updater and  dispatchers
updater = Updater(token=cfg['bot']['token'])
dispatcher = updater.dispatcher

# start command
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# link command
link_handler = CommandHandler('link', link, pass_args=True)
dispatcher.add_handler(link_handler)

# status command
status_handler = CommandHandler('status', status)
dispatcher.add_handler(status_handler)

# setup queue
q = Queue(maxsize=100)
bot = Bot(cfg['bot']['token'])
dispatcher.run_async(process_queue,(q,bot,acl_set_status))

# run updater and webserver as a threads
webserver_thread = Thread(target=flask_thread, name='webserver')
webserver_thread.start()

updater_thread = Thread(target=updater.start_polling, name='updater')
updater_thread.start()

