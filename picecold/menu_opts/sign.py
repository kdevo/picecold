import datetime as dt
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, Future

import libs.mount_tool as mount_tool
from config import Configuration
from libs.dot_extended.base import SymbolHandler, MenuOptionSwitcher
from libs.dot_extended.dialogs import StatusMessage, SimpleDialog
from libs.dot_extended.views import PageView, ProgressBarView, SelectFileView
from libs.electrum import ElectrumSigner
from menu_opts.usb import UsbHelper
from util import Symbols


class TransactionSigner(MenuOptionSwitcher):
    def __init__(self, lcd, backlight, cfg: Configuration):
        super().__init__()

        self._cfg = cfg
        self._lcd = lcd
        self._backlight = backlight

        self._electrum = None
        self._mounted_usb_dev = None
        self._tx_path = None

        self._usb_helper = UsbHelper(cfg)
        self._worker = ThreadPoolExecutor(max_workers=1)

        self._progressing = False

    def begin(self):
        self._electrum = AsyncBenchmarkingElectrum(self._cfg)
        if self._usb_helper.is_usb_plugged_in():
            try:
                self._mounted_usb_dev = self._usb_helper.find_trusted_usb()
                self._enter_select_tx_view()
            except LookupError as ex:
                self.switch(StatusMessage(["Please note", str(ex)], self._backlight))
            except PermissionError as ex:
                self.switch(StatusMessage(["Warning", str(ex)], self._backlight))
        else:
            self.switch(StatusMessage(["Please note", "No USB stick seems to be plugged in."],
                                      self._backlight))

    def _enter_select_tx_view(self):
        root_path = os.path.normpath(os.path.join(self._mounted_usb_dev.mount_path, self._cfg.transaction_dir))
        file_view = SelectFileView(root_path, prompt="Select TX on USB",
                                   file_filter_pattern=self._cfg.unsigned_pattern,
                                   callback_on_select=self._enter_deserializing_view)
        self.switch(file_view)

    def _enter_deserializing_view(self, tx: SelectFileView.FileEntry):
        self._tx_path = tx.file_path
        progress_bar = ProgressBarView(["Reading TX...", '{bar}', '{val:.0%}'],
                                       empty_char="\x00", fill_char="\x01",
                                       callback_after_redraw=lambda:
                                       SymbolHandler(self._lcd, [Symbols.CIRCLE, Symbols.CIRCLE_FILLED])
                                       .create_symbols())
        self.switch(progress_bar)
        read_tx_future = self._electrum.deserialize_transaction(self._tx_path)
        read_tx_future.add_done_callback(self._enter_show_tx_view)
        self._refresh_progress(read_tx_future, progress_bar,
                               Configuration.calc_estimated_time(self._cfg.deserialize_time_average, self._tx_path))

    def _enter_show_tx_view(self, future: Future):
        pages = []
        for tx in future.result():
            pages.append(PageView.Page(["{address}".format(address=tx[0]),
                                        "{amount}".format(amount=str(tx[1]))],
                                       ("To: {text1}", "\x00 : {text2}", "{nav}")))
        self.switch(PageView(pages,
                             callback_on_select=self._enter_confirm_tx_dialog,
                             callback_after_redraw=lambda: SymbolHandler(self._lcd, [Symbols.BTC_LOGO])
                             .create_symbols(),
                             auto_center=False))

    def _enter_confirm_tx_dialog(self):
        self.switch(SimpleDialog(["Sign TX?", "Confirm to sign  \"{file}\" "
                                              "and save it to your USB stick. "
                                              "Use left/right + select to choose an answer (Y/N)."
                                 .format(file=os.path.basename(self._tx_path)),
                                  "{answers}"],
                                 callback_on_positive=self._enter_sign_tx_view))

    def _enter_sign_tx_view(self):
        progress_bar = ProgressBarView(["Signing TX...".center(16), '{bar}', '{val:.0%} (ca.)'],
                                       empty_char="\x00", fill_char="\x01",
                                       callback_after_redraw=lambda:
                                       SymbolHandler(self._lcd,
                                                     [Symbols.CIRCLE, Symbols.CIRCLE_FILLED])
                                       .create_symbols())
        self.switch(progress_bar)
        path_without_ext = os.path.splitext(self._tx_path)[0]
        signed_tx_path = "{0}{suffix}.txn".format(path_without_ext,
                                                  suffix=self._cfg.signed_suffix
                                                  .format(time=dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
        sign_tx_future = self._electrum.sign_transaction(self._tx_path, signed_tx_path, self._cfg.wallet_password)
        sign_tx_future.add_done_callback(self._enter_finished_view)
        self._refresh_progress(sign_tx_future, progress_bar,
                               self._cfg.calc_estimated_time(self._cfg.sign_time_average, self._tx_path))

    def _enter_finished_view(self, future: Future):
        mount_tool.umount(self._mounted_usb_dev)
        if future.exception() is None:
            self.switch(StatusMessage(["Success", "The transaction has been signed successfully. "
                                                  "The USB stick was automatically unmounted."],
                                      self._backlight))
        else:
            self.switch(StatusMessage(["Error", "There was an error while signing the transaction: "
                                       + str(future.exception())], self._backlight))

    def _refresh_progress(self, future: Future, progress_bar: ProgressBarView, estimated_time: float):
        self._progressing = True
        start_time = time.clock()
        while not future.done():
            progress_bar.value = round((time.clock() - start_time) / estimated_time, 2)
            self._backlight.set_graph(progress_bar.value)
            time.sleep(0.25)
        self._progressing = False
        self._backlight.set_graph(0.0)

    def select(self):
        if isinstance(self._current_menu_opt, ProgressBarView):
            return False
        else:
            return super().select()

    def left(self):
        if isinstance(self._current_menu_opt, ProgressBarView):
            return True
        else:
            return super().left()

    def right(self):
        if isinstance(self._current_menu_opt, ProgressBarView):
            return True
        else:
            return super().right()

    @property
    def is_progressing(self):
        return self._progressing


class AsyncBenchmarkingElectrum:
    def __init__(self, cfg: Configuration):
        self._cfg = cfg
        self._electrum = ElectrumSigner(self._cfg.electrum_path)
        self._executor = ThreadPoolExecutor(max_workers=1)

    def sign_transaction(self, path_txn, path_signed_txn, password):
        return self._executor.submit(self._sync_sign_transaction, path_txn, path_signed_txn, password)

    def _sync_sign_transaction(self, tx_path, path_signed_txn, password):
        return self._benchmark(self._cfg.add_sign_timing, tx_path,
                               lambda: self._electrum.sign_transaction(tx_path, path_signed_txn, password))

    def deserialize_transaction(self, tx_path):
        return self._executor.submit(self._sync_deserialize_transaction, tx_path)

    def _sync_deserialize_transaction(self, tx_path):
        return self._benchmark(self._cfg.add_deserialize_timing, tx_path,
                               lambda: self._electrum.deserialize_transaction(tx_path))

    def start_electrum(self, electrum_args):
        return self._executor.submit(self._start_electrum, electrum_args)

    @staticmethod
    def _start_electrum(electrum_args):
        with subprocess.Popen("electrum " + electrum_args,
                              universal_newlines=True, stdout=subprocess.PIPE, shell=True) as process:
            return process.stdout.readlines()

    @staticmethod
    def _benchmark(add_timing_func, tx_path, func):
        start = time.clock()
        result = func()
        measured = time.clock() - start
        add_timing_func(measured, tx_path)
        return result
