#!/usr/bin/python

import sys
from django.core.management import setup_environ
from django.conf import settings
from profiles import thumbs

setup_environ(settings)
regenerate_thumbs()

