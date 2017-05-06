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
from model import Length, Width
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
    
@app.route( '/modify', methods = ['GET','POST'] )
def modify():
	# Identify the origin of operation
	# If it's not from safari, this operation fails.
    head = request.headers.get('User-Agent')
    if 'Mozilla' not in head :
        return jsonify( flag = False, notSafari = True )

    # Get json
    IP = request.environ.get( 'HTTP_X_REAL_IP', request.remote_addr )
    a  = request.get_json()
    canvas  = a['canvas'][0]
    position = canvas['x'] % Length + (canvas['y'] % Width) * Length
    color =    int( canvas['color'] )
    count =    int( conn.get("count") )
    time1 =    time.time()
    count_enter_in = a['count']

    if color < 0 or color > 0xFFFFFF :
    	return jsonify( model.error1 )
    # Operate
    remaining, Mark = model.operation( conn, count, position, color, time1, IP)

    # get data of update
    list_modify    = []
    model.update_canvas( list_modify, conn, count_enter_in, count )
    
    # Mark == 1 means that this operation fails.
    # Return the data of update
    if Mark == 1 :
        return jsonify( data = list_modify, count = count, remaingTime = remaining, flag = False )
    
    # If the operation succeed, count += 1
    # And append the it to list_modify.
    count = int( conn.incr("count") )
    data = {
        "y": canvas['y'],
        "x": canvas['x'],
        "color": color,
    }
    list_modify.append(data)
    
    return jsonify( data = list_modify, count = count, remaingCount = remaining, flag = True )

@app.route('/update', methods = ['GET'])
def update():
    head = request.headers.get('User-Agent')
    if 'Mozilla' not in head :
        return jsonify( flag = False, notSafari = True )
    count_current = int( request.args.get('count') )
    count =         int( conn.get('count') )
    if count_current < -1 or count_current == 0 :
        return jsonify( flag = False )
    if count_current == -1 :
        canvas_current = []
        canvas_current = model.refresh_canvas( canvas_current, conn )
        count_current = int( conn.get( 'count' ) )
        return jsonify( data = canvas_current, count = count_current, flag = True )

    list_modify = []
    model.update_canvas( list_modify, conn, count_current , count )
    return jsonify( data = list_modify, count = count, flag = True )

