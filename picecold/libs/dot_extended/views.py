import os
import re
from collections import defaultdict

from dot3k.menu import MenuOption

from .base import ScrollableMenu


class ProgressBarView(MenuOption):
    def __init__(self, rows=('Progress Bar:', '{bar}', '{val:%}'), initial_value=0.0,
                 fill_char='*', empty_char=' ', total_len=16,
                 auto_center=True, callback_after_redraw=None):
        super().__init__()
        self._rows = rows
        self._total_len = total_len
        self._auto_center = auto_center
        self.fill_char = fill_char
        self.empty_char = empty_char
        self._call_after_redraw = callback_after_redraw
        self._bar = ''
        self._value = initial_value

    def redraw(self, menu):
        for i, row in enumerate(self._rows):
            text = row.format(bar=self._bar, val=self._value)
            menu.write_row(i, text.center(16) if self._auto_center else text)
        if self._call_after_redraw:
            self._call_after_redraw()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value > 1.0:
            value = 1.0
        elif value < 0.0:
            value = 0.0
        self._value = value
        filled_chars = round((self._total_len - 2) * value)
        self._bar = '[' + (self.fill_char * filled_chars) + \
                    (self.empty_char * ((self._total_len - 2) - filled_chars)) + ']'

    def increase(self, value):
        new_val = self.value + value
        self.value = new_val if new_val <= 1.0 else 1.0

    def decrease(self, value):
        new_percentage = self.value - value
        self.value = new_percentage if new_percentage >= 0.0 else 0.0


class PageView(MenuOption):
    scroll_speed = 300
    scroll_delay = 500

    class Page:
        def __init__(self, texts, page_format=("{text1}", "{text2}", "{nav}")):
            self.rows = []
            self.fixed_pre_texts = []
            for fmt in page_format:
                match = re.match("^(.+)({text1}|{text2}|{nav}.*)$", fmt)
                replacements = defaultdict(str,
                                           text1=texts[0] if len(texts) > 0 else "",
                                           text2=texts[1] if len(texts) > 1 else "",
                                           text3=texts[2] if len(texts) > 2 else "",
                                           nav="{nav}")
                if match:
                    self.fixed_pre_texts.append(match.group(1))
                    self.rows.append(match.group(2).format_map(replacements))
                else:
                    self.fixed_pre_texts.append("")
                    self.rows.append(fmt.format_map(replacements))  # TODO: Fix this

    def __init__(self, pages, auto_center=True, callback_after_redraw=None, callback_on_select=None):
        """
        Args:
            pages: List containing PageView.Pages
            auto_center: Automatically center the text
        """
        super().__init__()
        self._pages = pages
        self._auto_center = auto_center
        self._call_after_redraw = callback_after_redraw
        self._callback = callback_on_select
        self._current_page_idx = 0

    def redraw(self, menu):
        for i, row in enumerate(self._pages[self._current_page_idx].rows):
            if row == "{nav}":
                prev_visible = self._current_page_idx > 0
                next_visible = self._current_page_idx != len(self._pages) - 1
                text = (chr(251) if prev_visible else " ") + \
                       (str(self._current_page_idx + 1) + "/" + str(len(self._pages))).center(14) + \
                       (chr(252) if next_visible else " ")
                menu.write_row(i, text)
            else:
                menu.write_option(i, row.center(16) if self._auto_center else row,
                                  scroll=len(row) > 16,
                                  scroll_delay=self.scroll_delay,
                                  scroll_speed=self.scroll_speed,
                                  icon=self._pages[self._current_page_idx].fixed_pre_texts[i])
        if self._call_after_redraw is not None:
            self._call_after_redraw()

    def right(self):
        if self._current_page_idx < len(self._pages) - 1:
            self._current_page_idx += 1
        return True

    def left(self):
        if self._current_page_idx > 0:
            self._current_page_idx -= 1
        return True

    def select(self):
        if self._callback is not None:
            return self._callback()


class SelectFileView(ScrollableMenu):
    """
    Possibly only works when using base.MenuOptionSwitcher
    """

    class FileEntry:
        def __init__(self, file_path, file_entry_text):
            self.file_path = file_path
            self.file_entry_text = file_entry_text

        def __str__(self):
            return self.file_entry_text

        def __repr__(self):
            return str(self)

    def __init__(self, root, prompt="Select file", file_filter_pattern=".*", callback_on_select=None):
        self._callback = callback_on_select
        self._file_entries = SelectFileView._search_files(root, file_filter_pattern)
        super().__init__([str(entry) for entry in self._file_entries], prompt)

    @staticmethod
    def _search_files(search_directory, pattern):
        """Search files in the given search_directory which match the pattern.

        Args:
            search_directory: The directory to search in (not recursively).
            pattern: The pattern to use as filter (only matches will be included)

        Returns:
             List of FileEntry
        """
        file_names = os.listdir(search_directory)
        file_paths_filtered = []
        for name in file_names:
            if re.search(pattern, name):
                file_paths_filtered.append(SelectFileView.FileEntry(os.path.join(search_directory, name), name))
        return file_paths_filtered

    def select(self):
        if self._callback and len(self._file_entries) > 0:
            self._callback(self._file_entries[self._current_idx])

    @property
    def current_file_entry(self):
        return self._file_entries[self._current_idx]
