# -*- coding: utf-8 -*-
"""
Created on Tue May  2 11:47:47 2017

@author: mmmmm
"""
#import redis
#from random import randint
#import json,requests

#r=redis.Redis(host='localhost',port=6379,db=0)
#import time


time1 = time.time()
for i in range(1,500):
    x = randint(1,200)
    y = randint(1,200)
    color = randint(0,0xffffff)
    count = eval(r.get('count'))
    a = {
    "canvas":[{
        "x": x,
        "y": y,
        "color": color
    }],
    "count":count
    }
    b = json.dumps(a)
    requests.post("http://127.0.0.1:5000/canvas/modify",json=b)
    #print(json.loads(data.text))
time2 = time.time()
print(time2-time1)



#time1=time.time()
#    requests.get('http://127.0.0.1:5000')
#    time2=time.time()
#    time_test.append(time2 - time1)
#x = randint(1,200)
#    y = randint(1,200)
#    color = randint(0,0xffffff)