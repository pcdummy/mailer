# encoding: utf-8

"""MIME-encoded electronic mail message class."""

from collections import OrderedDict as odict
from datetime import datetime
from email.message import EmailMessage

from .. import release
from .header import nodefault, Header, Priority, Date, Domain, Id
from .content import ContentMime, ContentEncoding
from .address import SenderAddress, Address, Addresses
from .body import Body

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


@_annotate('_fields')
class Message(object):
	__slots__ = ('_instance', '_mailer', '_domain', 'defaults')
	
	_fields = odict()
	
	# Basic Message Metadata
	
	domain = Domain('Message-Id', rfc=None, index=100)
	id = Id('Message-Id', default=None, rfc=None, index=100)
	date = Date('Date', default=datetime.utcnow, rfc=None, index=100)
	subject = Header('Subject', rfc=None)
	to = Addresses('To', rfc=None)
	cc = Addresses('Cc', rfc=None)
	bcc = Addresses('Bcc', rfc=None)
	author = Address('From', rfc=None)
	authors = Addresses('From', rfc=None, index=100)
	sender = Address('Sender', rfc=None)
	
	# Content Metadata
	# Note: The meanings of `mime` and `encoding` have changed in Mailer 5!
	
	mime = ContentMime(default="text/plain", rfc=None)
	charset = ContentEncoding(default="UTF-8", rfc=None)
	encoding = Header('Content-Transfer-Encoding', default='quoted-printable', rfc=None)
	
	# Message Routing
	
	sender = SenderAddress(rfc=None)
	reply = Address('Reply-To', rfc=None)
	notify = Addresses('Disposition-Notification-To', rfc=None)
	
	# Advanced Message Metadata
	
	organization = Header('Organization', rfc=None)
	organisation = organization  # Convienent spelling difference.
	priority = Header('X-Priority', rfc=None)
	
	# Message Parts
	
	plain = Body(('text', 'plain'), rfc=None)
	rich = Body(('text', 'html'), rfc=None)
	
	# Internally used attributes
	_id = None
	
	# Default values
	#date = datetime.now()
	
	def __init__(self, *args, **kw):
		"""Instantiate a new Message object.
		
		No arguments are required, as everything can be set using class
		properties.  Alternatively, __everything__ can be set using the
		constructor, using named arguments.  The first three positional
		arguments can be used to quickly prepare a simple message.
		"""
		
		self._instance = EmailMessage()
		self._mailer = kw.pop('_mailer', None)
		self._domain = None  # Default to auto-detection.
		
		if kw.pop('brand', True):
			self._instance['X-Mailer'] = "marrow.mailer-{release.version} <{release.url}>".format(release=release)
		
		seen = set()
		
		for value, (name, field) in zipl(args, iodict(self._fields), fillvalue=nodefault):
			seen.add(name)
			
			if value is nodefault:
				if name in kw:
					setattr(self, name, kw.pop(name))
				else:
					field.__prepare__(self)
			
			else:
				setattr(self, name, value)
		
		if seen.intersection(kw):
			raise TypeError("Keyword arguments duplicate positional arguments: " + ", ".join(seen.intersection(kw)))
		
		for name, value in idict(kw):
			setattr(self, name, value)
	
	def __str__(self):
		return self._instance.as_string()
	
	def __bytes__(self):
		return self._instance.as_bytes()
	
	if py == 2:
		__unicode__ = __str__
		__str__ = __bytes__
		del __bytes__
	
	@property
	def attachments(self):
		"""A generator over the message attachments.
		
		Individual attachment MIME parts can be further manipulated; the message will reflect any changes.
		"""
		return self._instance.iter_attachments()
	
	@property
	def headers(self):
		"""The list of headers for the top level message object.
		
		Can be manipulated; the message will reflect any changes.  Be careful not to violate the specification in
		regards to allowed duplicated headers.
		"""
		return self._instance._headers
	
	@property
	def recipients(self):
		"""A generator over the combination of To, CC, and BCC message recipients."""
		for recipient in chain(self.to, self.cc, self.bcc):
			yield recipient
	
	def send(self):
		if not self._mailer:
			raise NotImplementedError("Message instance is not bound to a Mailer. Use mailer.send() instead.")
		
		return self._mailer.send(self)


'''
import imghdr
import os
import time
import base64

from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.header import Header

from mimetypes import guess_type

from marrow.mailer import release
from marrow.mailer.address import Address, AddressList, AutoConverter
from marrow.util.compat import basestring, unicode, native

class OldMessage(object):
	"""Represents an e-mail message."""
	
	def attach(self, name, data=None, maintype=None, subtype=None,
		inline=False, filename=None, encoding=None):
		"""Attach a file to this message.

		:param name: Path to the file to attach if data is None, or the name
					 of the file if the ``data`` argument is given
		:param data: Contents of the file to attach, or None if the data is to
					 be read from the file pointed to by the ``name`` argument
		:type data: bytes or a file-like object
		:param maintype: First part of the MIME type of the file -- will be
						 automatically guessed if not given
		:param subtype: Second part of the MIME type of the file -- will be
						automatically guessed if not given
		:param inline: Whether to set the Content-Disposition for the file to
					   "inline" (True) or "attachment" (False)
		:param filename: The file name of the attached file as seen
									by the user in his/her mail client.
		:param encoding: Value of the Content-Encoding MIME header (e.g. "gzip"
						 in case of .tar.gz, but usually empty)
		"""
		self._dirty = True

		if not maintype:
			maintype, guessed_encoding = guess_type(name)
			encoding = encoding or guessed_encoding
			if not maintype:
				maintype, subtype = 'application', 'octet-stream'
			else:
				maintype, _, subtype = maintype.partition('/')

		part = MIMENonMultipart(maintype, subtype)
		part.add_header('Content-Transfer-Encoding', 'base64')

		if encoding:
			part.add_header('Content-Encoding', encoding)

		if data is None:
			with open(name, 'rb') as fp:
				value = fp.read()
			name = os.path.basename(name)
		elif isinstance(data, bytes):
			value = data
		elif hasattr(data, 'read'):
			value = data.read()
		else:
			raise TypeError("Unable to read attachment contents")
		
		part.set_payload(base64.encodestring(value))

		if not filename:
			filename = name
		filename = os.path.basename(filename)
		
		if inline:
			part.add_header('Content-Disposition', 'inline', filename=filename)
			part.add_header('Content-ID', '<%s>' % filename)
			self.embedded.append(part)
		else:
			part.add_header('Content-Disposition', 'attachment', filename=filename)
			self.attachments.append(part)

	def embed(self, name, data=None):
		"""Attach an image file and prepare for HTML embedding.

		This method should only be used to embed images.

		:param name: Path to the image to embed if data is None, or the name
					 of the file if the ``data`` argument is given
		:param data: Contents of the image to embed, or None if the data is to
					 be read from the file pointed to by the ``name`` argument
		"""
		if data is None:
			with open(name, 'rb') as fp:
				data = fp.read()
			name = os.path.basename(name)
		elif isinstance(data, bytes):
			pass
		elif hasattr(data, 'read'):
			data = data.read()
		else:
			raise TypeError("Unable to read image contents")

		subtype = imghdr.what(None, data)
		self.attach(name, data, 'image', subtype, True)

'''