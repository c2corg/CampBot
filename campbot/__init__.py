"""
campbot is a package for automatic edition of camptocamp.org
"""

from campbot.core import CampBot
from campbot.processors import BBCodeRemover, LtagCleaner, BBCodeUrlRemover

__version__ = "0.0.5"
