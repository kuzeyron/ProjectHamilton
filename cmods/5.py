#!/cmd/bin/env python3
# -*- coding: utf-8 -*-
import sys
from time import localtime, sleep, strftime, time

__all__ = ['CMOD', ]


class CMOD:
    """Test runner."""

    def __init__(self, logging):
        self.amount = 1

        while True:
            sleep(5)
            time_now = localtime(time())
            time_me = strftime("%H:%M:%S", time_now)

            if self.amount < 10:
                logging.info(
                    f'\033[37;1m5 - {time_me} | 5th CMOD example '
                    f'running {self.amount}/10 times.\033[0m')
                self.amount += 1

            else:
                logging.info(
                    f'\033[1m\033[37;1m5 - {time_me} | We are killing 5th '
                    f'CMOD thread now we are on the 10th step.\033[0m')

                sys.exit(0)
