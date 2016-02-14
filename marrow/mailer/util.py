# encoding: utf-8

"""Miscelaneous utilities for internal usage, and cross-compatibility aides."""

from collections import OrderedDict as odict

try:
	from itertools import chain, izip_longest as zipl
	iodict = odict.iteritems
	idict = dict.iteritems
	py = 2


except ImportError:
	from itertools import chain, zip_longest as zipl
	iodict = odict.items
	idict = dict.items
	py = 3


def _annotate(attribute):
	"""Annotate a class with an ordered mapping of indexed attributes."""
	
	def annotation_closure(cls):
		attr = getattr(cls, attribute)
		attrs = []
		
		for name in dir(cls):
			if name.startswith('_'): continue  # Skip private attributes.
			
			obj = getattr(cls, name)
			if not hasattr(obj, 'index'): continue  # Skip non-indexed attributes.
			if not hasattr(obj, 'foreign'): continue  # Only fields, please.
			
			attrs.append((name, obj))
		
		attrs.sort(key=lambda i: i[1].index)
		
		attr.update(attrs)
		
		return cls
	
	return annotation_closure
