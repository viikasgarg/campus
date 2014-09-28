from __future__ import unicode_literals
from django.utils.timezone import now, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from noticeapp.models import Course

class Command(BaseCommand):
    help = 'Resave all posts.'

    def handle(self, *args, **kwargs):
        check_time = now() - timedelta(seconds=10)
        courses = Course.objects.filter(created__lt=check_time)\
                      .annotate(counter=Count('posts'))\
                      .filter(counter=0)

        count = courses.count()
        print 'Found %d invalid courses' % count
        if count:
            answer = raw_input('Are you sure you want delete them? [y/n]:')
            if answer.lower() == 'y':
                print 'Deleting courses'
                courses.delete()
                print 'Deletion completed'
            else:
                print 'Aborting'
