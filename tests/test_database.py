import pytest
import pytest_asyncio
import databases

from aqimon import database
from datetime import timedelta, datetime


@pytest_asyncio.fixture
async def database_conn():
    """Fixture to set up the in-memory database with test data."""
    dbconn = databases.Database("sqlite+aiosqlite://:memory:", force_rollback=True)
    await dbconn.connect()
    await database.create_tables(dbconn)
    yield dbconn
    await dbconn.disconnect()


@pytest.mark.asyncio
async def test_get_latest_read(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    await database.add_read(database_conn, current_time - timedelta(hours=2), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=4), pm10=2, pm25=3)

    result = await database.get_latest_read(database_conn)
    assert result.pm10 == 1.0
    assert result.pm25 == 2.0
    assert result.event_time == current_time - timedelta(hours=2)


@pytest.mark.asyncio
async def test_get_latest_read_no_data(database_conn):
    result = await database.get_latest_read(database_conn)
    assert result.pm10 == 0.0
    assert result.pm25 == 0.0
    assert result.event_time is not None


@pytest.mark.asyncio
async def test_get_latest_epa_aqi(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=2),
        epa_aqi=3.5,
        read_count=3,
        pollutant="PM25",
        oldest_read_time=current_time - timedelta(days=3),
    )
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=4),
        epa_aqi=3.7,
        read_count=5,
        pollutant="PM25",
        oldest_read_time=current_time - timedelta(days=3),
    )

    result = await database.get_latest_epa_aqi(database_conn)
    assert result.epa_aqi == 3.5
    assert result.event_time == current_time - timedelta(hours=2)


@pytest.mark.asyncio
async def test_get_latest_epq_aqi_no_data(database_conn):
    result = await database.get_latest_epa_aqi(database_conn)
    assert result.epa_aqi == 0
    assert result.event_time is not None


@pytest.mark.asyncio
async def test_get_all_reads(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    await database.add_read(database_conn, current_time - timedelta(hours=1), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=2), pm10=2, pm25=3)
    await database.add_read(database_conn, current_time - timedelta(hours=3), pm10=3, pm25=4)

    result = await database.get_all_reads(database_conn, lookback=None)
    assert len(result) == 3
    assert result[2].pm10 == 1.0
    assert result[2].pm25 == 2.0
    assert result[2].event_time == current_time - timedelta(hours=1)

    assert result[0].pm10 == 3.0
    assert result[0].pm25 == 4.0
    assert result[0].event_time == current_time - timedelta(hours=3)


@pytest.mark.asyncio
async def test_get_all_reads_with_window(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    await database.add_read(database_conn, current_time - timedelta(hours=1), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=2), pm10=2, pm25=3)
    await database.add_read(database_conn, current_time - timedelta(hours=3), pm10=3, pm25=4)

    result = await database.get_all_reads(database_conn, current_time - timedelta(hours=2, minutes=30))
    assert len(result) == 2
    assert result[1].pm10 == 1.0
    assert result[1].pm25 == 2.0
    assert result[1].event_time == current_time - timedelta(hours=1)

    assert result[0].pm10 == 2.0
    assert result[0].pm25 == 3.0
    assert result[0].event_time == current_time - timedelta(hours=2)


@pytest.mark.asyncio
async def test_get_all_epa_aqi(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=1),
        epa_aqi=2,
        pollutant="PM25",
        read_count=5,
        oldest_read_time=current_time - timedelta(days=3),
    )
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=2),
        epa_aqi=3,
        pollutant="PM10",
        read_count=20,
        oldest_read_time=current_time - timedelta(days=60),
    )
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=3),
        epa_aqi=4,
        pollutant="PM25",
        read_count=10,
        oldest_read_time=current_time - timedelta(days=30),
    )

    result = await database.get_all_epa_aqis(database_conn, lookback=None)
    assert len(result) == 3
    assert result[2].epa_aqi == 2.0
    assert result[2].read_count == 5
    assert result[2].pollutant == "PM25"
    assert result[2].oldest_read_time == current_time - timedelta(days=3)
    assert result[2].event_time == current_time - timedelta(hours=1)

    assert result[0].epa_aqi == 4.0
    assert result[0].read_count == 10
    assert result[0].pollutant == "PM25"
    assert result[0].oldest_read_time == current_time - timedelta(days=30)
    assert result[0].event_time == current_time - timedelta(hours=3)


@pytest.mark.asyncio
async def test_get_all_epa_aqi_with_window(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=1),
        epa_aqi=2,
        pollutant="PM25",
        read_count=5,
        oldest_read_time=current_time - timedelta(days=3),
    )
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=2),
        epa_aqi=3,
        pollutant="PM10",
        read_count=20,
        oldest_read_time=current_time - timedelta(days=60),
    )
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=3),
        epa_aqi=4,
        pollutant="PM25",
        read_count=10,
        oldest_read_time=current_time - timedelta(days=30),
    )

    result = await database.get_all_epa_aqis(database_conn, current_time - timedelta(hours=2, minutes=30))
    assert len(result) == 2
    assert result[1].epa_aqi == 2.0
    assert result[1].read_count == 5
    assert result[1].pollutant == "PM25"
    assert result[1].oldest_read_time == current_time - timedelta(days=3)
    assert result[1].event_time == current_time - timedelta(hours=1)

    assert result[0].epa_aqi == 3.0
    assert result[0].read_count == 20
    assert result[0].pollutant == "PM10"
    assert result[0].oldest_read_time == current_time - timedelta(days=60)
    assert result[0].event_time == current_time - timedelta(hours=2)


@pytest.mark.asyncio
async def test_get_averaged_reads(database_conn):
    # Add reads every two hours
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    lookback_to = current_time - timedelta(hours=8)
    await database.add_read(database_conn, current_time - timedelta(hours=2), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=4), pm10=2, pm25=3)
    await database.add_read(database_conn, current_time - timedelta(hours=6), pm10=3, pm25=4)
    await database.add_read(database_conn, current_time - timedelta(hours=8), pm10=4, pm25=5)

    result = await database.get_averaged_reads(database_conn, lookback_to)
    assert result.count == 4
    assert result.avg_pm10 == 2.5
    assert result.avg_pm25 == 3.5
    assert result.oldest_read_time == current_time - timedelta(hours=8)


@pytest.mark.asyncio
async def test_get_averaged_reads_looks_past(database_conn):
    current_time = datetime(2020, 1, 1, 12, 0, 0)
    lookback_to = current_time - timedelta(hours=8)
    await database.add_read(database_conn, current_time - timedelta(hours=6), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=7), pm10=2, pm25=3)
    # Should be included since its the read just after the lookback
    await database.add_read(database_conn, current_time - timedelta(hours=8, minutes=5), pm10=3, pm25=4)
    # Should be excluded
    await database.add_read(database_conn, current_time - timedelta(hours=9), pm10=4, pm25=5)

    result = await database.get_averaged_reads(database_conn, lookback_to)
    assert result.count == 3
    assert result.avg_pm10 == 2.0
    assert result.avg_pm25 == 3.0
    assert result.oldest_read_time == current_time - timedelta(hours=8, minutes=5)


@pytest.mark.asyncio
async def test_clean_old(database_conn):
    current_time = datetime.now()
    await database.add_read(database_conn, current_time - timedelta(hours=2), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=4), pm10=2, pm25=3)
    # These should be deleted
    await database.add_read(database_conn, current_time - timedelta(hours=6), pm10=3, pm25=4)
    await database.add_read(database_conn, current_time - timedelta(hours=8), pm10=4, pm25=5)

    await database.clean_old(database_conn, retention_minutes=(60 * 4) + 30)

    result = await database.get_all_reads(database_conn, lookback=None)
    assert len(result) == 2
    assert result[0].event_time == (current_time - timedelta(hours=4)).replace(microsecond=0)
    assert result[1].event_time == (current_time - timedelta(hours=2)).replace(microsecond=0)


@pytest.mark.asyncio
async def test_add_read(database_conn):
    current_time = datetime.now()

    await database.add_read(database_conn, current_time - timedelta(hours=2), pm10=1, pm25=2)
    await database.add_read(database_conn, current_time - timedelta(hours=4), pm10=2, pm25=3)

    result = await database.get_all_reads(database_conn, lookback=None)
    assert len(result) == 2
    assert result[0].event_time == (current_time - timedelta(hours=4)).replace(microsecond=0)
    assert result[1].event_time == (current_time - timedelta(hours=2)).replace(microsecond=0)


@pytest.mark.asyncio
async def test_add_epa_read(database_conn):
    current_time = datetime.now()

    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=2),
        epa_aqi=2,
        pollutant="PM25",
        read_count=5,
        oldest_read_time=current_time - timedelta(days=3),
    )
    await database.add_epa_read(
        database_conn,
        current_time - timedelta(hours=4),
        epa_aqi=3,
        pollutant="PM10",
        read_count=20,
        oldest_read_time=current_time - timedelta(days=60),
    )

    result = await database.get_all_epa_aqis(database_conn, lookback=None)
    assert len(result) == 2
    assert result[0].event_time == (current_time - timedelta(hours=4)).replace(microsecond=0)
    assert result[1].event_time == (current_time - timedelta(hours=2)).replace(microsecond=0)
