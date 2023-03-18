"""Generic USB functions.

Used to control the USB hub for power savings, and ideally wear on the air quality monitor.  This lets us turn the
fan off when we're not using it.
"""
import pathlib
import asyncio

UHUB_CTL_PATH = "uhubctl"


class UhubCtlNotInstalled(Exception):
    """Exception raised if ububctl is not installed on the users path."""

    def __init__(self):
        """Init exception."""
        super().__init__("Unable to find uhubctl on path")


async def turn_on_usb():
    """Turn on the USB hub controller."""
    if not _uhubctl_installed():
        raise UhubCtlNotInstalled()
    # TODO: Device needs to be configurable here.
    await _run(UHUB_CTL_PATH, "-l", "1-1", "-a", "on", "-p", "2")


async def turn_off_usb():
    """Turn off the USB hub controller."""
    if not _uhubctl_installed():
        raise UhubCtlNotInstalled()
    # TODO: Device needs to be configurable here.
    await _run(UHUB_CTL_PATH, "-l", "1-1", "-a", "off", "-p", "2")


def _uhubctl_installed() -> bool:
    return pathlib.Path(UHUB_CTL_PATH).exists()


async def _run(*args):
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise Exception(f"Error running {args}")
