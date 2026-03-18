import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.data.BaseIotData import BaseIotData

class SystemPerformanceData(BaseIotData):

	def __init__(self, d = None):
		super(SystemPerformanceData, self).__init__(name = ConfigConst.SYSTEM_PERF_NAME, typeID = ConfigConst.SYSTEM_PERF_TYPE, d = d)
		
		self.cpuUtil = ConfigConst.DEFAULT_VAL
		self.memUtil = ConfigConst.DEFAULT_VAL

	def getCpuUtilization(self):
		return self.cpuUtil

	def getMemoryUtilization(self):
		return self.memUtil

	def setCpuUtilization(self, cpuUtil):
		self.cpuUtil = cpuUtil
		self.updateTimeStamp()

	def setMemoryUtilization(self, memUtil):
		self.memUtil = memUtil
		self.updateTimeStamp()

	def _handleUpdateData(self, data):
		if data and isinstance(data, SystemPerformanceData):
			self.cpuUtil = data.getCpuUtilization()
			self.memUtil = data.getMemoryUtilization()

	def __str__(self):
		return 'SystemPerformanceData: name={}, typeID={}, cpuUtil={}, memUtil={}'.format(
			self.name,
			self.typeID,
			self.cpuUtil,
			self.memUtil
		)
