#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


__title__ = 'oval'
from oval.version import version as __version__  # noqa: F401
__author__ = 'Joe Rivera <j@jriv.us>'
__repo__ = 'https://github.com/transfix/oval-charts'
__license__ = 'Copyright oval.bio 2021'


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
del logging, logger
