# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from noticeapp.models import Post, Course

from noticeapp.permissions import perms

class NoticeappFeed(Feed):
    feed_type = Atom1Feed

    def link(self):
        return reverse('noticeapp:index')

    def item_guid(self, obj):
        return str(obj.id)

    def item_pubdate(self, obj):
        return obj.created


class LastPosts(NoticeappFeed):
    title = _('Latest posts on notice')
    description = _('Latest posts on notice')
    title_template = 'noticeapp/feeds/posts_title.html'
    description_template = 'noticeapp/feeds/posts_description.html'

    def get_object(self, request, *args, **kwargs):
        return request.user

    def items(self, user):
        ids = [p.id for p in perms.filter_posts(user, Post.objects.only('id')).order_by('-created', '-id')[:15]]
        return Post.objects.filter(id__in=ids).select_related('course', 'course__notice', 'user')


class LastCourses(NoticeappFeed):
    title = _('Latest courses on notice')
    description = _('Latest courses on notice')
    title_template = 'noticeapp/feeds/courses_title.html'
    description_template = 'noticeapp/feeds/courses_description.html'

    def get_object(self, request, *args, **kwargs):
        return request.user

    def items(self, user):
        return perms.filter_courses(user, Course.objects.all()).order_by('-created', '-id')[:15]
