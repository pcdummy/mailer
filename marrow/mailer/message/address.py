# encoding: utf-8

from .base import GetterSetter
from .header import Header


class SenderAddress(GetterSetter):
	getter = 'get_unixfrom'
	setter = 'set_unixfrom'


class Address(Header):
	pass


class Addresses(Header):
	pass
