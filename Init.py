import redis
from random import randint
redis_db = redis.Redis( host='127.0.0.1', port=6379, db=0 )

p = redis_db.pipeline()
# fill in x1, x2+1
for x in range(100,110):
	# fill in y1, y2+1
    for y in range(100,110):
    	position = x + y * 300
    	p.zadd("canvas:", position, randint(0,0xFFFFFF) )
p.execute()