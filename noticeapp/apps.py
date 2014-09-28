# coding=utf-8
from __future__ import unicode_literals
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NoticeappConfig(AppConfig):
    name = 'noticeapp'
    verbose_name = _('Noticeappm notice solution')

    def ready(self):
        from noticeapp import signals
        signals.setup()