from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent
JAFF_DIR = CONFIG_DIR
SRC_DIR = CONFIG_DIR.parent
NETWORK_DIR = CONFIG_DIR.parent.parent / "network"
DATA_DIR = JAFF_DIR / "data"
XSECS_DATA_DIR = DATA_DIR / "xsecs"
SHIELDING_DATA_DIR = DATA_DIR / "shielding"
SHIELDING_FUNCTIONS_DIR = JAFF_DIR / "physics" / "photo_reactions" / "shielding"
