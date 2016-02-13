# encoding: utf-8

from .base import GetterSetter


class ContentMime(GetterSetter):
	foreign = 'Content-Type'
	getter = 'get_content_type'
	setter = 'set_type'


class ContentEncoding(GetterSetter):
	foreign = 'Content-Type'
	getter = 'get_charset'
	setter = 'set_charset'
