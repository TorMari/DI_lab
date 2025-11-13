import pandas as pd
import random
from datetime import datetime, timedelta

num_users = 5000 
num_sesssions = 90000
rows = []

for i in range(num_sesssions):
    if random.random() < 0.9:
        user_id = 'user_main'
    else:
        user_id = f'user_{random.randint(1, num_users)}'
    session_id = f'session_{i}'
    start_time = datetime(2018, 12, 1) + timedelta(seconds=random.randint(0, 3000000))
    duration = random.randint(30, 3000)

    for _ in range(random.randint(20, 50)):
        ts = start_time + timedelta(seconds=random.randint(0, duration))
        rows.append((user_id, session_id, int(ts.timestamp() * 1000)))

pdf = pd.DataFrame(rows, columns=['user_id', 'session_id', 'event_timestamp'])
df = spark.createDataFrame(pdf)

print("Total number of events: ", df.count())

from pyspark.sql.functions import count, col
df.groupBy('user_id').agg(count('*').alias('events_per_user')).orderBy(col('events_per_user').desc()).show(5)


import time
from pyspark.sql.functions import max as mx, min as mn, avg as ag

start = time.time()

df1 = df.repartition(50, 'user_id')
result1 = df1.groupBy('user_id', 'session_id').agg((mx('event_timestamp') - mn('event_timestamp')).alias('session_duration'))
result1 = result1.agg(ag('session_duration').alias('avg_session_duration'))

result1.show()
time1 = time.time() - start
print(f"Time taken: {time1:.4f} s" )

#-----------------------------------------------------------------
start = time.time()
N = 8

df2 = df.repartition(N, 'session_id')
result2 = df2.groupBy('user_id', 'session_id').agg((mx('event_timestamp') - mn('event_timestamp')).alias('session_duration'))
result2 = result2.agg(ag('session_duration').alias('avg_session_duration'))

result2.show()
time2 = time.time() - start
print(f"Time taken: {time2:.4f} s")

#-----------------------------------------------------------------
best = min(time1, time2)
if best == time1:
    print(f"Best time (Високе перетасування): {best:.4f} s")
else:
    print(f"Best time (Низьке перетасування): {best:.4f} s")

#-----------------------------------------------------------------
speedup = time1 / time2
S_measured = speedup
B = (1- (1/S_measured - 1/N)) if S_measured else None

print(f"\nParallelism: {B:.4f}")
print(f"Teoretical max speedup for N = {N}: {1 / ((1-B) + B/N):.1f}x")

#------------------------------------------------------------------
from pyspark.sql.functions import count

df.groupBy('user_id').agg(count('*').alias('events_per_user')) \
    .orderBy(col('events_per_user').desc()).show(5)
