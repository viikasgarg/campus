# -*- coding: utf-8 -*-
"""
Extensible permission system for noticeappm
"""

from __future__ import unicode_literals
from django.utils.importlib import import_module
from django.db.models import Q

from noticeapp import defaults
from noticeapp.models import Course, PollAnswerUser


def _resolve_class(name):
    """ resolves a class function given as string, returning the function """
    if not name: return False
    modname, funcname = name.rsplit('.', 1)
    return getattr(import_module(modname), funcname)()


class DefaultPermissionHandler(object):
    """
    Default Permission handler. If you want to implement custom permissions (for example,
    private notices based on some application-specific settings), you can inherit from this
    class and override any of the `filter_*` and `may_*` methods. Methods starting with
    `may` are expected to return `True` or `False`, whereas methods starting with `filter_*`
    should filter the queryset they receive, and return a new queryset containing only the
    objects the user is allowed to see.

    To activate your custom permission handler, set `settings.PYBB_PERMISSION_HANDLER` to
    the full qualified name of your class, e.g. "`myapp.noticeapp_adapter.MyPermissionHandler`".
    """
    #
    # permission checks on categories
    #
    def filter_categories(self, user, qs):
        """ return a queryset with categories `user` is allowed to see """
        return qs.filter(hidden=False) if not user.is_staff else qs

    def may_view_category(self, user, category):
        """ return True if `user` may view this category, False if not """
        return user.is_staff or not category.hidden

    #
    # permission checks on notices
    #
    def filter_notices(self, user, qs):
        """ return a queryset with notices `user` is allowed to see """
        return qs.filter(Q(hidden=False) & Q(category__hidden=False)) if not user.is_staff else qs

    def may_view_notice(self, user, notice):
        """ return True if user may view this notice, False if not """
        return user.is_staff or ( notice.hidden == False and notice.category.hidden == False )

    def may_create_course(self, user, notice):
        """ return True if `user` is allowed to create a new course in `notice` """
        return user.has_perm('noticeapp.add_post')

    #
    # permission checks on courses
    #
    def filter_courses(self, user, qs):
        """ return a queryset with courses `user` is allowed to see """
        if not user.is_staff:
            qs = qs.filter(Q(notice__hidden=False) & Q(notice__category__hidden=False))
        if not user.is_superuser:
            if user.is_authenticated():
                qs = qs.filter(Q(notice__moderators=user) | Q(user=user) | Q(on_moderation=False)).distinct()
            else:
                qs = qs.filter(on_moderation=False)
        return qs

    def may_view_course(self, user, course):
        """ return True if user may view this course, False otherwise """
        if user.is_superuser:
            return True
        if not user.is_staff and (course.notice.hidden or course.notice.category.hidden):
            return False  # only staff may see hidden notice / category
        if course.on_moderation:
            return user.is_authenticated() and (user == course.user or user in course.notice.moderators)
        return True

    def may_moderate_course(self, user, course):
        return user.is_superuser or user in course.notice.moderators.all()

    def may_close_course(self, user, course):
        """ return True if `user` may close `course` """
        return self.may_moderate_course(user, course)

    def may_open_course(self, user, course):
        """ return True if `user` may open `course` """
        return self.may_moderate_course(user, course)

    def may_stick_course(self, user, course):
        """ return True if `user` may stick `course` """
        return self.may_moderate_course(user, course)

    def may_unstick_course(self, user, course):
        """ return True if `user` may unstick `course` """
        return self.may_moderate_course(user, course)

    def may_vote_in_course(self, user, course):
        """ return True if `user` may unstick `course` """
        return (
            user.is_authenticated() and course.poll_type != Course.POLL_TYPE_NONE and not course.closed and
            not PollAnswerUser.objects.filter(poll_answer__course=course, user=user).exists()
        )

    def may_create_post(self, user, course):
        """ return True if `user` is allowed to create a new post in `course` """

        if course.notice.hidden and (not user.is_staff):
            # if course is hidden, only staff may post
            return False

        if course.closed and (not user.is_staff):
            # if course is closed, only staff may post
            return False

        # only user which have 'noticeapp.add_post' permission may post
        return defaults.PYBB_ENABLE_ANONYMOUS_POST or user.has_perm('noticeapp.add_post')

    def may_post_as_admin(self, user):
        """ return True if `user` may post as admin """
        return user.is_staff

    #
    # permission checks on posts
    #
    def filter_posts(self, user, qs):
        """ return a queryset with posts `user` is allowed to see """

        # first filter by course availability
        if not user.is_staff:
            qs = qs.filter(Q(course__notice__hidden=False) & Q(course__notice__category__hidden=False))

        if not defaults.PYBB_PREMODERATION or user.is_superuser:
            # superuser may see all posts, also if premoderation is turned off moderation
            # flag is ignored
            return qs
        elif user.is_authenticated():
            # post is visible if user is author, post is not on moderation, or user is moderator
            # for this notice
            qs = qs.filter(Q(user=user) | Q(on_moderation=False) | Q(course__notice__moderators=user))
        else:
            # anonymous user may not see posts which are on moderation
            qs = qs.filter(on_moderation=False)
        return qs

    def may_view_post(self, user, post):
        """ return True if `user` may view `post`, False otherwise """
        if user.is_superuser:
            return True
        if post.on_moderation:
            return post.user == user or user in post.course.notice.moderators.all()
        return True

    def may_edit_post(self, user, post):
        """ return True if `user` may edit `post` """
        return user.is_superuser or post.user == user or self.may_moderate_course(user, post.course)

    def may_delete_post(self, user, post):
        """ return True if `user` may delete `post` """
        return self.may_moderate_course(user, post.course)

    #
    # permission checks on users
    #
    def may_block_user(self, user, user_to_block):
        """ return True if `user` may block `user_to_block` """
        return user.has_perm('noticeapp.block_users')

    def may_attach_files(self, user):
        """
        return True if `user` may attach files to posts, False otherwise.
        By default controlled by PYBB_ATTACHMENT_ENABLE setting
        """
        return defaults.PYBB_ATTACHMENT_ENABLE

    def may_create_poll(self, user):
        """
        return True if `user` may attach files to posts, False otherwise.
        By default always True
        """
        return True


perms = _resolve_class(defaults.PYBB_PERMISSION_HANDLER)