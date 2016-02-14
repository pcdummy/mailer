# encoding: utf-8

"""MIME-encoded electronic mail message class."""

from datetime import datetime
from itertools import chain
from email.message import EmailMessage
from socket import getfqdn
from os import getuid, getpid

from .. import release
from ..util import zipl, iodict, idict, py, odict, _annotate
from .header import nodefault, Header, Priority, Date, Domain, Id
from .content import ContentMime, ContentEncoding
from .address import SenderAddress, Address, Addresses
from .body import Body


@_annotate('_fields')
class Message(object):  # https://tools.ietf.org/html/rfc5322
	__slots__ = ('_instance', '_mailer', '_domain', 'defaults')
	
	_fields = odict()
	
	# Basic Message Metadata
	
	domain = Domain('Message-Id', rfc=None, index=100)
	id = Id('Message-Id', default=None, rfc='822#4.6.1,1036#2.1.5,5322#3.6.4', index=100)
	date = Date('Date', default=datetime.utcnow, rfc='822#5.1,1123#5.2.14,1036#2.1.2', index=100)
	subject = Header('Subject', rfc='822#4.7.1,1036#2.1.4')
	to = Addresses('To', rfc='822#4.5.1,1123#5.2.15-16,1123#5.3.7')
	cc = Addresses('Cc', rfc='822#4.5.2,1123#5.2.15-16,1123#5.3.7')
	bcc = Addresses('Bcc', rfc='822#4.5.3,1123#5.2.15-16,1123#5.3.7')
	author = Address('From', rfc='822#4.4.1,1123#5.2.15-16,1036#2.1.1')
	authors = Addresses('From', rfc=None, index=100)
	
	# Content Metadata
	# Note: The meanings of `mime` and `encoding` have changed in Mailer 5!
	
	mime = ContentMime(default="text/plain", rfc='1049,1123#5.2.13,1521#4,1766#4.1')
	charset = ContentEncoding(default="utf-8", rfc='1049,1123#5.2.13,1521#4,1766#4.1')
	encoding = Header('Content-Transfer-Encoding', default='quoted-printable', rfc='1521#5')
	
	# Message Routing
	
	precedence = Header('Precedence', rfc=None)
	rpath = Header('Return-Path', rfc='821,1123#5.2.13')
	sender = SenderAddress('Sender', rfc='822#4.4.2,1123#5.2.15-16,1123#5.3.7')
	reply = Address('Reply-To', rfc='822#4.4.3,1036#2.2.1')
	notify = Addresses('Disposition-Notification-To', rfc=None)
	
	# Advanced Message Metadata
	
	organization = Header('Organization', rfc=None)
	organisation = organization  # Convienent spelling difference.
	priority = Priority('X-Priority', rfc=None)
	
	# Message Parts
	
	plain = Body(('text', 'plain'), rfc=None)
	rich = Body(('text', 'html'), rfc=None)
	
	def __init__(self, *args, **kw):
		"""Instantiate a new Message object.
		
		No arguments are required, as everything can be set through attribute assignment. Alternatively, everything
		may be defined using positional and keyword arguments. Positionally, subject, to, and so forth start the
		list. All keyword arguments are interepreted as attribute assignments.
		"""
		
		self._instance = EmailMessage()
		self._mailer = kw.pop('_mailer', None)
		self._domain = None  # Default to auto-detection.
		
		if kw.pop('brand', True):
			self._instance['User-Agent'] = "marrow.mailer/{release.version} <{release.url}>".format(release=release)
		
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
			failed = False
			try:
				setattr(self, name, value)
			except AttributeError:
				failed = True
			if failed:
				raise TypeError("Unknown argument: " + name)
		
		if 'User-Agent' in self._instance:
			self._instance['Received'] = "by {host} (Marrow Mailer, user {user} process {pid}) id {id}; {date}".format(
					host = getfqdn(),
					user = getuid(),
					pid = getpid(),
					date = Date.to_foreign(None, None, datetime.utcnow()),
					id = self.id
				)
	
	def validate(self):
		if not self.author:
			raise ValueError("You must specify an author.")
		
		if not self.subject:
			raise ValueError("You must specify a subject.")
		
		if not list(self.recipients):
			raise ValueError("You must specify at least one recipient.")
		
		if not self.plain and not self.rich:
			raise ValueError("You must specify message content.")
		
		return True
	
	def __str__(self):  # Python 2 and Python 3
		if __debug__:
			self.validate()
		
		return self._instance.as_string()
	
	def __bytes__(self):  # Python 3
		if __debug__:
			self.validate()
		
		return self._instance.as_bytes()
	
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
	def envelope(self):
		"""Returns the the envelope sender address, sender if set, author otherwise."""
		if not self.sender and not self.author:
			raise ValueError("Unable to determine message sender; no author or sender defined.")
			
		return self.sender or self.author
	
	@property
	def recipients(self):
		"""A generator over the combination of To, CC, and BCC message recipients."""
		
		parts = []
		
		if self.to:
			if isinstance(self.to, list):
				parts.extend(self.to)
			else:
				parts.append(self.to)
		
		if self.cc:
			if isinstance(self.cc, list):
				parts.extend(self.cc)
			else:
				parts.append(self.cc)
		
		if self.bcc:
			if isinstance(self.bcc, list):
				parts.extend(self.bcc)
			else:
				parts.append(self.bcc)
		
		return iter(parts)
	
	def send(self):
		if not self._mailer:
			raise NotImplementedError("Message instance is not bound to a Mailer. Use mailer.send() instead.")
		
		return self._mailer.send(self)
	
	def attach(self, name, data=None, inline=False, filename=None):
		if data is not None:  # Explicit value assignment.
			if not mimetype:
				mimetype = 'application/octet-stream'
			
			mimetype = mimetype.partition('/')
			self._instance.add_attachment(data, maintype=mimetype[0], subtype=mimetype[2], filename=filename or name)
			return self  # Allow chaining.
		
		return self  # Allow chaining.
	
	def detach(self, name):
		"""Remove an attachment by name."""
		pass
		
		return self  # Allow chaining.
