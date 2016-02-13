# encoding: utf-8

"""MIME-encoded electronic mail message class."""

from .header import nodefault, Header


nodefault = object()


class Body(object):
	__slots__ = ('index', 'foreign', 'default', 'reset', 'rfc')
	
	def __init__(self, foreign, default=nodefault, reset=True, rfc=None):
		self.index = Header._index
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
		
		return obj._instance.get_body((self.foreign[1], ))
	
	def __set__(self, obj, value):
		if obj._instance.is_multipart() or obj._instance.get_payload() is not None or obj._instance.get_charset() == '/'.join(self.foreign):
			part = obj._instance.get_body((self.foreign[1], ))
			
			if part is None:
				if isinstance(value, bytes):
					obj._instance.add_alternative(value, charset=str(obj._instance.get_charset()), maintype=self.foreign[0], subtype=self.foreign[1])
				else:
					obj._instance.add_alternative(value, charset=str(obj._instance.get_charset()), subtype=self.foreign[1])
				return
			
			part.set_payload(value, charset=obj._instance.get_charset())
			return
		
		obj._instance.set_payload(value, charset=obj._instance.get_charset())
	
	def __delete__(self, obj):
		"""Executed via the ``del`` statement with a DataAttribute instance attribute as the argument."""
		
		obj._instan
	
	def __prepare__(self, obj):
		"""Assign the default value to the underlying instance."""
		if self.default is not nodefault:
			self.__set__(obj, self.default)
	
	# Pseudo-Abstract API; Override these in subclasses.
	
	def to_native(self, obj, value):
		return value
	
	def to_foreign(self, obj, value):
		return value
