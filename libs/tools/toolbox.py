import json
import logging
import sys
import threading as cmoders
from importlib import import_module as impl
from os import listdir, makedirs
from os.path import dirname, exists, isdir, join, realpath, splitext

import __main__

__all__ = [
    'configuration',
    'get_json_data',
    'get_prompt_color',
    'interface_translation',
    'interface_translation',
    'KGB',
    'log_setup',
    'prompt_colors',
    'set_json_data',
    'Supo'
]


def interface_translation(interface: str):
    modules = {
        'ssh': 'paramiko',
        'ssl': 'paramiko',
        'bluetooth': 'paramiko',
        'oscpy': 'paramiko',
    }

    for key, name in modules.items():
        if key == interface:
            return name


def log_setup(interface: str, logger: dict):
    interface_logger = interface_translation(interface)
    logging.root.handlers = []

    if logger['log_data']:
        logging.basicConfig(
            level=logger['log_level'],
            format='%(levelname)s|%(asctime)s|%(message)s',
            stream=Supo(logger['dir_name']),
            filemode='w')

    logging.getLogger('').addHandler(logging.StreamHandler())

    if not logger['hide_info']:
        logging.getLogger('').setLevel(logging.NOTSET)

    if logger['hide_unrelated_logs']:
        if interface_logger == 'paramiko':
            logging.getLogger('paramiko').propagate = False

    else:
        if interface_logger == 'paramiko':
            logging.getLogger('paramiko').propagate = False


class KGB:
    cia = {}

    def __init__(self, startup, *largs):
        self.path = join(dirname(realpath(__main__.__file__)), 'cmods')
        makedirs(self.path, exist_ok=True)
        sys.path.append(self.path)

        for e in listdir(self.path):
            if startup.get('auto_load_dir', True) is not True:
                if e.strip('.py') in startup.get('scripts', []):
                    self.komandir(e)
            else:
                self.komandir(e, isdir(join(self.path, e)))

    def komandir(self, ataka: str, is_dir=False):
        dorozhka = join(self.path, ataka)

        if ataka.endswith(".py"):
            filename, file_ext = splitext(ataka)
            self.vtorzhenie('cmods', filename, is_dir, ataka)

        if is_dir:
            [
                self.vtorzhenie(
                    f'cmods.{ataka}',
                    'main',
                    is_dir,
                    ataka
                )
                for file in listdir(dorozhka)
                if 'main.py' in file
            ]

    def vtorzhenie(self, start: str, mod: str, bool_dir: bool, name: str):
        name = start.split('.')[1] if bool_dir else mod
        mods = impl(f'{start}.{mod}')

        if mods not in sys.modules:
            self.cia[name] = cmoders.Thread(
                name=name,
                target=mods.CMOD,
                daemon=True,
                args=(logging, )
            )
            self.cia[name].start()
        else:
            logging.warning(f"Module {mods} is already running!")


class Supo:
    """Log setup for ProjectHamilton"""

    files = {
        'ERROR': 'error.log',
        'CRITICAL': 'critical.log',
        'WARNING': 'warning.log',
        'DEBUG': 'debug.log',
        'INFO': 'info.log'}

    def __init__(self, conf, **kwargs):
        self.ohjukset = conf

        '''
            Creates the log folder if needed and writes the log templates.
        '''
        makedirs(self.ohjukset, exist_ok=True)
        [open(join(self.ohjukset, e[1]), 'a+').close()
            for e in self.files.items()]

    def write(self, kommentti: str):
        space = join(
            self.ohjukset, self.files.get(
                kommentti.split('|')[0],
                join(self.ohjukset, 'log.log')))

        with open(space, 'a+') as c4:
            if len(kommentti) > 3:
                c4.write(f"{kommentti}\n")


def log_mode(lvl=0):
    level = [logging.INFO, logging.DEBUG, logging.WARNING,
             logging.ERROR, logging.CRITICAL]

    return level[lvl]


def configuration(file='config.json'):

    if exists(file):
        config = get_json_data(file, islocal=False)

        if config:
            logging.info(f'We found `{file}`.')

    else:
        config = get_json_data('default.json')

        if config:
            with open(file, 'w') as d:
                d.write(config)

            logging.error(f"We couldn't find `{file}`.")
            logging.error("Reverting back to the default settings.")

    return config


def get_json_data(file: str, islocal=True):
    folder = dirname(realpath(__file__))
    path = join(folder, file)

    with open(path if islocal else file) as data:
        return json.load(data)

    return {}


def set_json_data(file: str, content: str):
    with open(file, 'w') as data:
        data.write(content)


def get_prompt_color(text: str, color='white', spaces=(0, 0)):
    spaces = [' ' * x for x in spaces]
    colors = {
        'bg_blue': '104m',
        'bg_gray': '100m',
        'bold_white': '1;1m\u001b[1;37m',
        'bold_yellow': '1;1m\033[1;93m',
        'green': '1;32m',
        'red': '1;31m',
        'white': '1;37m',
        'yellow': '1;33m',
    }

    return (
        f"\u001b[{colors.get(color, colors['white'])}"
        f"{spaces[0]}{text}{spaces[1]}\u001b[0m"
    ) if text else ''


def prompt_colors(user: str, host: str, root=False):
    return "".join([
        get_prompt_color(user, 'red' if root else 'green'),
        get_prompt_color('@'),
        get_prompt_color(host, 'bold_yellow'),
        get_prompt_color(':~'),
        get_prompt_color('$ ', 'red')
    ])


def string_merge(text: str, value: str):
    return text.format(value) if value else ''


def string_joiner(cont: list, newline='\n', spaces=4):
    return f"{newline}{' ' * spaces}".join([
        string_merge(*cont)
        for cont in cont if cont[1]
    ])


def argument_available(cont: list, args: list):
    if len(args) > 1 and args[1] in cont:
        return {args[1]: cont.get(args[1], cont)}

    return cont


def parse_helper_commands(cont: list, args: list, sender: str):
    title = get_prompt_color('Help commands:', 'bg_blue', spaces=(1, 55))
    manual = "\n  ".join([
        string_joiner([
            ("Command:  {}", get_prompt_color(key, 'bg_gray', spaces=(1, 1))),
            ("Example: {}", get_prompt_color(ct.get('help'), 'yellow')),
            ("About:   {}\n", get_prompt_color(ct.get('about'), 'bold_white'))
        ])
        for key, ct in argument_available(cont, args).items()
        if 'help' or 'about' in ct
    ])

    return f"{sender} \u25BC\n\n  {title}\n\n  {manual}\n\n"


def args_isset(args: list, index=0):
    return args[index] if args and index <= len(args) else False
