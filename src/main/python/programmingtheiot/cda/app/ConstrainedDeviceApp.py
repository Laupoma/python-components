#####
#
# This class is part of the Programming the Internet of Things project.
#
import logging
from time import sleep

from programmingtheiot.cda.app.DeviceDataManager import DeviceDataManager

logging.basicConfig(format = '%(asctime)s:%(name)s:%(levelname)s:%(message)s', level = logging.DEBUG)

class ConstrainedDeviceApp():

	def __init__(self):
		logging.info("Initializing CDA...")
		self.devDataMgr = DeviceDataManager()

	def startApp(self):
		logging.info("Starting CDA...")
		self.devDataMgr.startManager()
		logging.info("CDA started.")

	def stopApp(self, code: int):
		logging.info("CDA stopping...")
		self.devDataMgr.stopManager()
		logging.info("CDA stopped with exit code %s.", str(code))

	def parseArgs(self, args):
		logging.info("Parsing command line args...")

def main():
	cda = ConstrainedDeviceApp()
	cda.startApp()
	sleep(10)
	cda.stopApp(0)

if __name__ == '__main__':
	main()
