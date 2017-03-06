"""This is the webserver module 

It allow to manage authorization callbacks from Time4Mind cloud trust services

Here there are some example of the json structure to process.

## Example of a auth transaction APPROVED:
        {
        'pin': '', 
        'result': [], 
        'applicationId': None, 
        'transactionId': '954593fc-3162-4077-9731-af8aab27dda5', 
        'approved': 1, 
        'otp': 'E77337B8CC3FD9C5DB805B123259149BC9313A169D9319157187D91205214CFC', 
        'antiFraud': '[]'
        } 

## Example of a sign transaction APPROVED:

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

## Example of a transaction REFUSED:
        {
        'approved': 2, 
        'applicationId': None, 
        'transactionId': '8f52c58f-9f69-44e9-b716-d7dc1c69a6b4'
        }
"""

import logging
from flask import Flask, jsonify, abort, make_response, request

class CSBwebserver:
    """this class is just the wrapper for a simple flask implementation"""

    app = Flask(__name__)

    def __init__(self, queue):
        """initizalization with configuration data
        
        Keyword arguments:
        conf -- the configuration dictionary
        """
        q = queue

    # function to start webserver as a thread
    def flask_thread(self):
        self.app.run(debug=True, use_reloader=False)

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
            logging.error("failed processing authorization transaction callback")
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
        if True:
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
        else:
            logging.error("failed processing signature transaction callback")
        return jsonify({'authorization': 'received'}), 200



