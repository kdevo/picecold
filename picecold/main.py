import atexit
import logging

from config import ConfigurationManager
from libs.dot_extended.views import ProgressBarView
from menu_opts.general import About
from menu_opts.sign import TransactionSigner
from menu_opts.usb import UsbEject, UsbTrusting

PLUGIN_NAME = "PiceCold"
PLUGIN_VERSION = "v0.6.0"


class PiceCold:
    def __init__(self, cfg_path):
        logging.basicConfig(format="%{asctime}s - [%(levelname)s]: %(message)s")

        self._cfg_man = ConfigurationManager(cfg_path)
        atexit.register(self._cfg_man.save_configuration)
        self._is_hat = self._cfg_man.configuration.display_type == 'dothat'
        if self._is_hat:
            import dothat.backlight as backlight
            import dothat.lcd as lcd
            self._lcd = lcd
            self._backlight = backlight
        else:
            import dot3k.backlight as backlight
            import dot3k.lcd as lcd
            self._lcd = lcd
            self._backlight = backlight

    def add_to_menu(self, target_menu, parent_name="PiceCold", show_trust_usb=True):
        target_menu.add_item(parent_name + '/Sign TX',
                             TransactionSigner(self._lcd, self._backlight, self._cfg_man.configuration))
        if show_trust_usb:
            target_menu.add_item(parent_name + '/Trust USB', UsbTrusting(self._backlight, self._cfg_man.configuration))
        target_menu.add_item(parent_name + '/Eject USB', UsbEject())
        target_menu.add_item(parent_name + '/About', About(self._backlight, self._cfg_man.configuration))

        # Rebind navigation keys (only applies for DOT-HAT).
        # Rebinding is necessary because of the key "nav.CANCEL".
        # It is not intended to abort a transaction signing process.
        menu = target_menu
        if self._is_hat:
            import dothat.touch as nav
            from dot3k.menu import _MODE_ADJ as ADJUST

            @nav.on(nav.UP)
            def handle_up(ch, evt):
                menu.up()

            @nav.on(nav.DOWN)
            def handle_down(ch, evt):
                menu.down()

            @nav.on(nav.LEFT)
            def handle_left(ch, evt):
                menu.left()

            @nav.on(nav.RIGHT)
            def handle_right(ch, evt):
                menu.right()

            @nav.on(nav.BUTTON)
            def handle_button(ch, evt):
                menu.select()

            @nav.on(nav.CANCEL)
            def handle_cancel(ch, evt):
                current = menu.current_value()
                if menu.mode == ADJUST and \
                        isinstance(current, TransactionSigner) and \
                        (isinstance(current.current_menu_opt, ProgressBarView) or current.is_progressing):
                    # Do NOT menu.cancel() here!
                    # This can have unhandled consequences when cancelled while processing a tx
                    pass
                else:
                    menu.cancel()

            @nav.on(nav.UP)
            def handle_up(pin):
                menu.up()

            @nav.on(nav.DOWN)
            def handle_down(pin):
                menu.down()

            @nav.on(nav.LEFT)
            def handle_left(pin):
                menu.left()

            @nav.on(nav.RIGHT)
            def handle_right(pin):
                menu.right()

            @nav.on(nav.BUTTON)
            def handle_button(pin):
                menu.select()

    @property
    def lcd(self):
        return self._lcd

    @property
    def backlight(self):
        return self._backlight
