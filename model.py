# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 22:37:39 2017

@author: mmmmm
"""

import time
Limit_Minutes_In_Seconds = 5*60
Limit_Operation = 10
error1 = {
    'flag':0
}


Length = 200
Width  = 200

def init_canvas( conn ):
    p = conn.pipeline()
    for i in range( Length * Width ):   # [0, 39999]
        conn.zadd( 'canvas:', i, int(0xF9FAFC) )
    p.execute()
    
def update_modify_time( conn, IP, time1 ):
    conn.zadd( 'time:', IP, time1 )   #update the user'stime

def update_modify_IP_count( conn, IP ):
    return int( conn.zincrby( 'remaining_count:', IP ) )

def init_modify_time_IP( conn, IP ):
    conn.zrem( 'time:', IP )

def operated_position_record( conn, position ):
    conn.zincrby( 'operated_position:', position )  #plus 1 to the given positon

def modify_canvas( conn, position, color ):    #position is a integer & color is from 0 to 0xffffff
    conn.zadd( 'canvas:', position, color )

def operation_record( conn, count, position, color, time1):
    conn.hset( count, 'x',     position %  Width   )
    conn.hset( count, 'y',     position // Length  )
    conn.hset( count, 'color', color               )
    conn.hset( count, 'time' , time1               )

def operation( conn, count, position, color, time1, IP ):
    now_time = time1
    modified_time = conn.zscore('time:', IP)
    if modified_time == None :
        update_modify_IP_count( conn, IP )
        Mark = 0
    else :
        remainingTime = (modified_time + Limit_Minutes_In_Seconds) - now_time
        if remainingTime >= 0 :
            remainingCount = Limit_Operation - update_modify_IP_count( conn, IP )
            Mark = 1
            if remaingCount == 0 :
                return remainingTime, Mark
        else :
            update_modify_time ( conn, IP, time1 )
            remainingCount = Limit_Operation - 1

    # Mark == 1 means that this operation fails.
    p = conn.pipeline()
    modify_canvas            ( p, position, color )
    operated_position_record ( p, position )
    operation_record         ( p, count, position, color, time1 )    
    p.execute()
    return remaingCount, Mark

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
        "time" : int( q[i][b'time']  )
        }
        list_modify.append(data)
    return list_modify

def refresh_canvas( list_refresh, conn ):
    list_refresh = []
    p = conn.pipeline()
    for i in range( Length * Width ):
        p.zscore('canvas:',i)
    q = p.execute()
    for i in range( Length * Width ):
        dot = {
        "x": i %  Width,
        "y": i // Length,
        "color":  int(q[i])
        }
        list_refresh.append(dot)
    return list_refresh