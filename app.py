# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 21:54:30 2017

@author: mmmmm
"""

from flask import Flask,jsonify
from flask import request
from config import Configuration
import redis
import model
import time
import json

app = Flask( __name__ )
app.config.from_object( Configuration )

redis_db = redis.Redis( host='127.0.0.1', port=6379, db=0 )
conn = redis_db

# Initiation:
if not conn.get('init'):   
    model.init_canvas( conn )
    conn.set('count', 1)
    conn.set('init' , 1)
    
@app.route( '/canvas/modify', methods = ['GET','POST'] )
def modify():
    IP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    a = request.get_json()
    canvas = a['canvas'][0]
    position = canvas['x'] * Length + canvas['y']
    color = canvas['color']
    time1 = time.time()
    count = conn.get("count")
    if model.operation( conn, count, position, color, time1, IP):
        return jsonify( model.error1 )
    # model.operation( conn, count, position, color, time1, IP )
    conn.incr("count")
    data = {
        "x": canvas['x'],
        "y": canvas['y'],
        "color": color,
        "time": time1
    }
    count_enter_in = request.get_json()['count']
    list_modify = model.update_canvas( conn, count_enter_in, count ).append(data)
    update_data = { "data":list_modify, "count":count }
    return jsonify( list_modify )

@app.route('/canvas/update', methods = ['GET'])
def update():
    # count_current = 1  #just for test
    count_current = request.get_json()['count']
    count = conn.get('count')
    list_modify = model.update_canvas( conn, count_current, count )
    update_data = { "data":list_modify, "count":count }
    return jsonify( update_data )

# @app.route('/canvas/refresh', methods = ['GET'])
# def refresh():
#     return jsonify("data":list_modify)

# @app.route( '/canvas/get', methods=['GET'] )
# def get1():
# 	data={
# 		'position':1,
# 		'color':0xFF,
# 		'time': time.time(),
# 		'flag':1
# 	}
# 	return jsonify(data)

@app.route('/')
def home():
	count_current = conn.get( 'count' )
    canvas_current = model.refresh_canvas( conn )
	return jsonify( data = canvas_current, count = count_current )