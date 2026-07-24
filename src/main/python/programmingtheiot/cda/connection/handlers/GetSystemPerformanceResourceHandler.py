#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# Copyright (c) 2020 by Andrew D. King
# 

import logging

from coapthon import defines
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData

class GetSystemPerformanceResourceHandler(Resource, ISystemPerformanceDataListener):
	"""
	Observable resource that will collect system performance data based on the
	given name from the data message listener implementation.
	"""

	def __init__(self, name: str = ConfigConst.SYSTEM_PERF_MSG, coap_server = None, dataMsgListener: IDataMessageListener = None):
		super(GetSystemPerformanceResourceHandler, self).__init__( \
			name, coap_server, visible = True, observable = True, allow_children = True)

		self.pollCycles = \
			ConfigUtil().getInteger( \
				section = ConfigConst.CONSTRAINED_DEVICE, \
				key = ConfigConst.POLL_CYCLES_KEY, \
				defaultVal = ConfigConst.DEFAULT_POLL_CYCLES)

		self.dataUtil    = DataUtil()
		self.sysPerfData = SystemPerformanceData()

		self.dataMsgListener = dataMsgListener

		# reservado para lab module 10
		if self.dataMsgListener:
			self.dataMsgListener.setSystemPerformanceDataListener(self)

		# para testing
		self.payload = "GetSysPerfData"

	def render_GET_advanced(self, request, response):
		if request:
			response.code = defines.Codes.CONTENT.number

			if not self.sysPerfData:
				response.code = defines.Codes.EMPTY.number
				self.sysPerfData = SystemPerformanceData()

			jsonData = DataUtil().systemPerformanceDataToJson(self.sysPerfData)

			logging.info("Latest SystemPerformanceData JSON: " + jsonData)

			response.payload = (defines.Content_types["application/json"], jsonData)
			response.max_age = self.pollCycles

			# se activa en cap. 10
			self.changed = False

		return self, response

	def onSystemPerformanceDataUpdate(self, data: SystemPerformanceData) -> bool:
		self.sysPerfData = data
		return True
