from datetime import datetime, timedelta

import databases


async def get_latest_stats(dbconn: databases.Database):
    result = await dbconn.fetch_one("SELECT * FROM aqi_log ORDER BY event_time DESC LIMIT 1")
    if result:
        return result[0], result[1], result[2], result[3]
    else:
        return 0, 0, 0, 0


async def get_all_stats(dbconn: databases.Database):
    result = await dbconn.fetch_all("SELECT * FROM aqi_log ORDER BY event_time ASC")
    return result


async def clean_old(dbconn: databases.Database, retention_minutes: int):
    last_week = datetime.now() - timedelta(minutes=retention_minutes)
    last_week_timestamp = int(last_week.timestamp())
    await dbconn.execute("DELETE FROM aqi_log WHERE event_time < :last_week_timestamp", values={"last_week_timestamp": last_week_timestamp})


async def add_entry(dbconn: databases.Database, event_time, epa_aqi_pm25, raw_pm25, raw_pm10):
    formatted_time = int(event_time.timestamp())
    await dbconn.execute(query="INSERT INTO aqi_log VALUES (:formatted_time, :epa_aqi_pm25, :raw_pm25, :raw_pm10)",
                   values={"formatted_time": formatted_time,
                           "epa_aqi_pm25": epa_aqi_pm25,
                           "raw_pm25": raw_pm25,
                           "raw_pm10": raw_pm10})


async def create_tables(dbconn: databases.Database):
    # Create table
    await dbconn.execute('''CREATE TABLE IF NOT EXISTS aqi_log (event_time integer, epa_aqi_pm25 real, raw_pm25 real, raw_pm10 real)''')
    await dbconn.execute('''CREATE INDEX IF NOT EXISTS aqi_eventtime ON aqi_log (event_time)''')
