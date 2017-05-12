# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 21:54:30 2017

@author: mmmmm
"""
from model import *
from flask_compress import Compress
from flask import Flask, jsonify
from flask import request
from config import Configuration
import redis
import gzip
import time

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

# if not conn.get('expand'):
#     conn.set('expand', 1)
#     canvasStatus = []
#     p = conn.pipeline()
#     for i in range( 40000, Length * Width ):
#         p.zadd( "canvas:", i, int(0xF9FAFC) )
#     for i in range( 40000 ):
#     	color = int(conn.zscore("canvas:", i ))
#     	x = i % 200
#     	y = i //200
#     	position = x + y * 300
#     	p.zadd( "canvas:", position, color)
#     p.execute()

#     p1 = conn.pipeline()
#     for i in range( Length * Width ):
#         p1.zscore("canvas:", i)
#     q1 = p1.execute()
#     for i in range( Length * Width ):
#     	if int(q1[i]) != int(0xF9FAFC):
#     		canvasStatus.append( i )
canvasStatus = []
# Redeploy
if 1:
    p2 = conn.pipeline()
    for i in range( Length * Width ):
        p2.zscore("canvas:", i)
    q2 = p2.execute()
    for i in range( Length * Width ):
        if int(q2[i]) != int(0xF9FAFC):
            canvasStatus.append( i )

@app.route( '/modify', methods = ['POST'] )
def modify():
	# Identify the origin of operation
	# If it's not from safari, this operation fails.
    # head = request.headers.get('User-Agent')
    # if 'Mozilla' not in head :
    #     return jsonify( flag = False, notSafari = True )

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
        "color": color
    }
    if color != 0xF9FAFC and position not in canvasStatus:
        canvasStatus.append( position )
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
        list_modify = response_refresh( conn, count, canvasStatus)
        return jsonify( data = list_modify, count = count, flag = True )
    # Update
    update_canvas( list_modify, conn, count_current , count )
    return jsonify( data = list_modify, count = count, flag = True )
