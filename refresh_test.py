# -*- coding: utf-8 -*-
"""
Created on Tue May  2 13:51:08 2017

@author: mmmmm
"""

import numpy as np
import requests
import time
time_test = []
for j in range(10):
    time1=time.time()
    requests.get('http://127.0.0.1:5000')
    #p = r.pipeline()
    #for i in range(1,40001):
    #    p.zscore('canvas:',i)
    #q = p.execute()
    time2=time.time()
    time_test.append(time2 - time1)
    
print( np.array(time_test).mean())

#