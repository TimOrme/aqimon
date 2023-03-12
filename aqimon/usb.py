import subprocess
import pathlib
import asyncio

UHUB_CTL_PATH = "uhubctl"


class UhubCtlNotInstalled(Exception):
    def __init__(self):
        super().__init__("Unable to find uhubctl on path")


async def turn_on_usb():
    if not _uhubctl_installed():
        raise UhubCtlNotInstalled()
    await _run(UHUB_CTL_PATH, ["-l", "1-1", "-a", "on", "-p", "2"])


async def turn_off_usb():
    if not _uhubctl_installed():
        raise UhubCtlNotInstalled()
    await _run(UHUB_CTL_PATH, ["-l", "1-1", "-a", "off", "-p", "2"])


def _uhubctl_installed() -> bool:
    return pathlib.Path(UHUB_CTL_PATH).exists()


async def _run(command, args):
    proc = await asyncio.create_subprocess_exec(
        program=command,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise Exception(f"Error running {command}, with args {args}")
