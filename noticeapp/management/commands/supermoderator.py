from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError
from noticeapp import compat

from noticeapp.models import Notice


class Command(BaseCommand):
    help = 'Set and remove moderator to all notices'
    args = '{add|del} username'

    def handle(self, *args, **kwargs):
        if len(args) != 2:
            raise CommandError("Enter action {add|del} and username")
        action, username = args
        assert action in ('add', 'del')
        user = compat.get_user_model().objects.get(**{compat.get_username_field(): username})
        notices = Notice.objects.all()
        for notice in notices:
            notice.moderators.remove(user)
            if action == 'add':
                notice.moderators.add(user)
