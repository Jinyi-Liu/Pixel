# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 21:54:30 2017

@author: mmmmm
"""
import gzip
from flask import Flask,jsonify
from flask import request
from config import Configuration
import redis
from model import *
import time
import json
import ast

from flask_compress import Compress
app = Flask(__name__)
app.config.from_object( Configuration )
Compress( app )

redis_db = redis.Redis( host='127.0.0.1', port=6379, db=0 )
conn = redis_db

# Initiation:
if not conn.get('init'):
    init_canvas( conn )
    conn.set('count', 1)
    conn.set('init' , 1)
    conn.set('update_db', 3)
if not conn.get('expand'):
    p = conn.pipeline()
    for i in range( 40000, Length * Width ):
        conn.zadd( 'canvas:', i, int(0xF9FAFC) )
    p.execute()
    conn.set('expand', 1)

canvas1 = []
canvas2 = []
canvas3 = []

@app.route( '/modify', methods = ['POST'] )
def modify():
	# Identify the origin of operation
	# If it's not from safari, this operation fails.
    head = request.headers.get('User-Agent')
    if 'Mozilla' not in head :
        return jsonify( flag = False, notSafari = True )

    # Get json
    IP = request.environ.get( 'HTTP_X_REAL_IP', request.remote_addr )
    a  = request.get_json()
    canvas   = a['canvas'][0]
    position = canvas['x'] % Length + (canvas['y'] % Width) * Length
    color =    int( canvas['color'] )
    count =    int( conn.get("count") )
    time1 =    time.time()
    count_enter_in = a['count']

    if color < 0 or color > 0xFFFFFF :
    	return jsonify( flag = False )
    # Operate
    remaining, Mark = operation( conn, count, position, color, time1, IP )
    
    # get data of update
    list_modify    = []
    update_canvas( list_modify, conn, count_enter_in, count )
    
    # update canvas DB
    refresh_canvas( conn, count, canvas1, canvas2, canvas3 )

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

    list_modify = []
    # Refresh
    if count_current == -1 :
        list_modify = response_refresh( conn, count, canvas1, canvas2, canvas3 )
        return jsonify( data = list_modify, count = count, flag = True )
    # Update
    update_canvas( list_modify, conn, count_current , count )
    return jsonify( data = list_modify, count = count, flag = True )

@app.route('/refresh', methods=['GET'])
def refresh():
	count = int( conn.get('count') )
	flag = refresh_canvas( conn, count, canvas1, canvas2, canvas3 )
	return jsonify( flag = flag )
