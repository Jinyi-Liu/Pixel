# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 21:54:30 2017

@author: mmmmm
"""
from model import *
from flask_compress import Compress
from flask_session import Session
from flask import jsonify
from flask import Flask, session, redirect, url_for, escape, request
from config import Configuration
import redis
import gzip
import time
from flask import render_template

app = Flask(__name__)
app.config.from_object( Configuration )
Compress( app )
Session(app)

redis_db = redis.Redis( host='127.0.0.1', port=6379, db=0 )
conn = redis_db

# Initiation:
if not conn.get('init'):
    init_canvas( conn )
    conn.set('count', 1)
    conn.set('init' , 1)

canvasStatus = []
canvasDict = []
# Redeploy
if 1:
    p2 = conn.pipeline()
    for i in range( Length * Width ):
        p2.zscore( "canvas:", i )
    q2 = p2.execute( )
    for i in range( Length * Width ):
        if int(q2[i]) != int(0xF9FAFC):
            canvasStatus.append( i )
    j = 0 
    for i in canvasStatus :
        canvasDict.append({
            "x": i % Width,
            "y": i// Length,
            "color": int(q2[j])
        })
        j += 1

cas_host = "https://passport.ustc.edu.cn"
service_url = "http://home.ustc.edu.cn/~jm123456/cas/index.html?id=1"
check_url = "https://passport.ustc.edu.cn/login?service=http://home.ustc.edu.cn/~jm123456/cas/index.html?id=1"

@app.route('/check')
def check():
    return render_template('check.html')

@app.route('/cas', methods = ['GET'])
def cas():
    ticket = request.args.get('ticket')
    ticket_status, ticketid = validate_cas_1(cas_host, service_url, ticket)
    if ticket_status == 0:
    	return jsonify( login = False)
    session['username'] = ticketid
    return redirect ( url_for('update') )

@app.route( '/modify', methods = ['POST'] )
def modify():
    a = request.get_json()
    count_enter_in = a['count']
    if 'username' not in session:
    	session['count'] = count_enter_in
    	return redirect ( url_for('check') )
    user_ID = session['username']
    user_ID = bytes.decode(user_ID)
    # Get json
    canvas   = a['canvas'][0]
    position = canvas['x'] % Length + (canvas['y'] % Width) * Length
    color    = int( canvas['color'] )
    count    = int( conn.get("count") )
    time1    = time.time()
    
    # Operate
    remaining, Mark = operation( conn, count, position, color, time1, user_ID )
    
    # get data of update
    list_modify    = []
    update_canvas( list_modify, conn, count_enter_in, count )

    # Mark == 1 means that this operation fails.
    # Return the data of update
    if Mark == 1 :
        return jsonify( data = list_modify, count = count, remaingTime = remaining, flag = False, CAS = True)

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
        canvasDict.append(data)
    list_modify.append(data)
    
    return jsonify( data = list_modify, count = count, remaingCount = remaining, flag = True, CAS = True )

@app.route('/update', methods = ['GET'])
def update():
	CAS = True
    if 'count' in session :
        count_current = session['count']
        session.pop('count')
        CAS = False
    else :
    	count_current = int( request.args.get('count') )
    count = int( conn.get('count') )
    list_modify = []
    # Refresh
    if count_current == -1 :
        # list_modify = response_refresh( conn, count, canvasStatus)
        return jsonify( data = canvasDict, count = count, flag = True, CAS = True)
    # Update
    update_canvas( list_modify, conn, count_current , count )
    return jsonify( data = list_modify, count = count, flag = True, CAS = CAS )