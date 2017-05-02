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
    a = json.loads(request.get_json())
    canvas = a['canvas'][0]
    position = canvas['x'] + (canvas['y']-1) * model.Length
    color = canvas['color']
    time1 = time.time()
    count = eval(conn.get("count"))
    if model.operation( conn, count, position, color, time1, IP) == 1:
        return jsonify( model.error1 )
    # model.operation( conn, count, position, color, time1, IP )
    conn.incr("count")
    data = {
        "x": canvas['x'],
        "y": canvas['y'],
        "color": color,
        "time": time1
    }
    count_enter_in = a['count']
    list_modify = []
    # list_modify = model.update_canvas( list_modify, conn, count_enter_in, count )
    # list_modify = []
    model.update_canvas( list_modify, conn, count_enter_in, count )
    list_modify.append(data)
    update_data = { "data":list_modify, "count":count }
    return jsonify( update_data )

@app.route('/canvas/update', methods = ['GET'])
def update():
    # count_current = 1  #just for test
    count_current = json.loads(request.get_json())['count']
    count = eval(conn.get('count'))
    list_modify = []
    model.update_canvas( list_modify, conn, count_current, count )
    # update_data = { "data":list_modify, "count":count }
    return jsonify( data = list_modify, count = count )


'''home is done.'''
@app.route('/',methods = ['GET'])
def home():
    canvas_current = []
    canvas_current = model.refresh_canvas( canvas_current, conn )
    count_current = eval( conn.get( 'count' ) )
    return jsonify( data = canvas_current, count = count_current )
    # return jsonify(  count = count_current )