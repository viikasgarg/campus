#!/usr/bin/env python
# vim:fileencoding=utf-8

from __future__ import unicode_literals
__author__ = 'zeus'

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from django.contrib.contenttypes.models import ContentType
from django.conf import settings

class Command(BaseCommand):
    args = ''
    help = 'Migrate noticeapp profiles to local site profile'

    def handle(self, *args, **options):
        profile_app, profile_model = settings.AUTH_PROFILE_MODULE.split('.')
        profile_model = ContentType.objects.get(app_label=profile_app, model=profile_model).model_class()
        for user in User.objects.all():
            #print(u'migrating profile for %s\n' % user.username)
            noticeapp_profile = user.noticeapp_profile
            try:
                profile = user.get_profile()
            except profile_model.DoesNotExist:
                profile = profile_model(user=user)
            profile.avatar = noticeapp_profile.avatar
            profile.signature = noticeapp_profile.signature
            profile.signature_html = noticeapp_profile.signature_html
            profile.time_zone = noticeapp_profile.time_zone
            profile.language = noticeapp_profile.language
            profile.show_signatures = noticeapp_profile.show_signatures
            profile.markup = noticeapp_profile.markup
            profile.post_count = noticeapp_profile.post_count
            profile.avatar = noticeapp_profile.avatar
            profile.save()
        self.stdout.write('All profiles successfuly migrated')
