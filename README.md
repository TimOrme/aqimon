# AQIMON

A simple Air Quality Index monitor, designed to work on the Raspberry Pi with the SDS011 Nova PM Sensor.

## Installation


### Pre-Requisites

* Python 3.9+
* [uhubctl](https://github.com/mvp/uhubctl) must be installed and on your PATH.

### Install

```commandline
pip install aqimon
```

## Running Aqimon

Aqimon is a simple web server.  To start with all the defaults, you can just run:

```commandline
aqimon
```

And then go to your browser at `http://{serveraddress}:8000/` to view the UI.

### Configure With Systemd

Generally, you'd want to run `Aqimon` as an always-on service, using `systemd`.

To do so, create a file at `/etc/systemd/system/aqimin.service` with the following contents:

```
[Unit]
Description=AQIMON
After=multi-user.target

[Service]
Type=simple
Restart=always
ExecStart=aqimon

[Install]
WantedBy=multi-user.target
```

And then run:

```commandline
sudo systemctl daemon-reload
sudo systemctl start aqimon
```

## Configuration

Aqimon uses environment variables for configuration, but all values should ship with sensible defaults.

| Variable                         | Default             | Description                                                                                                                       |
|----------------------------------|---------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **AQIMON_DB_PATH**               | ~/.aqimon/db.sqlite | The path to the database file, where read information is stored. It should be an absolute path; user home expansion is supported. | 
| **AQIMON_POLL_FREQUENCY_SEC**    | 900 (15 minutes)    | Sets how frequently to read from the device, in seconds.                                                                          |
| **AQIMON_RETENTION_MINUTES**     | 10080 (1 week)      | Sets how long data will be kept in the database, in minutes.                                                                      |
| **AQIMON_READER_TYPE**           | NOVAPM              | The reader type to use, either NOVAPM or MOCK.                                                                                    |
| **AQIMON_USB_PATH**              | /dev/ttyUSB0        | The path to the USB device for the sensor.                                                                                        |
| **AQIMON_SLEEP_TIME_SEC**        | 5                   | The number of seconds to wait for between each read in a set of reads.                                                            |
| **AQIMON_SAMPLE_COUNT_PER_READ** | 5                   | The number of reads to take with each sample.                                                                                     |
| **AQIMON_SERVER_PORT**           | 8000                | The port to run the server on.                                                                                                    |
| **AQIMON_SERVER_HOST**           | 0.0.0.0             | The host to run the server on.                                                                                                    |
 

## Contributing

### Toolset

To start developing, you'll need to install the following tools:

* [Python 3.9+](https://www.python.org/) - For API Code
* [Elm 0.19](https://elm-lang.org/) - For client code
* [poetry](https://python-poetry.org/) - For python package management
* [justfile](https://github.com/casey/just) - For builds
* [elm-format](https://github.com/avh4/elm-format) - For auto-formatting elm code.

Optionally, we have [pre-commit](https://pre-commit.com/) hooks available as well.  To install hooks, just run
`pre-commit install` and then linters and autoformatting will be applied automatically on commit.

### Quickstart

To build the project, and install all dev-dependencies, run:

```commandline
just build
```

To start the server in develop mode, run:

```commandline
poetry run aqimond
```

To compile elm changes, run:

```commandline
just compile_elm
```

To manually run lint checks on the code, run:

```commandline
just lint
```

To run auto-formatters, run:

```commandline
just format
```

### Using the Mock Reader

Aqimon ships with a mock reader class that you can use in the event that you don't have a reader available on your 
development computer.  The mock reader just returns randomized reads.  To use it, you can start the server like:

```commandline
AQIMON_READER_TYPE=MOCK poetry run aqimon
```

### Submitting a PR

Master branch is locked, but you can open a PR on the repo.  Build checks must pass, and changes approved by a code 
owner, before merging.

