from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ColorScheme:
    normal: str = "white"
    error: str = "red"
    human_interaction: str = "blue"
    success: str = "green"
    warning: str = "yellow"
    message: str = "magenta"


colorscheme = ColorScheme()
