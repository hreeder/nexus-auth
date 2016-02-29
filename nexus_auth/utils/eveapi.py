from evelink import api
from pylibmc import Client
import time

class MemcacheCache(api.APICache):
	def __init__(self, config):
		super(MemcacheCache, self).__init__()
		self.mc = Client(config['MEMCACHE'])

	def get(self, key):
		return self.mc.get(key)
		
	def set(self, key, value, duration):
		if duration < 0:
			duration = time.time() + duration
		self.mc.set(key, value, time=duration)
