#! /usr/bin/python3
# -*- coding: utf-8 -*-
import logging
from os.path import expanduser
from socket import (AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, getfqdn,
                    socket)
from sys import exit, modules
from threading import Thread, enumerate

from libs.tools.toolbox import (args_isset, get_json_data, get_prompt_color,
                                parse_helper_commands, prompt_colors)
from paramiko import (AUTH_SUCCESSFUL, OPEN_SUCCEEDED, RSAKey, ServerInterface,
                      Transport)

__all__ = ['Spana', ]


class Server(ServerInterface):
    def __init__(self, remote: str):
        self.remote = remote

    def check_channel_request(self, kind: str, chanid: int):
        if kind == 'session':
            return OPEN_SUCCEEDED

    def check_auth_publickey(self, username, key):
        self.user = username
        return AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return 'publickey'

    def check_channel_exec_request(self, channel, command):
        command = command.decode("utf-8")  # py3 solution

        if command in ('terminal', 'api'):
            logging.info(
                f"[*] Incoming call from {self.remote} "
                f"which is using {command}.")

            return True

        channel.close()
        logging.warning(
            f"Closed the channel for {self.remote}."
            " Wrong kind of client..")


class Spana:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    send_prompt = True

    def __init__(self, config, *largs):
        server = config['server']
        self.motd = server['motd']

        self.available_commands = get_json_data('base_commands.json')
        self.server_name = server.get('server_name', 'Hamilton')
        self.master = prompt_colors('server', self.server_name, True)
        self.prompt = prompt_colors('{0}', '{1}')

        self.blacklist = server.get('blacklist', [])
        self.host_key = RSAKey(
            filename=expanduser(
                server['protocols']['ssh']))
        self.sock.bind((server['address'], server['port']))
        self.sock.listen(5)

        while True:
            client, address = self.sock.accept()
            client.settimeout(server.get('timeout', 30))
            Thread(
                target=self.client_connection,
                args=(client, address, ),
                daemon=True
            ).start()

    def user_rights(self, address):
        if address not in self.blacklist:
            logging.info(f"[*] [{address}] has access to the server.")

            return True

        logging.critical(
            f"[*] [{address}] does not have access to the server!")

        return False

    def hold_prompt(self, rmessage, release, ruser, raddress):
        if not release:
            self.user_prompt(rmessage, ruser)
            self.ask_for_prompt(
                rmessage,
                ruser,
                raddress)

    def quit(self, rmessage, ruser, raddress):
        rmessage.send(
            "{2} {0}@{1} is now being disconnected.\n".format(
                get_prompt_color(ruser, 'green'),
                get_prompt_color(raddress, 'bold_yellow'),
                self.master))

        logging.info(
            f"[*] Disconnected {ruser}@{raddress}..")

        rmessage.close()
        exit(0)

    def ask_for_prompt(self, message, ruser, raddress, **kwargs):
        cmd = message.makefile('r+U').readline().strip('\r\n')
        print(cmd)
        arguments = cmd.split()
        argument = args_isset(arguments)
        halt = False

        if argument in self.available_commands:
            cmd_ = self.available_commands[cmd]
            case_ = cmd_['send_message']
            args_ = arguments[1:] or case_.get('args', [])
            msg_ = case_.get('message', False)

            try:

                if args_ and msg_:
                    msg = case_['message'].format(args_)

                elif all([
                    'message' in case_,
                    'target' not in case_,
                    not args_
                ]):
                    msg = case_['message']

                else:
                    sub_ = case_['target'].split('.')

                    if sub_[0] in modules:
                        class_ = modules[sub_[0]]
                        attr_ = getattr(class_, sub_[1])(*args_)
                        msg = (
                            case_['message'].format(attr_)
                            if not args_ and msg_ else attr_)

                    else:
                        mod = case_['target'].find('.') + 1
                        msg = getattr(self, case_['target'][mod:])(*args_)

                if log_msg := cmd_.get('log_message'):
                    logging.info(log_msg.format(ruser, raddress))

                message.send(f"{self.master} \u25BC\n{msg}")

            except Exception as error:
                message.send(f"{self.master} \u25BC\nProblem with: {error}.\n")
                logging.error(f"We failed with: {error}")

            halt = cmd_.get('hold_prompt', False)

        elif argument in ('-q', 'quit', 'exit'):
            self.quit(message, ruser, raddress)

        elif argument in ('-h', 'help'):
            message.send(
                parse_helper_commands(
                    self.available_commands,
                    arguments,
                    self.master))

        else:
            if argument:
                message.send(
                    f"{self.master} Could not recognize the command: "
                    f"{cmd}\n")

        self.hold_prompt(message, halt, ruser, raddress)

    def user_prompt(self, message, cmd):
        message.send(self.prompt.format(cmd, self.server_name))

    def client_connection(self, client, address):
        if self.user_rights(address[0]):
            t = Transport(client)
            t.set_gss_host(getfqdn(""))
            t.load_server_moduli()
            t.add_server_key(self.host_key)
            t.use_compression(compress=True)
            server = Server(remote=address[0])
            t.start_server(server=server)
            message = t.accept(timeout=None)

            message.send('\n')
            [
                message.send(
                    f" {get_prompt_color(line, 'bg_gray', spaces=(1, 1))}\n"
                )
                for line in self.motd.split('\n')
            ]
            message.send('\n\n')
            self.user_prompt(
                message,
                server.user)
            self.ask_for_prompt(
                message=message,
                ruser=server.user,
                raddress=address[0])
        else:
            self.sock.close()

    def list_running_cmods(self):
        ac = [
            get_prompt_color(x.name, 'bg_gray', spaces=(1, 1))
            for x in enumerate()
            if 'Thread' not in x.name
        ]
        ac.sort()
        ln = get_prompt_color(len(ac), 'bg_gray', spaces=(1, 1))

        return f"\n {ln} running cmods.\n Running cmods: {', '.join(ac)}\n\n"
