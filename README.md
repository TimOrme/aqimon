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

### Submitting a PR

Master branch is locked, but you can open a PR on the repo.  Build checks must pass, and changes approved by a code 
owner, before merging.

