_ansi = {
    "gray": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "black": "\033[38m",

    "orange": "\033[38;5;11m",

    "dark_green": "\033[38;5;22m",
    "dark_red": "\033[38;5;88m",

    "clear": "\033[0m",

    "prev": "\033[F",
    "start": "\033[G",

    "bold": "\033[1m"
}

import sys

def pprint(fmt: str, *args, print_args = {}, **kwargs) -> None:
    print((fmt + "{clear}").format(*args, **{**kwargs, **_ansi}), **print_args)
    sys.stdout.flush()

def pprints(fmt: str, *args, **kwargs) -> str:
    return (fmt + "{clear}").format(*args, **{**kwargs, **_ansi})
