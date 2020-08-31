#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from wsgiref.handlers import CGIHandler
from hello import application

CGIHandler.run(application)