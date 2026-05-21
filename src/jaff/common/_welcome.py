from textwrap import dedent

import numpy as np

words: list[str] = [
    "Fabulous",
    "Fair",
    "Faithful",
    "Familiar",
    "Famous",
    "Fancy",
    "Fantastic",
    "Fast",
    "Fearless",
    "Feisty",
    "Festive",
    "Fiery",
    "Fine",
    "Firm",
    "Fit",
    "Flaky",
    "Flamboyant",
    "Flashy",
    "Flat",
    "Flawed",
    "Flawless",
    "Flexible",
    "Flimsy",
    "Flippin",
    "Floccinaucinihilipilificating",
    "Flowery",
    "Fluffy",
    "Focused",
    "Formal",
    "Fortunate",
    "Fragile",
    "Friendly",
    "Frightening",
    "Frugal",
    "Functional",
    "Functionless",
    "Funky",
    "Fuzzy",
]


def get_jaff_mode_dict(fword: str, mode: str = "default") -> tuple[str, str]:
    jaff_mode_dict: dict[str, dict[str, str]] = {
        "default": {
            "title": dedent(
                """
                ░░█ ▄▀█ █▀▀ █▀▀
                █▄█ █▀█ █▀░ █▀░
                """
            ),
            "sub_title": f"Just Another {fword.title()} Format!",
        },
        "jaffgen": {
            "title": dedent(
                """
                ░░█ ▄▀█ █▀▀ █▀▀ █▀▀ █▀▀ █▄░█
                █▄█ █▀█ █▀░ █▀░ █▄█ ██▄ █░▀█
                """
            ),
            "sub_title": f"Just Another {fword.title()} Format Generator!",
        },
        "jaffx": {
            "title": dedent(
                """
                ░░█ ▄▀█ █▀▀ █▀▀ ▀▄▀
                █▄█ █▀█ █▀░ █▀░ █░█
                """
            ),
            "sub_title": f"Just Another {fword.title()} Format Xecutor!",
        },
    }

    return jaff_mode_dict[mode]["title"], jaff_mode_dict[mode]["sub_title"]


def motd(mode: str = "default") -> str:
    fword = np.random.choice(words)
    title, sub_title = get_jaff_mode_dict(fword, mode)

    return f"{title}\n{sub_title}\n"
