1# -*- coding: utf-8 -*-
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
import ast
app = Flask( __name__ )
app.config.from_object( Configuration )
redis_db = redis.Redis( host='127.0.0.1', port=6379, db=0 )
conn = redis_db

# Initiation:
if not conn.get('init'):   
    model.init_canvas( conn )
    conn.set('count', 1)
    conn.set('init' , 1)
    
@app.route( '/modify', methods = ['POST'] )
def modify():
    IP = request.environ.get( 'HTTP_X_REAL_IP', request.remote_addr )
    a  = request.get_json()
    canvas   = a['canvas'][0]
    position = canvas['x'] + (canvas['y']) * model.Length
    color =    int(canvas['color'])
    count =    int( conn.get("count") )
    time1 =    time.time()
    if position > model.Width * model.Length - 1 or color < 0 or color > 0xFFFFFF :
    	return jsonify( model.error1 )
    if model.operation( conn, count, position, color, time1, IP) == 1 :
        return jsonify( model.error1 )
    conn.incr("count")
    data = {
        "y": canvas['y'],
        "x": canvas['x'],
        "color": color,
        "time" : time1
    }
    count_enter_in = a['count']
    list_modify    = []
    model.update_canvas( list_modify, conn, count_enter_in, count )
    list_modify.append(data)
    update_data = { "data":list_modify, "count":int(conn.get("count")), "flag":True }
    return jsonify( update_data )

@app.route('/update', methods = ['GET'])
def update():
    count_current = int( request.args.get('count') )
    count = int( conn.get('count') )
    if count_current < -1 or count_current == 0 :
        return jsonify( model.error1 )
    if count_current == 2:
    	return jsonify(test = request.environ.get( 'HTTP_X_REAL_IP', request.remote_addr ))
    if count_current == -1 :
        canvas_current = []
        canvas_current = model.refresh_canvas( canvas_current, conn )
        count_current = int( conn.get( 'count' ) )
        return jsonify( data = canvas_current, count = count_current, flag=True )

    list_modify = []
    model.update_canvas( list_modify, conn, count_current , count )
    return jsonify( data = list_modify,    count = count,         flag=True )

