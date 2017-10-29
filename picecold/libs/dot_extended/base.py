from dot3k.menu import MenuOption

# Documentation: http://www.lcd-module.de/pdf/doma/dog-m.pdf
BUILTIN_SYMBOLS = {
    'double_arrow_left': chr(251),
    'double_arrow_right': chr(252),
    'underlined_arrow_left': chr(249),
    'underlined_arrow_right': chr(250),
    'standard_arrow_left': chr(126),
    'standard_arrow_right': chr(126)
}


class SymbolHandler:
    def __init__(self, lcd, symbols):
        self._lcd = lcd
        self._symbols = symbols

    def create_symbols(self):
        if len(self._symbols) > 8:
            raise OverflowError("Display only supports eight created chars at a time.")
        else:
            for idx, sym in enumerate(self._symbols):
                self._lcd.create_char(idx, sym)


class ScrollableMenu(MenuOption):
    scroll_speed = 400
    scroll_delay = 800

    def __init__(self, entries, title=None,
                 cursor_char=BUILTIN_SYMBOLS['standard_arrow_right'], cycling=False):
        self._entries = entries
        self._cycling = cycling
        self._title = title
        self._current_idx = 0
        self._write_offset = 1 if title else 0
        self._available_rows = 2 if title else 3
        self.cursor_char = cursor_char
        self._page_range = range(self._current_idx, self._available_rows)
        super().__init__()

    def redraw(self, menu):
        if self._show_title():
            menu.write_option(0, self._title,
                              scroll=len(self._title) > 16,
                              scroll_delay=self.scroll_delay,
                              scroll_speed=self.scroll_speed)
        for row_idx, i in enumerate(self._page_range):
            if i in range(0, len(self._entries)):
                row_txt = self.get_entry(i)
                menu.write_option(self._write_offset + row_idx, row_txt,
                                  scroll=len(row_txt) > 16 and i == self._current_idx,
                                  scroll_delay=self.scroll_delay,
                                  scroll_speed=self.scroll_speed,
                                  icon=self._get_cursor(i))
            else:
                menu.clear_row(self._write_offset + row_idx)

    # Delivers cursor if idx == current index
    def _get_cursor(self, idx):
        return self.cursor_char if idx == self._current_idx else ' '

    def _show_title(self) -> bool:
        return self._title

    def up(self):
        if len(self._entries) > 0:
            if (self._current_idx - 1) in range(0, len(self._entries)):
                self._current_idx -= 1
                # check if new cursor points on last element of screen/page, that would mean "one page up":
                if (self._current_idx + 1) % self._available_rows == 0:
                    self._page_range = range(self._current_idx - (self._available_rows - 1), self._current_idx + 1)
            elif self._cycling:
                self._current_idx = len(self._entries) - 1
                len_modulo = (len(self._entries) % self._available_rows)
                self._page_range = range(len(self._entries) - self._available_rows if len_modulo == 0 else len_modulo,
                                         len(self._entries))

    def down(self):
        if len(self._entries) > 0:
            if (self._current_idx + 1) in range(0, len(self._entries)):
                self._current_idx += 1
                # check if new cursor points on first element of screen/page, that would mean "one page down":
                if self._current_idx % self._available_rows == 0:
                    self._page_range = range(self._current_idx, self._current_idx + self._available_rows)
            elif self._cycling:
                self._current_idx = 0
                self._page_range = range(0, self._available_rows)

    def get_entry(self, idx):
        return self._entries[idx]


class RadioBoxMenu(ScrollableMenu):
    def __init__(self, entries, cursor_char=BUILTIN_SYMBOLS['standard_arrow_right'],
                 select_char='o', preset_idx=None,
                 row_format="{entry} [{select_char}]", cycling=False):
        super().__init__(entries, cursor_char, cycling=cycling)
        self._select_char = select_char
        self._selected_idx = None
        self._row_format = row_format
        if preset_idx is not None:
            self._selected_idx = preset_idx

    def get_entry(self, idx):
        return self._row_format.format(cursor=self._get_cursor(idx), entry=self._entries[idx],
                                       select_char=(self._select_char if idx == self._selected_idx else ' '))

    def select(self):
        if self._selected_idx == self._current_idx:
            self._selected_idx = None
        else:
            self._selected_idx = self._current_idx

    @property
    def selected_idx(self):
        return self._selected_idx


class MenuOptionSwitcher(MenuOption):
    def __init__(self):
        super().__init__()
        self._current_menu_opt = None

    def switch(self, menu_opt):
        if self._current_menu_opt is not None:
            self._current_menu_opt.cleanup()
        self._current_menu_opt = menu_opt
        self._current_menu_opt.setup(self.config)
        self._current_menu_opt.begin()

    def setup(self, config):
        super().setup(config)

    def begin(self):
        self._current_menu_opt.begin()

    def redraw(self, menu):
        if self._current_menu_opt is not None:
            self._current_menu_opt.redraw(menu)

    def select(self):
        return self._current_menu_opt.select()

    def left(self):
        return self._current_menu_opt.left()

    def right(self):
        self._current_menu_opt.right()

    def up(self):
        self._current_menu_opt.up()

    def down(self):
        self._current_menu_opt.down()

    def cleanup(self):
        self._current_menu_opt.cleanup()
        self._current_menu_opt = None

    @property
    def current_menu_opt(self):
        return self._current_menu_opt
