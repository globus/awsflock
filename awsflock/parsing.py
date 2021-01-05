import collections
import re

import click

_windownames = {
    "seconds": ["s", "sec", "second", "seconds"],
    "minutes": ["m", "min", "minute", "minutes"],
    "hours": ["h", "hr", "hrs", "hour", "hours"],
    "days": ["d", "day", "days"],
}
_str2window = {v: k for k, vs in _windownames.items() for v in vs}
_window2factor = {"seconds": 1, "minutes": 60, "hours": 60 * 60, "days": 60 * 60 * 24}

ResolvedDuration = collections.namedtuple("ResolvedDuration", ["seconds", "unit"])


class Duration(click.ParamType):
    name = "Duration"

    _valid_re = re.compile(r"\s*(\d+)(\s)?(\w+)?\s*")

    def convert(self, value, param, ctx):
        if value is None or (ctx and ctx.resilient_parsing):
            return
        match = self._valid_re.fullmatch(value)
        if not match:
            self.fail(f"'{value}' is not a valid duration", param=param, ctx=ctx)

        num = int(match.group(1))
        window = match.group(3)
        if window and window not in _str2window:
            self.fail(f"'{window}' is not a valid duration unit", param=param, ctx=ctx)

        window = _str2window.get(window, "seconds")  # default to seconds
        factor = _window2factor[window]

        return ResolvedDuration(num * factor, window)
