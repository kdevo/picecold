import time

from dot3k.menu import MenuOption

import main
from config import Configuration
from util import Symbols
from .sign import AsyncBenchmarkingElectrum


class About(MenuOption):
    def __init__(self, backlight, cfg: Configuration):
        super().__init__()
        self._backlight = backlight
        self._cfg = cfg
        self._electrum = None
        self._electrum_version = None
        self._sweep = 0

    def setup(self, config):
        super().setup(config)
        self._electrum = AsyncBenchmarkingElectrum(self._cfg)

    def begin(self):
        future_version = self._electrum.start_electrum("version")
        future_version.add_done_callback(self._on_electrum_end)

    def redraw(self, menu):
        self._backlight.sweep(((self._sweep % 100) / 100))
        self._sweep += 1
        Symbols(menu.lcd, [Symbols.ARROW_RIGHT, Symbols.BTC_LOGO, Symbols.TARGET]).create_symbols()
        menu.write_row(0, "{0} {1}".format(main.PLUGIN_NAME, main.PLUGIN_VERSION))
        menu.write_option(1, "Offline wallet \x00 "
                             "Easily sign your \x01itcoin transactions. "
                             "Installed Electrum version: {version} - "
                             "Electrum benchmark stats: "
                             "DESERIALIZE={deserialize_time}ms/kb | SIGN={sign_time}ms/kb"
                          .format(version="Fetching..." if self._electrum_version is None else self._electrum_version,
                                  deserialize_time=self._cfg.deserialize_time_average,
                                  sign_time=self._cfg.sign_time_average),
                          scroll=self._electrum_version is not None, scroll_speed=200)
        if int(self._sweep / 60) != 0 and int(self._sweep / 60) % 2 == 0:
            menu.write_row(2, "~git.io/pyo".format().center(16))
        else:
            menu.write_row(2, "By Py\x02tek".format().center(16))
        time.sleep(0.01)

    def _on_electrum_end(self, future):
        self._electrum_version = future.result()[0].strip()

    def cleanup(self):
        self._backlight.rgb(int(self.get_option('Backlight', 'r', 255)),
                            int(self.get_option('Backlight', 'g', 255)),
                            int(self.get_option('Backlight', 'b', 255)))

    def select(self):
        self.cleanup()
        return True
