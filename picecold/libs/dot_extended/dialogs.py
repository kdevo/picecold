import threading
import time

from dot3k.menu import MenuOption


class SimpleDialog(MenuOption):
    scroll_speed = 300
    scroll_delay = 500

    def __init__(self, rows=("Question", "Use left/right arrows to select", "{answers}"),
                 negative="[No]", positive="[Yes]", auto_center=True,
                 callback_on_positive=None, callback_on_negative=None):
        super().__init__()
        self.rows = rows
        self.negative = negative
        self.positive = positive
        self._auto_center = auto_center
        self._selected = None
        self._callback_on_positive = callback_on_positive
        self._callback_on_negative = callback_on_negative

    def redraw(self, menu):
        for i, row in enumerate(self.rows):
            if "{answers}" in row:
                spaces = 16 - (len(self.negative) + len(self.positive) + 2)
                answers = self.negative + (chr(251) if self.selected_answer == self.negative else " ") \
                          + (" " * spaces if spaces > 0 else "") \
                          + (chr(252) if self.selected_answer == self.positive else " ") + self.positive
                menu.write_row(i, answers)
            else:
                menu.write_option(i, row.center(16) if self._auto_center else row,
                                  scroll=len(row) > 16,
                                  scroll_delay=SimpleDialog.scroll_delay, scroll_speed=SimpleDialog.scroll_speed)
        time.sleep(0.01)

    def select_answer(self, opt):
        self._selected = opt

    def right(self):
        self.select_answer(self.positive)
        return True

    def left(self):
        self.select_answer(self.negative)
        return True

    def up(self):
        return self.right()

    def down(self):
        return self.left()

    @property
    def selected_answer(self):
        return self._selected

    def select(self):
        if self._callback_on_positive is not None and self.selected_answer == self.positive:
            return self._callback_on_positive()
        elif self._callback_on_negative is not None and self.selected_answer == self.negative:
            return self._callback_on_negative()
        if self.selected_answer is None:
            return False
        else:
            return True


class SimpleMessage(MenuOption):
    scroll_speed = 300
    scroll_delay = 500

    def __init__(self, rows=("Information", "This is a simple message", "{button}"), button="[OK]",
                 blink=True, auto_center=True, auto_button=True):
        super().__init__()
        self.rows = rows
        self.button = button
        self._blink = blink
        self._auto_center = auto_center

        self._blink_timer = None
        self._show_arrows = True

        if auto_button and len(self.rows) < 3:
            self.rows.append("{button}")

    def begin(self):
        if self._blink:
            self._start_animation_timer()

    def redraw(self, menu):
        for i, row in enumerate(self.rows):
            if "{button}" in row:
                if self._show_arrows:
                    menu.write_row(i, (chr(252) + self.button + chr(251)).center(16))
                else:
                    menu.write_row(i, self.button.center(16))
            else:
                menu.write_option(i, row.center(16) if self._auto_center else row,
                                  scroll=len(row) > 16, scroll_delay=self.scroll_delay, scroll_speed=self.scroll_speed)
        time.sleep(0.01)

    def cleanup(self):
        if self._blink_timer is not None:
            self._blink_timer.cancel()

    def _start_animation_timer(self):
        if self._blink_timer is None or self._blink_timer.finished:
            self._show_arrows = not self._show_arrows
            self._blink_timer = threading.Timer(1.0, self._start_animation_timer)
            self._blink_timer.start()


class StatusMessage(SimpleMessage):
    _COLOR_MAP = {"Success": [0, 255, 0],
                  "Info": [0, 0, 255],
                  "Note": [0, 0, 255],
                  "Warning": [255, 255, 0],
                  "Error": [255, 0, 0]}

    def __init__(self, rows, backlight):
        super().__init__(rows)
        self._backlight = backlight
        self._color = None
        for kw in self._COLOR_MAP:
            if kw in rows[0]:
                self._color = self._COLOR_MAP[kw]

    def begin(self):
        super().begin()
        if self._color is not None:
            self._backlight.rgb(self._color[0], self._color[1], self._color[2])

    def cleanup(self):
        super().cleanup()
        self._backlight.rgb(int(self.get_option('Backlight', 'r', 255)),
                            int(self.get_option('Backlight', 'g', 255)),
                            int(self.get_option('Backlight', 'b', 255)))

    def select(self):
        self.cleanup()
        return super().select()
