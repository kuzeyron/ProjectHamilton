#! /usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import sys
from importlib import import_module

from libs.tools.toolbox import KGB, configuration, log_setup

if __name__ == '__main__':
    config = configuration()
    interface = config['server']['interface']
    log_setup(interface, config['logger'])

    try:

        KGB(config['startup'])
        import_module(
            "libs.interfaces."
            f"{interface}."
            "interface"
        ).Spana(config)

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as exc:
        logging.error(f"[*] Problem with: {exc}..")
