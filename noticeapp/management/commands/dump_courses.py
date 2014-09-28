#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import unicode_literals
__author__ = 'zeus'

from django.core.management.base import BaseCommand
from noticeapp.models import Course, Post
from django.core import serializers


class Command(BaseCommand):
    args = '<course_id course_id>'
    help = 'Dump target courses to json'

    def handle(self, *args, **options):
        ids = [int(course_id) for course_id in args]
        objects = list(Course.objects.filter(id__in=ids)) + list(Post.objects.filter(course_id__in=ids))
        dump = serializers.serialize('json', objects)
        self.stdout.write(dump)
