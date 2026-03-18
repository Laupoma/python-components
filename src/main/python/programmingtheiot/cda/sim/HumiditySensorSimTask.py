import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class HumiditySensorSimTask(BaseSensorSimTask):

	def __init__(self, dataSet = None):
		super( \
			HumiditySensorSimTask, self).__init__( \
				name = ConfigConst.HUMIDITY_SENSOR_NAME, \
				typeID = ConfigConst.HUMIDITY_SENSOR_TYPE, \
				dataSet = dataSet, \
				minVal = SensorDataGenerator.LOW_NORMAL_ENV_HUMIDITY, \
				maxVal = SensorDataGenerator.HI_NORMAL_ENV_HUMIDITY)
