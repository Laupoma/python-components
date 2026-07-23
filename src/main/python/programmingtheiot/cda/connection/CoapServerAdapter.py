#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# Copyright (c) 2020 by Andrew D. King
# 

import logging
import traceback

from threading import Thread
from time import sleep

from coapthon.server.coap import CoAP
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.cda.connection.handlers.GetTelemetryResourceHandler import GetTelemetryResourceHandler
from programmingtheiot.cda.connection.handlers.UpdateActuatorResourceHandler import UpdateActuatorResourceHandler
from programmingtheiot.cda.connection.handlers.GetSystemPerformanceResourceHandler import GetSystemPerformanceResourceHandler

class CoapServerAdapter():
	"""
	Definition for a CoAP communications server, with embedded test functions.
	"""

	def __init__(self, dataMsgListener = None):
		self.config          = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False

		self.host = self.config.getProperty(
			ConfigConst.COAP_GATEWAY_SERVICE,
			ConfigConst.HOST_KEY,
			ConfigConst.DEFAULT_HOST)

		self.port = self.config.getInteger(
			ConfigConst.COAP_GATEWAY_SERVICE,
			ConfigConst.PORT_KEY,
			ConfigConst.DEFAULT_COAP_PORT)

		self.serverUri = f"coap://{self.host}:{self.port}"

		self.coapServer     = None
		self.coapServerTask = None

		self.listenTimeout = 30

		self._initServer()

		logging.info(f"CoAP server configured for host and port: {self.serverUri}")

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True
		return False

	def addResource(self, resourcePath: ResourceNameEnum = None, endName: str = None, resource = None):
		pass

	def startServer(self):
		if self.coapServer:
			logging.info("Starting CoAP server...")

			if self.coapServerTask and self.coapServerTask.is_alive():
				self.stopServer()
				self.coapServerTask = None

			self.coapServerTask = Thread(target = self._runServer)
			self.coapServerTask.daemon = True
			self.coapServerTask.start()

			logging.info("\n\n***** CoAP server started. *****\n\n")
		else:
			logging.warning("CoAP server not yet initialized (shouldn't happen).")

	def stopServer(self):
		if self.coapServer:
			logging.info("Stopping CoAP server...")
			self.coapServer.close()
			self.coapServerTask.join(5)
		else:
			logging.warning("CoAP server not yet initialized (shouldn't happen).")

	def _initServer(self):
		self.coapServer = CoAP(
			server_address = (self.host, self.port),
			multicast = False)

		logging.info("CoAP server initialized.")

	def _runServer(self):
		try:
			logging.info("CoAP server running...")
			self.coapServer.listen(self.listenTimeout)
		except Exception as e:
			traceback.print_exception(type(e), e, e.__traceback__)
			logging.warning("Failed to run CoAP server.")

