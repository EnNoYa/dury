from yacs.config import CfgNode as CN

_C = CN()

# Base Options
_C.PLATFORM = "pixiv" # one of (pixiv, ...)
_C.OUTPUT_DIR = "output"

# Configs for Selenium
_C.SELENIUM = CN()
_C.SELENIUM.CHROMEDRIVER_PATH = "./chromedriver"
_C.SELENIUM.SAFE_DELAY = 2 # force deply for safe navigation (seconds)
_C.SELENIUM.COOKIE_FILE = "cookies.json"
_C.SELENIUM.HEADLESS = False

# Configs for pixiv
_C.PIXIV = CN()
_C.PIXIV.USERNAME = ""
_C.PIXIV.PASSWORD = ""

# Configs for TwitchTV

# Configs for YouTube

# Configs fot Twitter

# Configs for Instagram

# Configs for Facebook

def get_default_config():
    return _C.clone()
