# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import inspect

import math
import time
import warnings

from django import template
from django.core.cache import cache
from django.template.base import get_library, InvalidTemplateLibrary, TemplateSyntaxError, TOKEN_BLOCK
from django.template.defaulttags import LoadNode, CommentNode, IfNode
from django.template.smartif import Literal
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_text
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat
from django.utils.timezone import timedelta
from django.utils.timezone import now as tznow

try:
    import pytils
    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from noticeapp.models import CourseReadTracker, NoticeReadTracker, PollAnswerUser, Course, Post
from noticeapp.permissions import perms
from noticeapp import defaults, util


register = template.Library()


#noinspection PyUnusedLocal
@register.tag
def noticeapp_time(parser, token):
    try:
        tag, context_time = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('noticeapp_time requires single argument')
    else:
        return NoticeappTimeNode(context_time)


class NoticeappTimeNode(template.Node):
    def __init__(self, time):
    #noinspection PyRedeclaration
        self.time = template.Variable(time)

    def render(self, context):
        context_time = self.time.resolve(context)

        delta = tznow() - context_time
        today = tznow().replace(hour=0, minute=0, second=0)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        if delta.days == 0:
            if delta.seconds < 60:
                if context['LANGUAGE_CODE'].startswith('ru') and pytils_enabled:
                    msg = _('seconds ago,seconds ago,seconds ago')
                    msg = pytils.numeral.choose_plural(delta.seconds, msg)
                else:
                    msg = _('seconds ago')
                return '%d %s' % (delta.seconds, msg)

            elif delta.seconds < 3600:
                minutes = int(delta.seconds / 60)
                if context['LANGUAGE_CODE'].startswith('ru') and pytils_enabled:
                    msg = _('minutes ago,minutes ago,minutes ago')
                    msg = pytils.numeral.choose_plural(minutes, msg)
                else:
                    msg = _('minutes ago')
                return '%d %s' % (minutes, msg)
        if context['user'].is_authenticated():
            if time.daylight:
                tz1 = time.altzone
            else:
                tz1 = time.timezone
            tz = tz1 + util.get_noticeapp_profile(context['user']).time_zone * 60 * 60
            context_time = context_time + timedelta(seconds=tz)
        if today < context_time < tomorrow:
            return _('today, %s') % context_time.strftime('%H:%M')
        elif yesterday < context_time < today:
            return _('yesterday, %s') % context_time.strftime('%H:%M')
        else:
            return dateformat.format(context_time, 'd M, Y H:i')


@register.simple_tag
def noticeapp_link(object, anchor=''):
    """
    Return A tag with link to object.
    """

    url = hasattr(object, 'get_absolute_url') and object.get_absolute_url() or None
    #noinspection PyRedeclaration
    anchor = anchor or smart_text(object)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))


@register.filter
def noticeapp_course_moderated_by(course, user):
    """
    Check if user is moderator of course's notice.
    """
    warnings.warn("noticeapp_course_moderated_by filter is deprecated and will be removed in later releases. "
                  "Use noticeapp_may_moderate_course(user, course) filter instead",
                  DeprecationWarning)
    return perms.may_moderate_course(user, course)

@register.filter
def noticeapp_editable_by(post, user):
    """
    Check if the post could be edited by the user.
    """
    warnings.warn("noticeapp_editable_by filter is deprecated and will be removed in later releases. "
                  "Use noticeapp_may_edit_post(user, post) filter instead",
                  DeprecationWarning)
    return perms.may_edit_post(user, post)


@register.filter
def noticeapp_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """
    return post.user == user


@register.filter
def noticeapp_is_course_unread(course, user):
    if not user.is_authenticated():
        return False

    last_course_update = course.updated or course.created

    unread = not NoticeReadTracker.objects.filter(
        notice=course.notice,
        user=user.id,
        time_stamp__gte=last_course_update).exists()
    unread &= not CourseReadTracker.objects.filter(
        course=course,
        user=user.id,
        time_stamp__gte=last_course_update).exists()
    return unread


@register.filter
def noticeapp_course_unread(courses, user):
    """
    Mark all courses in queryset/list with .unread for target user
    """
    course_list = list(courses)

    if user.is_authenticated():
        for course in course_list:
            course.unread = True

        notices_ids = [f.notice_id for f in course_list]
        notice_marks = dict([(m.notice_id, m.time_stamp)
                            for m
                            in NoticeReadTracker.objects.filter(user=user, notice__in=notices_ids)])
        if len(notice_marks):
            for course in course_list:
                course_updated = course.updated or course.created
                if course.notice.id in notice_marks and course_updated <= notice_marks[course.notice.id]:
                    course.unread = False

        qs = CourseReadTracker.objects.filter(user=user, course__in=course_list).select_related('course')
        course_marks = list(qs)
        course_dict = dict(((course.id, course) for course in course_list))
        for mark in course_marks:
            if course_dict[mark.course.id].updated <= mark.time_stamp:
                course_dict[mark.course.id].unread = False
    return course_list


@register.filter
def noticeapp_notice_unread(notices, user):
    """
    Check if notice has unread messages.
    """
    notice_list = list(notices)
    if user.is_authenticated():
        for notice in notice_list:
            notice.unread = notice.course_count > 0
        notice_marks = NoticeReadTracker.objects.filter(
            user=user,
            notice__in=notice_list
        ).select_related('notice')
        notice_dict = dict(((notice.id, notice) for notice in notice_list))
        for mark in notice_marks:
            curr_notice = notice_dict[mark.notice.id]
            if (curr_notice.updated is None) or (curr_notice.updated <= mark.time_stamp):
                if not any((f.unread for f in noticeapp_notice_unread(curr_notice.child_notices.all(), user))):
                    notice_dict[mark.notice.id].unread = False
    return notice_list


@register.filter
def noticeapp_course_inline_pagination(course):
    page_count = int(math.ceil(course.post_count / float(defaults.PYBB_TOPIC_PAGE_SIZE)))
    if page_count <= 5:
        return range(1, page_count+1)
    return range(1, 5) + ['...', page_count]


@register.filter
def noticeapp_course_poll_not_voted(course, user):
    return not PollAnswerUser.objects.filter(poll_answer__course=course, user=user).exists()


@register.filter
def endswith(str, substr):
    return str.endswith(substr)


@register.assignment_tag
def noticeapp_get_profile(*args, **kwargs):
    try:
        return util.get_noticeapp_profile(kwargs.get('user') or args[0])
    except:
        return util.get_noticeapp_profile_model().objects.none()


@register.assignment_tag(takes_context=True)
def noticeapp_get_latest_courses(context, cnt=5, user=None):
    qs = Course.objects.all().order_by('-updated', '-created', '-id')
    if not user:
        user = context['user']
    qs = perms.filter_courses(user, qs)
    return qs[:cnt]


@register.assignment_tag(takes_context=True)
def noticeapp_get_latest_posts(context, cnt=5, user=None):
    qs = Post.objects.all().order_by('-created', '-id')
    if not user:
        user = context['user']
    qs = perms.filter_posts(user, qs)
    return qs[:cnt]


def load_perms_filters():
    def partial(func_name, perms_obj):
        def newfunc(user, obj):
            return getattr(perms_obj, func_name)(user, obj)
        return newfunc

    def partial_no_param(func_name, perms_obj):
        def newfunc(user):
            return getattr(perms_obj, func_name)(user)
        return newfunc

    for method in inspect.getmembers(perms):
        if inspect.ismethod(method[1]) and inspect.getargspec(method[1]).args[0] == 'self' and\
                (method[0].startswith('may') or method[0].startswith('filter')):
            if len(inspect.getargspec(method[1]).args) == 3:
                register.filter('%s%s' % ('noticeapp_', method[0]), partial(method[0], perms))
            elif len(inspect.getargspec(method[1]).args) == 2: # only user should be passed to permission method
                register.filter('%s%s' % ('noticeapp_', method[0]), partial_no_param(method[0], perms))
load_perms_filters()

# next two tags copied from https://bitbucket.org/jaap3/django-friendly-tag-loader

@register.tag
def friendly_load(parser, token):
    """
    Tries to load a custom template tag set. Non existing tag libraries
    are ignored.

    This means that, if used in conjuction with ``if_has_tag``, you can try to
    load the comments template tag library to enable comments even if the
    comments framework is not installed.

    For example::

        {% load friendly_loader %}
        {% friendly_load comments webdesign %}

        {% if_has_tag render_comment_list %}
            {% render_comment_list for obj %}
        {% else %}
            {% if_has_tag lorem %}
                {% lorem %}
            {% endif_has_tag %}
        {% endif_has_tag %}
    """
    bits = token.contents.split()
    for taglib in bits[1:]:
        try:
            lib = get_library(taglib)
            parser.add_library(lib)
        except InvalidTemplateLibrary:
            pass
    return LoadNode()


@register.tag
def if_has_tag(parser, token):
    """
    The logic for both ``{% if_has_tag %}`` and ``{% if not_has_tag %}``.

    Checks if all the given tags exist (or not exist if ``negate`` is ``True``)
    and then only parses the branch that will not error due to non-existing
    tags.

    This means that the following is essentially the same as a
    ``{% comment %}`` tag::

      {% if_has_tag non_existing_tag %}
          {% non_existing_tag %}
      {% endif_has_tag %}

    Another example is checking a built-in tag. This will alway render the
    current year and never FAIL::

      {% if_has_tag now %}
          {% now \"Y\" %}
      {% else %}
          FAIL
      {% endif_has_tag %}
    """
    bits = list(token.split_contents())
    if len(bits) < 2:
        raise TemplateSyntaxError("%r takes at least one arguments" % bits[0])
    end_tag = 'end%s' % bits[0]
    has_tag = all([tag in parser.tags for tag in bits[1:]])
    nodelist_true = nodelist_false = CommentNode()
    if has_tag:
        nodelist_true = parser.parse(('else', end_tag))
        token = parser.next_token()
        if token.contents == 'else':
            parser.skip_past(end_tag)
    else:
        while parser.tokens:
            token = parser.next_token()
            if token.token_type == TOKEN_BLOCK and token.contents == end_tag:
                try:
                    return IfNode([(Literal(has_tag), nodelist_true),
                                   (None, nodelist_false)])
                except TypeError:  # < 1.4
                    return IfNode(Literal(has_tag), nodelist_true, nodelist_false)
            elif token.token_type == TOKEN_BLOCK and token.contents == 'else':
                break
        nodelist_false = parser.parse((end_tag,))
        token = parser.next_token()
    try:
        return IfNode([(Literal(has_tag), nodelist_true),
                       (None, nodelist_false)])
    except TypeError:  # < 1.4
        return IfNode(Literal(has_tag), nodelist_true, nodelist_false)


@register.filter
def noticeappm_calc_course_views(course):
    cache_key = util.build_cache_key('anonymous_course_views', course_id=course.id)
    return course.views + cache.get(cache_key, 0)