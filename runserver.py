#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : runserver.py.py
# @Author: harry
# @Date  : 18-8-19 下午5:56
# @Desc  : Run flask server

from gevent import monkey

monkey.patch_all()
import os
import _thread
import time
from flask import Flask, request, jsonify
from werkzeug.contrib.cache import SimpleCache
from gevent import pywsgi
import configparser
from generate_new import *

app = Flask(__name__)
cache = SimpleCache()

model = None
rhyme_style = ['AAAA', 'ABAB', '_A_A', 'ABBA']


def start_suicide():
    time.sleep(1)
    print("Reaching restart threshold, exiting...")
    exit(0)


@app.route('/generate/verse', methods=['POST'])
def generate_verse():
    if request.method == 'POST':
        # POST params
        text = str(request.form['text'])
        num_sentence = int(request.form['num_sentence'])
        target_long = int(request.form['target_length'])
        rhyme_mode = int(request.form['rhyme_mode'])
        rhyme_style_id = int(request.form['rhyme_style_id'])

        # now return the first sentence along with generated sentences
        global model
        model.user_input(
            text=text,
            sample_size=num_sentence - 1,
            target_long=target_long,
            rhyme_mode=rhyme_mode,
            rhyme_style=rhyme_style[rhyme_style_id]
        )
        sentences = [text] + list(model.generator())

        # temporary restart solution
        restart_counter = cache.get('restart_counter')
        restart_threshold = cache.get('restart_threshold')
        if restart_counter == restart_threshold - 1:
            print("Reaching restart threshold, suicide...")
            _thread.start_new_thread(start_suicide)
        restart_counter += 1
        cache.set('restart_counter', restart_counter)

        return jsonify(sentences)
    return 'POST method is required'


if __name__ == "__main__":
    # load model
    print("Loading model...")
    model = Gen()
    model.init_session()
    model.restore_model('./checkpoint')

    # load config from web.ini
    cp = configparser.ConfigParser()
    cp.read('web.ini')
    ip = str(cp.get('web', 'ip'))
    port = int(cp.get('web', 'port'))
    cache.set('restart_counter', 0)
    cache.set('restart_threshold', int(cp.get('restart', 'threshold')))

    # start flask server
    print("Starting web server at {}:{}".format(ip, port))
    server = pywsgi.WSGIServer((ip, port), app)
    server.serve_forever()
