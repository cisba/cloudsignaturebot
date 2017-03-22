"""This is the Cloud Signature Bot based on Time4Mind and Telegram

It allow to sign documents using a Telegram chat and a Time4Mind account
"""

import sys 
import os
import yaml
import logging
import time
import datetime
import uuid
import urllib.request
import shutil
import re
import magic
from threading import Thread
from queue import Queue
from time4mind import Time4Mind
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import Bot
from flask import Flask, jsonify, abort, make_response, request
from pkboxsoap import PkBoxSOAP

# methods for a "poor man" data persistence based on a yaml file

def acl_load():
    try:
        with open(cfg['acl'], 'r') as yml_file: acl = yaml.load(yml_file)
    except:
        logging.warning("failed to read acl file: " + str(cfg['acl']))
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
  
def acl_get_user_info(user_id):
    acl = acl_load()
    if user_id not in acl:
        return None
    return acl[user_id]

# queue consumer
def process_queue(args):
    (queue, bot, acl_set_status) = args
    while True:
        q_msg = queue.get()
        logging.info('queue.get() : ' + repr(q_msg))

        # auth transaction
        if q_msg['type'] == "authorization":
            transaction = q_msg['content']
            acl_set_status(q_msg['chat_id'],"authorized")
            message = 'You have been authorized. Now send me a file to sign!'
            try:
                bot.sendMessage(chat_id=q_msg['chat_id'], text=message)
            except:
                logging.warning('error sending auth confirmation for transaction '\
                                + '\ncontent: ' + str(transaction) \
                                + '\nbot: ' + str(bot) \
                                + '\nchat_id: ' + str(q_msg['chat_id']) \
                                + '\nuser_id: ' + str(q_msg['user_id']) )
            else:
                logging.info('authorized user: ' + str(q_msg['user_id'])) 
        # sign transaction
        elif q_msg['type'] == "signature":

            # retrive file info
            try:
                operation_uuid4 = q_msg['operation_uuid4'] 
                yml_pathname = cfg['storage'] + '/' + operation_uuid4 + '.yml'
                logging.info("process_queue() operation " + operation_uuid4 \
                            + " retriving info from " + yml_pathname)
                with open(yml_pathname, 'r') as yml_file: 
                    docs = yaml.load(yml_file)
                #logging.info(repr(docs))
            except: 
                logging.warning('error retriving saved info for operation: '\
                                + operation_uuid4)

            # sign
            transaction = q_msg['content']
            parent_dir = cfg['storage'] + '/' + str(q_msg['chat_id'])
            directory = parent_dir + '/' + operation_uuid4 + '/'
            for file_item in docs['list']:
                # retrive user certificate alias
                user_info = acl_get_user_info(q_msg['user_id'])
                signer = user_info['cred']['alias']
                if 'domain' in cfg['pkbox'] and cfg['pkbox']['domain'] == "open":
                    signer = '[' + user_info['cred']['domain'] + ']_' + signer
                # retrive file info
                pathname = directory + file_item['file_id']
                filetype = 'p7m'
                if re.match(r'PDF document.*', magic.from_file(pathname)):
                    filetype = 'pdf'
                # call pkbox for signing 
                logging.info("process_queue() operation " + operation_uuid4 \
                        + "signing file: " + pathname)
                result = sign_service.envelope(pathname, filetype, signer,
                                                    transaction['pin'], 
                                                    transaction['otp'])
                # evaluate result
                if result == 'ok' or True:
                    index = docs['list'].index(file_item)
                    if filetype == "pdf":
                        docs['list'][index]['new_name'] = \
                            'SIGNED_' + docs['list'][index]['file_name']
                    else:
                        docs['list'][index]['new_name'] = \
                            docs['list'][index]['file_name'] + '.p7m'
                    logging.info('user ' + str(q_msg['user_id']) \
                                      + ' signed documents in operation: ' \
                                      + operation_uuid4 ) 
                else:
                    logging.warning("envelope() returned " + result 
                            + ' signing document for operation:'\
                            + operation_uuid4) 
                    # TODO:
                    # if pdfsign fail it is possible that pdf is invalid
                    # (i.e.: corrupted or protected with a password)
                    # so should return a msg to request sign it as p7m

            # send message and signed files
            message = 'File signing result:'
            bot.sendMessage(chat_id=q_msg['chat_id'], text=message)
            for file_item in docs['list']:
                pathname = directory + file_item['file_id']
                if not 'new_name' in file_item:
                    message = 'Error signing file: ' + file_item['file_name']
                    bot.sendMessage(chat_id=q_msg['chat_id'], text=message)
                elif not os.path.exists(pathname):
                    logging.warning("not found " + pathname)
                    message = 'Error reading signed file: ' + file_item['new_name']
                    bot.sendMessage(chat_id=q_msg['chat_id'], text=message)
                else:
                    bot.sendDocument( chat_id=q_msg['chat_id'], 
                        document=open(pathname, 'rb'),
                        filename=file_item['new_name'])
                os.remove(pathname)

            # remove yaml file and operation dir
            os.remove(yml_pathname)
            os.rmdir(directory)
            # try remove also chat_id dir if empty
            try:
                os.rmdir(parent_dir)
            except:
                pass

        q.task_done()


# flask webserver to handle callback

app = Flask(__name__)
# function to start webserver as a thread
def flask_thread():
    if 'listenaddr' in cfg['webserver']:
        listenaddr = cfg['webserver']['listenaddr']
    else:
        listenaddr = '127.0.0.1'
    app.run(host=listenaddr,debug=True, use_reloader=False)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/api/v1.0/authorize/<int:chat_id>/<int:user_id>', methods=['POST'])
def get_authorization(chat_id,user_id):
    if any([ not request.json,
             not user_id, 
             not chat_id ]):
        logging.debug(request)
        abort(400)
    # process callback
    try:
        for transaction in request.json:
            if transaction['approved'] == 1:
                q_msg = dict()
                q_msg['user_id'] = user_id
                q_msg['chat_id'] = chat_id
                q_msg['type'] = "authorization"
                q_msg['content'] = transaction
                q.put(q_msg)
    except:
        logging.error("failed processing transaction callback")
    return jsonify({'authorization': 'received'}), 200

@app.route('/api/v1.0/sign/<int:chat_id>/<int:user_id>/<string:operation_uuid4>', methods=['POST'])
def get_signature(chat_id,user_id,operation_uuid4):
    if any([ not request.json,
             not operation_uuid4,
             not chat_id,
             not user_id ]):
        logging.debug(request)
        abort(400)
    # process callback
    try:
        logging.debug(request)
        for transaction in request.json:
            if transaction['approved'] == 1:
                q_msg = dict()
                q_msg['chat_id'] = chat_id
                q_msg['user_id'] = user_id
                q_msg['operation_uuid4'] = operation_uuid4
                q_msg['type'] = "signature"
                q_msg['content'] = transaction
                q.put(q_msg)
    except:
        logging.error("failed processing signature transaction callback")
    return jsonify({'authorization': 'received'}), 200

"""
Example of a auth transaction APPROVED:
    {
    'pin': '', 
    'result': [], 
    'applicationId': None, 
    'transactionId': '954593fc-3162-4077-9731-af8aab27dda5', 
    'approved': 1, 
    'otp': 'E77337B8CC3FD9C5DB805B123259149BC9313A169D9319157187D91205214CFC', 
    'antiFraud': '[]'
    } 

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

Example of a transaction REFUSED:
    {
    'approved': 2, 
    'applicationId': None, 
    'transactionId': '8f52c58f-9f69-44e9-b716-d7dc1c69a6b4'
    }
"""

############################
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
    user_info = acl_get_user_info(update.message.from_user.id)
    if not user_info:
        return
    if user_info['status'] == "authorized":
        text="You are already authorized to use Valid account *" \
             + str(user_info['time4mind_account']) +'*' 
    elif user_info['status'] == "waiting authorization":
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
    user_info['status'] = 'waiting authorization'
    if user_info['last_name']:
        user_info['display_name'] = user_info['first_name'] + ' ' + user_info['last_name']
    else:
        user_info['display_name'] = user_info['first_name'] 
    logging.info("/link command received from user: " + user_info['time4mind_account'])
    # look for credentials
    cred = time4mind.getMobileActiveCredentials(user_info['time4mind_account'])
    if len(cred) < 1:
        logging.warning("/link command did not found valid credentials for user: " + user_info['time4mind_account'])
        message = 'Error sending an authorization request to this account'
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
    else:
        # TODO: choice if credentials > 1
        user_info['cred'] = cred[0] 
        # send request
        route = '/api/v1.0/authorize/' + str(user_info['chat_id']) \
                + '/' + str(user_info['id'])
        try:
            user_info['last_transaction'] = time4mind.authorize(user_info,route)
            # save user data
            acl_update(user_info)
            # message user
            message = 'I sent an authorization request to your Valid app'
            bot.sendMessage(chat_id=update.message.chat_id, text=message)
        except:
            logging.warning("failed to request account usage authorization")


def sign_single_document(bot, update):
    user_info = acl_get_user_info(update.message.from_user.id)
    chat_id = update.message.chat_id
    operation_uuid4 = str(uuid.uuid4())
    logging.info("sign_single_document() operation " + operation_uuid4 \
                + " for user " + user_info)
    if not user_info:
        text="You are not yet authorized"
    if user_info['status'] == "authorized":
        doc_info = update.message.document.__dict__
        # {'mime_type': 'application/pdf', 'file_id': 'BQADBAADbwADNnbhUZSE6H4S95PIAg', 'file_name': '2017_ci_01_28.pdf', 'file_size': 71689}
        file_id = doc_info['file_id']
        file_info = bot.getFile(file_id)
        # {'file_size': 71689, 'file_path': 'https://api.telegram.org/file/bot333930621:AAGJ4XLJ9UxQvfTEQXeKwOkiAvhTE5rdRJE/documents/file_0.pdf', 'file_id': 'BQADBAADbwADNnbhUZSE6H4S95PIAg'}
        doc_info['file_path'] = file_info['file_path']
        doc_info['href'] = cfg['webserver']['endpoint'] + '/api/v1.0/file/' \
                           + operation_uuid4 + '/' + file_id 
        docs = { 'operation_uuid4': operation_uuid4,
                 'list': [ doc_info ] }
        # save data to yaml
        yml_pathname = cfg['storage'] + '/' + operation_uuid4 + '.yml'
        with open(yml_pathname, 'w+') as yml_file: yml_file.write(yaml.dump(docs))
        logging.info("sign_single_document() operation " + operation_uuid4 \
                    + " saved docs to " + yml_pathname)
        # request to sign
        signMobileRequest(user_info,docs) 
        text="Request to sign sent to your Valid app"
        # download file 
        directory = cfg['storage'] + '/' + str(chat_id) + '/' + operation_uuid4 + '/'
        if not os.path.exists(directory):
                os.makedirs(directory)
        with urllib.request.urlopen(doc_info['file_path']) as response, \
                open(directory + doc_info['file_id'], 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    elif user_info['status'] == "waiting authorization":
        text="Sorry but I'm still waiting your authorization from Valid app\n" \
             + str(user_info) 
    else:
        text="You are not yet authorized"
    bot.sendMessage(chat_id=update.message.chat_id, text=text, parse_mode="Markdown") 

def signMobileRequest(user_info,docs):
        title = 'Signature Request'
        sender = '@CloudSignature_Bot'
        message = 'Documents to sign:'
        for file_item in docs['list']:
            message += '<li><a href=\"' + file_item['href'] + '\">' \
                       + file_item['file_name'] + '</a></li>'
        route = '/api/v1.0/sign/' \
                + str(user_info['chat_id']) + '/' \
                + str(user_info['id']) + '/' \
                + str(docs['operation_uuid4'])
        try:
            user_info['last_transaction'] = time4mind.signMobile(
                                            user_info['cred']['otpId'],
                                            user_info['cred']['otpProvider'],
                                            title,sender,message,
                                            user_info['cred']['label'],route)
        except:
            logging.warning("failed to request signature authorization")
        else:
            logging.info("signMobileRequest() sent to user: " + str(user_info['id']) \
                         + " - operation: " + str(docs['operation_uuid4']) \
                         + " - transaction: " + str(user_info['last_transaction']) )
        try:
            acl_update(user_info)
        except:
            logging.warning("failed to save transaction data")


###############
# Main section

# read configuration and setup time4mind class
with open(sys.argv[1], 'r') as yml_file: cfg = yaml.load(yml_file)
time4mind = Time4Mind(cfg)

# setup logger
logging.basicConfig(level=logging.DEBUG,
                    filename=cfg['logfile'], 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

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

# sign document filter 
sign_handler = MessageHandler(Filters.document, sign_single_document)
dispatcher.add_handler(sign_handler)

# setup queue
q = Queue(maxsize=100)
bot = Bot(cfg['bot']['token'])
dispatcher.run_async(process_queue,(q,bot,acl_set_status))

# setup pkbox handler to sign
sign_service = PkBoxSOAP()

# run updater and webserver as a threads
webserver_thread = Thread(target=flask_thread, name='webserver')
webserver_thread.start()

updater_thread = Thread(target=updater.start_polling, name='updater')
updater_thread.start()



