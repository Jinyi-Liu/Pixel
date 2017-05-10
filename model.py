# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 22:37:39 2017

@author: mmmmm
"""
import time
Limit_Minutes_In_Seconds = 5*60
Limit_Operation = 10

Length = 300
Width  = 300

def init_canvas( conn ):
    p = conn.pipeline()
    for i in range( Length * Width ):
        conn.zadd( 'canvas:', i, int(0xF9FAFC) )
    p.execute()
    
def update_modify_time( conn, IP, time1 ):
    conn.zadd( 'time:', IP, time1 )   #update the user'stime

def update_modify_IP_count( conn, IP ):
    return conn.zincrby( 'already_count:', IP )

def init_modify_IP_count( conn, IP ):
    conn.zrem( 'already_count:', IP )

def operated_position_record( conn, position ):
    conn.zincrby( 'operated_position:', position )  #plus 1 to the given positon

def modify_canvas( conn, position, color ):    #position is a integer & color is from 0 to 0xffffff
    conn.zadd( 'canvas:', position, color )

def operation_record( conn, count, position, color, time1):
    conn.hset( count, 'x',     position %  Width   )
    conn.hset( count, 'y',     position // Length  )
    conn.hset( count, 'color', color               )
    conn.hset( count, 'time' , time1             )

def operation( conn, count, position, color, time1, IP ):
    now_time = time1
    modified_time = conn.zscore('time:', IP)
    if modified_time == None :
        Mark = 0
    else :
        remainingTime = int( (modified_time + Limit_Minutes_In_Seconds) - now_time )
        if remainingTime >= 0 :
            remainingCount = Limit_Operation - int(update_modify_IP_count( conn, IP ))     
            if remainingCount < 0 :
                Mark = 1
                return remainingTime, Mark
            else :
                Mark = 2
        else :
        	# Five minutes have passed
            Mark = 0

    p = conn.pipeline()
    # Haven't operated or five minutes have passed
    if not Mark :
    	init_modify_IP_count  ( p, IP )
    	update_modify_IP_count( p, IP )
    	update_modify_time    ( p, IP, time1 )
    	remainingCount = Limit_Operation - 1
    
    modify_canvas            ( p, position, color )
    operated_position_record ( p, position )
    operation_record         ( p, count, position, color, time1 )
    p.execute()
    return remainingCount, Mark

def update_canvas( list_modify, conn, count_current, count ):
    p = conn.pipeline()
    for i in range( count_current, count  ):
        p.hgetall( i )
    q = p.execute()
    for i in range( count - count_current ):
        data = {
        "color": int( q[i][b'color'] ),
        "x" :    int( q[i][b'x']     ),
        "y" :    int( q[i][b'y']     ),
        }
        list_modify.append(data)
    return list_modify

def refresh_canvas( conn, count, canvas1, canvas2, canvas3 ):
    time_current = int(time.time())
    time_last = conn.get('canvas_save_time')
    if time_last == None:
        time_sinceLast = 0
    else :
        time_sinceLast = time_current - int(time_last)

    if not conn.get('Updating') :
        pass
    elif int(conn.get('Updating')) == 1:
        return 2
    if (not conn.get("canvas_save")) or time_sinceLast > 30:
        conn.set( 'Updating' , 1)
        conn.set( 'update_db', 1)
        p = conn.pipeline()
        for i in range( Length * Width ):
            p.zscore('canvas:',i)
        q = p.execute()
        for i in range( Length * Width ):
            if int(q[i]) != 0xF9FAFC and i not in canvas1:
                canvas1.append( i )
        conn.set('canvas_save', 1)
        conn.set('canvas1_save_count', count)
        conn.set('canvas_save_time', int(time.time()))

        conn.set('update_db', 2)
        canvas2 = list.copy(canvas1)
        conn.set('canvas2_save_count', count)

        conn.set('update_db', 3)
        canvas3 = list.copy(canvas2)
        conn.set('canvas3_save_count', count)
        conn.set('Updating', 0)
        return 1

    return 0

def response_refresh( conn, count, canvas1, canvas2, canvas3 ):
    list_modify = []
    Status = int(conn.get('update_db'))
    if   Status == 3:
        canvas_save_count = int(conn.get('canvas1_save_count'))
        canvas_Now = canvas1
    elif Status == 1:
        canvas_save_count = int(conn.get('canvas2_save_count'))
        canvas_Now = canvas2
    elif Status == 2:
        canvas_save_count = int(conn.get('canvas3_save_count'))
        canvas_Now = canvas3
    update_canvas( list_modify, conn, canvas_save_count, count )

    canvas = []
    p = conn.pipeline()
    for i in canvas_Now:
        p.zscore("canvas:",i)
    q = p.execute()
    j = 0
    for i in canvas1 :
        canvas.append({
            "x": i % Width,
            "y": i// Length,
            "color": q[j],
            })
        j +=1
    return canvas + list_modify