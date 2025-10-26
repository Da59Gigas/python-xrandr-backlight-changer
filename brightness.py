#!/usr/bin/env python3
# coding=utf-8

# the name of the service is "py_mntbrt"
# TODO: write a better global docstring
# TODO: Check all the print statements and make them only pring when on verbose mode (TO ADD)

from pyinotify import WatchManager, Notifier, ProcessEvent, Event
from subprocess import run, CalledProcessError
from importlib import import_module
from sys import exit as _exit
from types import ModuleType
from typing import Tuple

# My IDE was whining about IN_MODIFY not existing, but it does, I checked with dir.
# But just in case, I checked what it was, it was a <class 'int'> with value 2, so I made the check.
pyinotify_temp: ModuleType = import_module("pyinotify")
if "IN_MODIFY" in dir(pyinotify_temp):
	# noinspection PyUnresolvedReferences
	from pyinotify import IN_MODIFY
else:
	IN_MODIFY: int = 2
del pyinotify_temp


def exit_(code: int) -> None:
	"""
	Exit the program with a given exit code.
	:param code: The exit code (as an integer) to use when exiting the program.
	:return: None
	"""
	print("[*] Exitting...")
	_exit(code)


def get_brightness_from_file(file_path: str) -> float | None:
	"""
	Read the brightness value from a specified file.
	It reads the first line and expects an integer or a float to be alone, followed possibly by a newline character.

	:param file_path: String containing the path to the file to analyze.
	:return: The brightness value as a float, or None if an error occurs.
	"""
	try:
		with open(file_path, mode='rt') as file:
			brightness_value: float = float(file.readline().strip())
			return brightness_value
	except Exception as e:
		print(f"Error reading brightness from file: {e.__class__}")
		return None


def set_brightness(value: float, debug_mode: bool = True) -> int:
	"""
	    Set the screen brightness by calling a subprocess and using the xrandr command.

	    :param value: The desired brightness value (0 to 99).
	    :param debug_mode: If True, print debug information.
	    :return: 0 if successful, -1 if an error occurs.
	"""
	max_brightness: float = 99.0  # Set maximum brightness possible to get from file to 99
	offset: float = 0.15
	normalized_value: value = value / max_brightness + offset
	# FIXME: eDP was the name of my laptop screen, so it might need changing
	command: str = f"xrandr --output eDP --brightness {normalized_value}"
	try:
		run(command, shell=True, check=True)
		if debug_mode:
			print(f"Brightness set to {normalized_value:.2f}")
		return 0
	except CalledProcessError as e:
		if debug_mode:
			print(f"Error setting brightness: {e}")
		return -1


class EventHandler(ProcessEvent):
	def __init__(self, BRIGHTNESS_FILE_PATH: str, debug_mode: bool = False) -> None:
		"""
		Handle file modification events, specificly on one file.

		:param BRIGHTNESS_FILE_PATH: The path to the brightness file.
		:param debug_mode: If True, enable debug output.
		"""
		super(EventHandler, self).__init__()
		self.BRIGHTNESS_FILE_PATH: str = BRIGHTNESS_FILE_PATH
		self.debug_mode: bool = debug_mode

	# noinspection PyUnusedLocal
	def process_IN_MODIFY(self, *event: Tuple[Event]) -> None:
		"""
		Process the IN_MODIFY event to update brightness.

		:param event: Ignored context data provided by pyinotify
		:return: None
		"""
		print("Brightness file modified. Updating... (", end="")
		brightness_value: float = get_brightness_from_file(self.BRIGHTNESS_FILE_PATH)
		print(f"{brightness_value})")
		if brightness_value is not None:
			set_brightness(brightness_value, self.debug_mode)


# noinspection PyUnboundLocalVariable
def main() -> None:
	"""
	Main function to initialize and run the brightness control service.

	:return: None
	"""
	# setting up...
	print("[*] Starting...")
	print("[*] Initializing constants:")
	try:
		print("[*] \tBRIGHTNESS_FILE_PATH = ", end="")
		# FIXME: Chage this path if, in this case you mentioned an nvidea brigthness file
		BRIGHTNESS_FILE_PATH: str = "/sys/class/backlight/acpi_video0/brightness"
		print(BRIGHTNESS_FILE_PATH)
		print("[*] \tDEBUG_MODE = ", end="")
		DEBUG: bool = False
		print(DEBUG)
	except Exception as error:
		print(f"[!] An error has ocurred! ({error.__class__})")
		exit_(-1)
	print("[*] Constants initialized with no detected error")

	# on boot
	print("[*] Testing screen brightness control")
	try:
		print("[*] \tGetting brightness value...")
		_temp: float = get_brightness_from_file(BRIGHTNESS_FILE_PATH)
		print(f"[*] \t\tFOUND: {_temp}")
		if not _temp:
			print("[!] Invalid value found!")
			exit_(-1)
		print("[*] Attempting to set screen brightenness...")
		set_brightness(_temp, DEBUG)
		print("[*] \tFinished.")
	except Exception as error:
		print(f"[!] An error has ocurred! ({error.__class__})")
		exit_(-1)
	print("[*] Screen brightness control test completed with no detected errors")

	# Initialize pyinotify handler
	print("[*] Initializing pynotify handler")
	try:
		print("[*] \tCreating 'WhatchManager'...")
		wm = WatchManager()
		print("[*] \t\tFinished.")
		print("[*] \tAdding hook to BRIGHTNESS_FILE_PATH for modifications...")
		wm.add_watch(BRIGHTNESS_FILE_PATH, IN_MODIFY)
		print("[*] \t\tFinished.")
		print("[*] \tCreating handler for the events...")
		handler = EventHandler(BRIGHTNESS_FILE_PATH, DEBUG)
		print("[*] \t\tFinished.")
		print("[*] \tCreating bridge between handler and watcher...")
		notifier = Notifier(wm, handler)
		print("[*] \t\tFinished.")
	except Exception as error:
		print(f"[!] An error has ocurred! ({error.__class__})")
		exit_(-1)
	print("[*] Pynotify initialized with no detected errors")

	print("[*] Starting main loop...")
	try:
		notifier.loop()
	except KeyboardInterrupt:
		print("Stopping monitoring.")


if __name__ == "__main__":
	try:
		main()
	except Exception as elo:
		print("[!!] PANIC!: Crytical failure in program:")
		print(f"{elo.__class__}")
		print(f"{elo.__cause__}")
		print(f"{elo}")
		_exit(-2)
	print("[*] Exitting...")
	_exit(0)
