from __future__ import annotations

import logging
import re
from pathlib import Path

from ulauncher.config import PATHS

logger = logging.getLogger()
CSS_RESET = """
* {
  color: inherit;
  font-size: inherit;
  font-family: inherit;
  font-style: inherit;
  font-variant: inherit;
  font-weight: inherit;
  text-shadow: inherit;
  background-color: initial;
  box-shadow: initial;
  margin: initial;
  padding: initial;
  border-color: initial;
  border-style: initial;
  border-width: initial;
  border-radius: initial;
  outline-color: initial;
  outline-style: initial;
  outline-width: initial;
  outline-offset: initial;
  background-clip: initial;
  background-origin: initial;
  background-size: initial;
  background-position: initial;
  background-repeat: initial;
  background-image: initial;
  transition-property: initial;
  transition-duration: initial;
  transition-timing-function: initial;
  transition-delay: initial;
}
"""

def get_theme_css(theme_name: str) -> str:
    """
    Gets a dict with the theme name as the key and theme as the value
    """
    css_theme_paths = [
        *Path(PATHS.SYSTEM_THEMES).glob("*.css"),
        *Path(PATHS.USER_THEMES).glob("*.css"),
    ]
    theme_path = next(path for path in css_theme_paths if path.stem == theme_name)
    content = theme_path.read_text()
    return CSS_RESET + re.sub(r"(?<=url\([\"\'])(\./)?(?!\/)", f"{theme_path.parent}/", content)
