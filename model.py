# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 22:37:39 2017

@author: mmmmm
"""
import time
import urllib
import bs4
Limit_Minutes_In_Seconds = 5*60
Limit_Operation = 20

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

def operation_record( conn, count, position, color, time1, IP):
    conn.hset( count, 'x',     position %  Width   )
    conn.hset( count, 'y',     position // Length  )
    conn.hset( count, 'color', color               )
    conn.hset( count, 'time' , time1               )
    conn.hset( count, 'IP' ,   IP                  )

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

    p.zincrby("operationRecord_IP", IP)
    modify_canvas            ( p, position, color )
    operated_position_record ( p, position )
    operation_record         ( p, count, position, color, time1, IP )
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
        "y" :    int( q[i][b'y']     )
        }
        list_modify.append(data)
    return list_modify

def response_refresh( conn, count, canvasStatus):
    canvas = []
    p = conn.pipeline()
    for i in canvasStatus:
        p.zscore("canvas:",i)
    q = p.execute()
    j = 0
    for i in canvasStatus :
        canvas.append({
            "x": i % Width,
            "y": i// Length,
            "color": int(q[j])
            })
        j += 1
    return canvas

TICKET_OK = 0
TICKET_INVALID = 1

def validate_cas_1(cas_host, service_url, ticket):
    """Validate ticket using cas 1.0 protocol."""
    #  Second Call to CAS server: Ticket found, verify it.
    cas_validate = cas_host + "/serviceValidate?ticket=" + ticket + "&service=" + service_url
    f_validate = urllib.request.urlopen(cas_validate)
    #  Get first line - should be yes or no
    response = f_validate.readline()
    ticket_status = int( b'Success' in f_validate.readline() )
    ticketid = f_validate.readline()
    index = ticketid.index( b'>' ) + 1
    ticketid = ticketid[ index : index+10 ]
    f_validate.close()
    return ticket_status, ticketid

# https://passport.ustc.edu.cn/serviceVal
# idate?id=1&ticket=ST-6a2e72e9a038c6e752500fa0fb16079c&service=http://home.ustc.edu.cn/~jm123456/cas/index.html?id=1
def validate_cas_2(cas_host, service_url, ticket, opt):
    """
    Validate ticket using cas 2.0 protocol
    The 2.0 protocol allows the use of the mutually exclusive "renew" and "gateway" options.
    """
    #  Second Call to CAS server: Ticket found, verify it.
    cas_validate = cas_host + "/serviceValidate?ticket=" + ticket + "&service=" + service_url
    if opt:
        cas_validate += "&{}=true".format(opt)
    f_validate = urllib.request.urlopen(cas_validate)
    #  Get first line - should be yes or no
    response = f_validate.read()
    ticketid = _parse_tag(response, "cas:user")
    #  Ticket does not validate, return error
    if ticketid == "":
        return TICKET_INVALID, ""
    #  Ticket validates
    else:
        return TICKET_OK, ticketid

def _parse_tag(string, tag):
    """
    Used for parsing xml.  Search string for the first occurence of <tag>.....</tag> and return text (stripped
    of leading and tailing whitespace) between tags.  Return "" if tag not found.
    """
    soup = bs4.BeautifulSoup(string, "xml")
    if soup.find(tag) is None:
        return ''
    return soup.find(tag).string.strip()