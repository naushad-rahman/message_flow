from flask import Flask, render_template, request, jsonify, escape

import json
import threading
import hashlib
import uuid
import collections
import conf
import jwt


app = Flask(__name__)
app.secret_key = conf.secret


import zmq
ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.connect('ipc:///tmp/message_flow_in')


# Task IDs
class TID:
    OK = 'OK'
    ERROR = 'ERROR'
    DONE = 'TASK DONE'


def push(user, task_id, data):
    """Push message to `user` over websocket.

    """
    pub.send(b"0 " + json.dumps({'username': user,
                                 'id': task_id,
                                 'data': data}).encode('utf-8'))


def long_task(user, message):
    """This is an example of a task that takes long to execute.

    """
    import time
    try:
        from time import monotonic
    except ImportError:
        from time import time as monotonic
    import random

    m0 = monotonic()
    time.sleep(2 + random.random())
    m1 = monotonic()

    processed_message = 'Message processed, "{}" in {:.2f} seconds'.format(escape(message), m1 - m0)
    push(user, TID.DONE, processed_message)


@app.route('/send', methods=['POST'])
def send():
    message = request.form.get('message', '')

    if not message:
        return jsonify(status=TID.ERROR, data='No message submitted')
    else:
        threading.Thread(target=long_task, args=(get_username(), message)).start()
        return jsonify(status=TID.OK,
                       data='Message submitted for processing')


# Modify this for your specific application
#
# !! Certainly don't get usernames from the client like I do here--that would be highly
# insecure
def get_username():
    return request.cookies.get('username')


# !!!
# This API call should **only be callable by logged in users**
# !!!
@app.route('/socket_auth_token', methods=['GET'])
def socket_auth_token():
    return jwt.encode({'username': get_username()}, app.secret_key)


@app.route('/')
def index():
    return render_template('index.html', username=get_username())
