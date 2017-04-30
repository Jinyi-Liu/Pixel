# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 22:37:39 2017

@author: mmmmm
"""


Limit_Minutes_In_Seconds = 3*60

error1 = {
    'flag':0
}

Length = 200
Width = 200

def init_canvas( conn ):
    p = conn.pipeline()
    for i in range( 1, Length * Width + 1 ):
        conn.zadd( 'canvas:', i, 0xFFFFFF )
    p.execute()   
    
# def update_modify_time( conn, user ):
    # conn.zadd( 'time:', user, int(time.time()) )   #update the user'stime

def operated_position_record( conn, position ):
    conn.zincrby( 'operated_positon:', position )  #plus 1 to the given positon

def modify_canvas( conn, position, color ):    #position is a integer & color is from 0 to 0xffffff
    conn.zadd( 'canvas:', position, color )

def operation_record( conn, count, position, color, time1):
    conn.hset( count, 'x',     position % Length      )
    conn.hset( count, 'y',     position // Length + 1 )
    conn.hset( count, 'color', color               )
    conn.hset( count, 'time' , time1               )

def operation( conn, count, position, color, time1 ):
    # cutoff = time.time() - Limit_Minutes_In_Seconds
    # if conn.zscore('time:',user) == None :    #interval should be 3 minutes.
    #     pass
    # elif conn.zscore('time:',user) > cutoff :
    #     return 1
    # # update_modify_time ( p, user )
    #    
    p = conn.pipeline()
    modify_canvas ( p, position, color )
    operated_position_record ( p, position )
    operation_record( p, count, position, color, time1 )
    p.execute()

def update_canvas( conn, count_current, count ):
    list_modify = []
    while count_current < count:
        list_modify.append(conn.hgetall( count_current ))
        count_current += 1
    return list_modify