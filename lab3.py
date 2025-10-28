import asyncio
import random
import json
import logging
from datetime import datetime, timedelta, timezone
import psycopg2


DB_CONFIG = {
    "dbname": "PipelineDB",
    "user": "postgres",
    "password": "**",
    "host": "localhost",
    "port": 5432,
}

NUM_EVENTS = 100
GEN_INTERVAL = 0.05
MAX_RETRIES = 3
RETRY_BASE = 0.1  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            event_id BIGINT PRIMARY KEY,
            sensor_id INT,
            ts TIMESTAMPTZ,
            value DOUBLE PRECISION,
            raw JSONB
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dlq (
            event_id BIGINT PRIMARY KEY,
            raw JSONB,
            reason TEXT,
            ts TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    cur.close()
    conn.close()
    logging.info("PostgreSQL tables initialized.")


SENSOR_IDS = list(range(1, 6))  

def mk_event(event_id: int, sensor_id: int, ts: str, value):
    return {
        "event_id": event_id,
        "sensor_id": sensor_id,
        "ts": ts,
        "value": value,
    }

def gen_error_event(counter: int):
    t = datetime.utcnow()
    event_id = counter
    sensor = random.choice(SENSOR_IDS)
    ts = (t - timedelta(seconds=random.randint(0, 5))).isoformat() + "Z"
    value = round(random.uniform(0, 100), 3)
    evt = mk_event(event_id, sensor, ts, value)

    ev_type = counter % 6

    if ev_type == 0:
        evt.pop("value", None)

    elif ev_type == 1:
        evt["value"] = " "

    elif ev_type == 2:
        duplicate_id = random.randint(0, counter - 1) if counter > 0 else 0
        evt["event_id"] = duplicate_id

    elif ev_type == 3:
        old = t - timedelta(minutes=10 + random.randint(0, 60))
        evt["ts"] = old.isoformat() + "Z"

    elif ev_type == 4:
        evt["value"] = 1e6

    return evt


def get_last_event_id():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(MAX(event_id), 0) FROM (
                SELECT event_id FROM sensor_data
                UNION ALL
                SELECT event_id FROM dlq
            ) AS all_events;
        """)
        last_id = cur.fetchone()[0] or 0
        cur.close()
        conn.close()
        return int(last_id)
    except Exception as e:
        logging.exception(f"Error reading last event_id: {e}")
        return 0


async def data_generator(out_q: asyncio.Queue, start_id: int):
    for i in range(start_id, start_id + NUM_EVENTS):
        if random.random() < 0.3:
            evt = gen_error_event(i)
        else:
            t = datetime.utcnow().isoformat() + "Z"
            evt = mk_event(i, random.randint(1, 6), t, round(random.uniform(10, 30), 3))
        await out_q.put(evt)
        await asyncio.sleep(GEN_INTERVAL)
    await out_q.put(None)
    logging.info(f"Data generation finished. Last event_id: {start_id + NUM_EVENTS - 1}")


def validate_event(event):
    try:
        ts_str = event["ts"].replace("Z", "+00:00")
        ts = datetime.fromisoformat(ts_str)
        now = datetime.now(timezone.utc)
        required = {"event_id", "sensor_id", "ts", "value"}
        missing = required - event.keys()
        if missing:
            return False, f"missing_fields: {','.join(missing)}"

        if ts < now - timedelta(hours=1):
            return False, "stale_timestamp"

        if not (-20 <= event["value"] <= 50):
            return False, "out_of_range"
            
        return True, None

    except Exception as e:
        return False, f"parse_error: {e}"


def persist_event(evt: dict):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sensor_data (event_id, sensor_id, ts, value, raw)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
        """, (
            evt["event_id"],
            evt["sensor_id"],
            evt["ts"],
            float(evt["value"]),
            json.dumps(evt, ensure_ascii=False)
        ))
        conn.commit()
        inserted = cur.rowcount > 0
        cur.close()
        conn.close()
        if inserted:
            return True, None
        else:
            return False, "duplicate_key"
    except Exception as e:
        return False, str(e)


def write_dlq(evt: dict, reason: str):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO dlq (event_id, raw, reason, ts)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (event_id)
            DO UPDATE SET raw = EXCLUDED.raw, reason = EXCLUDED.reason, ts = NOW();
        """, (
            evt.get("event_id", f"noid_{random.random()}"),
            json.dumps(evt, ensure_ascii=False),
            reason
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.exception(f"- Error writing DLQ: {e}")


async def validator_worker(in_q: asyncio.Queue, valid_q: asyncio.Queue, dlq_q: asyncio.Queue, metrics: dict):
    while True:
        evt = await in_q.get()
        if evt is None:
            await valid_q.put(None)
            in_q.task_done()
            break

        ok, reason = validate_event(evt)
        if ok:
            await valid_q.put(evt)
        else:
            await dlq_q.put((evt, reason))
            metrics["dlq"] += 1  
            logging.warning(f"- Validation failed for event {evt.get('event_id')}: {reason}")

        in_q.task_done()


async def persister_worker(in_q: asyncio.Queue, dlq_q: asyncio.Queue, metrics: dict):
    while True:
        evt = await in_q.get()
        if evt is None:
            in_q.task_done()
            break
        event_id = evt.get("event_id")
        attempt = 0
        while attempt <= MAX_RETRIES:
            success, err = persist_event(evt)
            if success:
                metrics["ingested"] += 1
                logging.info(f"+ Persisted event {event_id}")
                break
            elif err == "duplicate_key":
                metrics["duplicates"] += 1
                logging.info(f"- Duplicate skipped: event {event_id}")
                break
            else:
                attempt += 1
                if attempt > MAX_RETRIES:
                    metrics["dlq"] += 1
                    await dlq_q.put((evt, f"persist_fail:{err}"))
                    logging.error(f"- DLQ: failed to persist event {event_id}: {err}")
                    break
                backoff = RETRY_BASE * (2 ** (attempt - 1))
                logging.warning(f"Retry {attempt} for event {event_id} after {backoff:.2f}s")
                await asyncio.sleep(backoff)
        in_q.task_done()


async def dlq_worker(dlq_q: asyncio.Queue):
    while True:
        item = await dlq_q.get()
        if item is None:
            dlq_q.task_done()
            break
        evt, reason = item
        write_dlq(evt, reason)
        dlq_q.task_done()
        logging.info(f"- DLQ stored: event {evt.get('event_id')} ({reason})")


async def main():
    init_db()
    start_id = get_last_event_id() + 1  
    logging.info(f"Starting event generation")

    gen_q = asyncio.Queue()
    valid_q = asyncio.Queue()
    dlq_q = asyncio.Queue()
    metrics = {"ingested": 0, "duplicates": 0, "dlq": 0}

    tasks = [
        asyncio.create_task(data_generator(gen_q, start_id)),
        asyncio.create_task(validator_worker(gen_q, valid_q, dlq_q, metrics)),
        asyncio.create_task(persister_worker(valid_q, dlq_q, metrics)),
        asyncio.create_task(dlq_worker(dlq_q)),
    ]

    await asyncio.gather(*tasks[:1])
    await gen_q.join()
    await valid_q.join()
    await dlq_q.join()

    await dlq_q.put(None)

    logging.info("Pipeline completed.")
    logging.info(f"Metrics: {metrics}")



if __name__ == "__main__":
    asyncio.run(main())

















"""elapsed = time.perf_counter() - start_time
    logging.info(f"⏱ Pipeline completed in {elapsed:.2f} seconds.")
    logging.info(f"Metrics: {metrics}")
    logging.info(f"Throughput: {metrics['ingested'] / elapsed:.2f} events/sec")"""
