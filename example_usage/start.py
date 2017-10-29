#!/usr/bin/env python3

import os
import sys
import time

PLUGIN_PATH = os.path.expanduser("~/Pimoroni/displayotron/examples/")

from dot3k.menu import Menu

sys.path.insert(1, os.path.join(sys.path[0], '../picecold'))
sys.path.insert(1, PLUGIN_PATH)

from main import PiceCold

from plugins.graph import IPAddress, GraphCPU, GraphTemp, GraphSysReboot, GraphSysShutdown
from plugins.text import Text
from plugins.utils import Contrast, Backlight

picecold = PiceCold("picecold.ini")

menu = Menu(
    structure={
        'System': {
            'Boot Options': {
                'Shutdown': GraphSysShutdown(),
                'Reboot': GraphSysReboot()
            },
            'Settings': {
                'Display': {
                    'Contrast': Contrast(picecold.lcd),
                    'Backlight': Backlight(picecold.backlight)
                }
            }
        },
        'Status': {
            'IP': IPAddress(),
            'CPU': GraphCPU(picecold.backlight),
            'Temp': GraphTemp()
        }
    },
    lcd=picecold.lcd,
    input_handler=Text())

picecold.add_to_menu(menu)

# nav.enable_repeat(True)

while True:
    menu.redraw()
    time.sleep(0.025)
