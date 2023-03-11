import subprocess
import pathlib

UHUB_CTL_PATH = "uhubctl"


class UhubCtlNotInstalled(Exception):
    def __init__(self):
        super().__init__("Unable to find uhubctl on path")


def turn_on_usb():
    if not _uhubctl_installed():
        raise UhubCtlNotInstalled()
    subprocess.run([UHUB_CTL_PATH, "-l", "1-1", "-a", "on", "-p", "2"], check=True)


def turn_off_usb():
    if not _uhubctl_installed():
        raise UhubCtlNotInstalled()
    subprocess.run([UHUB_CTL_PATH, "-l", "1-1", "-a", "off", "-p", "2"], check=True)


def _uhubctl_installed() -> bool:
    return pathlib.Path(UHUB_CTL_PATH).exists()
