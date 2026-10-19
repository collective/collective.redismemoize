"""Redis-backed storage for plone.memoize, shared across Plone instances."""

import logging


__version__ = "1.0.0a0"

PACKAGE_NAME = "collective.redismemoize"

logger = logging.getLogger(PACKAGE_NAME)
