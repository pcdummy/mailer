# encoding: utf-8

"""MIME-encoded electronic mail message class."""

from .header import nodefault, Header



class GetterSetter(object):
	__slots__ = ('index', 'default', 'rfc')
	
	getter = None  # Override these in subclasses.
	setter = None
	
	def __init__(self, default=nodefault, rfc=None):
		self.index = Header._index
		Header._index += 1
		
		self.default = default
		self.rfc = rfc
	
	def __repr__(self, extra=None):
		return '{self.__class__.__name__}({extra})'.format(
				self = self,
				es = ' ' if extra else '',
				extra = extra if extra else ''
			)
	
	def __get__(self, obj, cls=None):
		# If this is class attribute (and not instance attribute) access, we return ourselves.
		if obj is None: return self
		
		getter = getattr(obj._instance, self.getter)
		return self.to_native(obj, getter())
	
	def __set__(self, obj, value):
		if value is None and self.default is not nodefault:
			value = self.default
		
		setter = getattr(obj._instance, self.setter)
		setter(self.to_foreign(obj, value))
	
	def __delete__(self, obj):
		"""Executed via the ``del`` statement with a DataAttribute instance attribute as the argument."""
		
		setter = getattr(obj._instance, self.setter)
		setter(None if self.default is nodefault else self.default)
	
	def __prepare__(self, obj):
		if self.default is not nodefault:
			setter = getattr(obj._instance, self.setter)
			setter(self.default)
	
	def to_native(self, obj, value):
		return value
	
	def to_foreign(self, obj, value):
		return value
