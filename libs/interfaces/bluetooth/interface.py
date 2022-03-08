#! /usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import os
import socket
import sys
import threading as clients
from abc import ABC, abstractmethod  # noqa
from pathlib import Path

import paramiko
from __main__ import config as ServerConfig
from libs.common.interaction import controller

__all__ = ['Spana', ]


class Server(paramiko.ServerInterface):
    def __init__(self, remote):
        self.remote = remote

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

        if command in ['terminal', 'client']:
            logging.info(
                f"[*] Incoming call from [{self.remote}] "
                f"which is using the client: [{command}]")

            return True

        channel.close()
        logging.warning(
            f'Closed the channel for {self.remote}. Wrong kind of client..'
        )

        return False


class Spana(ABC):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    prompt = (
        "\033[92m{0}\033[0;0m@\033[1m\033[93m{1}"
        "\033[0;0m\033[0;0m:~\033[34m$\033[0;0m ")
    send_prompt = True
    for f_ in controller():
        exec(f_)

    def __init__(self):
        server = ServerConfig['server']
        self.server_name = server.get('server_name', 'Hamilton')
        self.master = (
            f"\033[1m\033[93m{self.server_name}\033[0;0m:"
            "~\033[34m$\033[0;0m")

        self.rsa_key = os.path.join(Path.home(), server['RSA_KEY'])
        self.blacklist = server.get('blacklist', [])

        self.ib_affair()
        self.host_key = paramiko.RSAKey(filename=self.rsa_key)
        self.sock.bind(
            (
                self.host,
                self.port,
            )
        )
        self.sock.listen(5)

        while True:
            client, address = self.sock.accept()
            client.settimeout(server.get('timeout', 30))
            clients.Thread(
                target=self.client_connection,
                args=(client, address, ),
                daemon=True
            ).start()

    def user_rights(self, address):

        if address not in self.blacklist:
            logging.info(
                f"[*] [{address}] has access to the server.")

            return True

        logging.critical(
            f"[*] [{address}] does not have access to the server!")

        return False

    def hold_prompt(self, rem_message, boolean, rem_user, rem_address):
        if not boolean:
            self.user_prompt(rem_message, rem_user)
            self.ask_for_prompt(
                rem_message,
                rem_user,
                rem_address,
            )

    def ask_for_prompt(self, message, rem_user, rem_address, **kwargs):
        inp = message.makefile('r+U')
        cmd = inp.readline().strip('\r\n')
        # hostname = socket.gethostname()
        logging.info(f"[*] {rem_user}@{rem_address} sent: {cmd}")

        if cmd in 'list':
            message.send(
                self.list_them()
            )
            logging.info(
                "[*] Listing all available CMOD's for "
                f"{rem_user}@{rem_address}..")
            self.hold_prompt(
                message,
                False,
                rem_user,
                rem_address,
            )

        elif cmd in 'thread count':
            message.send(
                "\n Active threads: \033[100m "
                f"{clients.active_count()} \033[0m\n\n")
            logging.info(
                f"[*] Counting all threads: {clients.active_count()}.")
            self.hold_prompt(
                message,
                False,
                rem_user,
                rem_address,
            )

        elif cmd in 'kill':
            message.send(
                self.kill_task('test5')
            )
            logging.info(
                f"[*] Stopping the task for {rem_user}@{rem_address}..")
            self.hold_prompt(
                message,
                False,
                rem_user,
                rem_address,
            )

        elif cmd in 'dir':
            message.send(
                self.access_cmod('5')
            )
            logging.info(
                "[*] Printed info from CMOD 5")
            self.hold_prompt(
                message,
                False,
                rem_user,
                rem_address,
            )

        elif cmd in ('q', 'quit', 'exit'):
            message.send(
                f"{self.master} \033[93m{rem_user}@{rem_address}"
                "\033[0;0m is now being disconnected.\n")
            logging.info(
                f"[*] Disconnected {rem_user}@{rem_address}..")
            message.close()
            sys.exit(0)

        elif cmd in ('-H', '-halt'):
            self.hold_prompt(
                message,
                False,
                rem_user,
                rem_address,
            )

        else:
            message.send(
                f"{self.master} Couldn't recognize the command "
                f"input from \033[93m{rem_user}\033[0;0m\n")
            self.hold_prompt(
                message,
                False,
                rem_user,
                rem_address,
            )

    def user_prompt(self, message, cmd):
        message.send(self.prompt.format(cmd, self.server_name))

    def client_connection(self, client, address):
        if self.user_rights(address[0]):
            t = paramiko.Transport(client)
            t.set_gss_host(socket.getfqdn(""))
            t.load_server_moduli()
            t.add_server_key(self.host_key)
            t.use_compression(compress=True)
            server = Server(remote=address[0])
            t.start_server(server=server)
            message = t.accept(timeout=None)

            message.send('\n')
            [
                message.send(f" \033[100m{line}\033[0;0m\n")
                for line in self.motd.split('\n')
            ]
            message.send('\n\n')

            self.user_prompt(
                message,
                server.user,
            )

            self.ask_for_prompt(
                message=message,
                rem_user=server.user,
                rem_address=address[0]
            )
        else:
            self.sock.close()
