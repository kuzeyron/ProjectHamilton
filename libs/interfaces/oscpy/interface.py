# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
import paramiko, socket
import threading as clients
import sys, time
from pathlib import Path
import configparser
config = configparser.ConfigParser()
config.read('configuration.ini')
server_port = int(config.get('NETWORKING', 'SERVER_PORT').strip())
rsa_key = "{}/{}".format(Path.home(), config.get('NETWORKING', 'RSA_KEY').strip())
addresses = [e[:8].strip() for e in config.get('NETWORKING', 'ALLOW').split(',')]

__all__ = ['Spana', ]

class Server(paramiko.ServerInterface):
	def __init__(self, remote, log_book):
		self.remote = remote
		self.log_book = log_book

	def check_channel_request(self, kind, chanid):
		if kind == 'session':
			return paramiko.OPEN_SUCCEEDED

	def check_auth_publickey(self, username, key):
		self.user = username
		return paramiko.AUTH_SUCCESSFUL

	def get_allowed_auths(self, username):
		return 'publickey'

	def check_channel_exec_request(self, channel, command):
		command = command.decode("utf-8")
		if command in ['terminal']:
			self.log_book.info("[*] Incoming call from [{}] which is using the client: [{}]".format(self.remote, command))
			return True
		else:
			channel.close()
			self.log_book.warning('Closed the channel for {}. Wrong kind of client..'.format(self.remote))
			return False


class Spana(ABC):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	send_prompt = True

	def __init__(self):
		self.ib_affair()
		self.log_setup()
		self.port = server_port
		self.addresses = addresses
		self.host_key = paramiko.RSAKey(filename=rsa_key)
		self.sock.bind((self.host, self.port))
		self.sock.listen(5)
		while True:
			client, address = self.sock.accept()
			client.settimeout(30)
			clients.Thread(target=self.client_connection, args=(client, address)).start()
			time.sleep(2)

	@abstractmethod
	def log_setup(self):
		pass
	@abstractmethod
	def ib_affair(self):
		pass
	@abstractmethod
	def interests(self):
		pass
	@abstractmethod
	def radio(self):
		pass
	def user_rights(self, address):
		if(address[:7] in self.addresses):
			self.log_book.info("[*] [{}] have access to the server.".format(address))
			self.remote_user = address
			return True
		else:
			self.log_book.critical("[*] [{}] doesn't have access to the server!".format(address))
			return False

	def hold_prompt(self, message, boolean, user, remote_address):
		if not boolean:	self.user_prompt(message, user); self.ask_for_prompt(message, user, remote_address)

	def ask_for_prompt(self, message, user, remote_address, **kwargs):
		inp = message.makefile('r+U'); cmd = inp.readline().strip('\r\n')
		hostname = socket.gethostname()

		self.log_book.info("[*] {0}@{1} sent: {2}".format(user, remote_address, cmd))

		if cmd in ['q', 'quit', 'exit']:
			message.send("Hamilton@{0}:~$ {1}@{2} is now being disconnected.\n".format(hostname, user, remote_address))
			self.hold_prompt(message, True, user, remote_address); message.close()
			self.log_book.info("[*] Disconnected {0}@{1}..".format(user, remote_address))
		elif cmd in ['-H', '-halt']:
			self.hold_prompt(message, False, user, remote_address)
		elif cmd == "interests":
			message.send("[Hamilton@{0}] In the Interest of the Nation: {1}\n".format(hostname, str(self.interests('example'))))
			self.hold_prompt(message, False, user, remote_address)
		elif cmd == "add":
			message.send("[Hamilton@{0}] In the Interest of the Nation: {1}\n".format(hostname, str(self.radio('example', 'NEW_DATA'))))
			self.hold_prompt(message, False, user, remote_address)
		else:
			message.send("[Hamilton@{0}] Couldn't recognize the command input from {1}\n".format(hostname, user))
			self.hold_prompt(message, False, user, remote_address)

	def user_prompt(self, message, cmd):
		message.send('{0}@{1}:~$ '.format(cmd, socket.gethostname()))

	def client_connection(self, client, address):
		if self.user_rights(address[0]):
			t = paramiko.Transport(client);t.set_gss_host(socket.getfqdn(""))
			t.load_server_moduli(); t.add_server_key(self.host_key)
			t.use_compression(compress=True); server = Server(remote=address[0], log_book=self.log_book)
			t.start_server(server=server); message = t.accept(timeout=None)
			message.send('\n')
			for e in self.motd.split('\\n'):
				message.send(e+'\n')
			message.send('\n\n')
			self.user_prompt(message, server.user); self.ask_for_prompt(message, server.user, self.remote_user)
		else: self.sock.close()