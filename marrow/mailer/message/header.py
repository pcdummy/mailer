# encoding: utf-8

"""MIME-encoded electronic mail message class."""

from email.utils import format_datetime, parsedate_to_datetime, make_msgid


nodefault = object()


class Header(object):
	__slots__ = ('index', 'foreign', 'default', 'reset', 'rfc')
	
	_index = 0
	
	def __init__(self, foreign, default=nodefault, reset=True, rfc=None, index=0):
		self.index = Header._index + index
		Header._index += 1
		
		self.foreign = foreign
		self.default = default
		self.reset = reset
		self.rfc = None
	
	def __repr__(self, extra=None):
		return '{self.__class__.__name__}("{self.foreign}"{extra})'.format(
				self = self,
				es = ' ' if extra else '',
				extra = extra if extra else ''
			)
	
	def __get__(self, obj, cls=None):
		# If this is class attribute (and not instance attribute) access, we return ourselves.
		if obj is None: return self
		
		# Attempt to retrieve and return the data from the warehouse.
		try:
			return self.to_native(obj, obj._instance[self.foreign])
		except KeyError:
			if self.default is nodefault:
				raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(
						obj.__class__.__name__,
						self.__name__
					))
			return self.__default__(obj)
	
	def __set__(self, obj, value):
		value = self.to_foreign(obj, value)
		
		if value is None:
			if self.default is nodefault:
				return self.__delete__(obj)
			else:
				value = self.__default__(obj)
		
		if self.reset and self.foreign in obj._instance:
			obj._instance.replace_header(self.foreign, value)
		
		else:
			obj._instance[self.foreign] = value
	
	def __delete__(self, obj):
		"""Executed via the ``del`` statement with a DataAttribute instance attribute as the argument."""
		
		# Delete the data completely from the warehouse.
		del obj._instance[self.foreign]
		
		if self.foreign not in obj._instance and self.default is not nodefault:
			# No value remaining, but we have a default.
			obj._instance[self.foreign] = self.__default__(obj)
	
	def __default__(self, obj):
		return self.default() if callable(self.default) else self.default
	
	def __prepare__(self, obj):
		"""Assign the default value to the underlying instance."""
		if self.default is not nodefault:
			self.__set__(obj, self.default() if callable(self.default) else self.default)
	
	# Pseudo-Abstract API; Override these in subclasses.
	
	def to_native(self, obj, value):
		return value
	
	def to_foreign(self, obj, value):
		return value


class Priority(Header):
	def to_native(self, obj, value):
		return value if value is None else int(value)
	
	def to_foreign(self, obj, value):
		return str(value)


class Date(Header):
	def to_native(self, obj, value):
		return value if value is None else parsedate_to_datetime(value)
	
	def to_foreign(self, obj, value):
		return value if value is None else format_datetime(value)


class Domain(Header):
	def __set__(self, obj, value):
		obj._domain = value
		obj.id = None  # Trigger ID regeneration.
	
	def to_native(self, obj, value):
		return value.rpartition('@')[2].rstrip('>')


class Id(Header):
	def __default__(self, obj):
		return make_msgid(domain=obj._domain)
