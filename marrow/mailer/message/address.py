# encoding: utf-8

from .base import GetterSetter
from .header import Header


class SenderAddress(GetterSetter):
	getter = 'get_unixfrom'
	setter = 'set_unixfrom'
	
	def to_foreign(self, obj, value):
		if isinstance(value, list):
			raise ValueError("Only a single sender is permitted.")
		
		return value


class Address(Header):
	pass


class Addresses(Header):
	pass
