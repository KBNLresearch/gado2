#!/usr/bin/env python3

import sys


if not sys.argv[-1].endswith('.py'):
    with open(f'{sys.argv[-1]}', 'r') as fh:
        for line in fh.read().split('\n'):
            try:
                print(line.split()[0], line.split()[-1])
            except:
                pass
