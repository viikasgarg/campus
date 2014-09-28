#!/usr/bin/env python
# vim:fileencoding=utf-8

from __future__ import unicode_literals
__author__ = 'zeus'

from django.core.management.base import BaseCommand, CommandError
from noticeapp.models import Course, Notice

class Command(BaseCommand):
    help = 'Recalc post counters for notices and courses'

    def handle(self, *args, **options):

        for course in Course.objects.all():
            course.update_counters()
            self.stdout.write('Successfully updated course "%s"\n' % course)

        for notice in Notice.objects.all():
            notice.update_counters()
            self.stdout.write('Successfully updated notice "%s"\n' % notice)
