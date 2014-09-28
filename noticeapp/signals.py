# coding=utf-8
from __future__ import unicode_literals
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from noticeapp.models import Profile, Post
from noticeapp.subscription import notify_course_subscribers
from noticeapp import util, defaults, compat


def post_saved(instance, **kwargs):
    notify_course_subscribers(instance)

    if util.get_noticeapp_profile(instance.user).autosubscribe:
        instance.course.subscribers.add(instance.user)

    if kwargs['created']:
        profile = util.get_noticeapp_profile(instance.user)
        profile.post_count = instance.user.posts.count()
        profile.save()


def post_deleted(instance, **kwargs):
    profile = util.get_noticeapp_profile(instance.user)
    profile.post_count = instance.user.posts.count()
    profile.save()


def user_saved(instance, created, **kwargs):
    if not created:
        return
    try:
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'noticeapp', 'post')
        add_course_permission = Permission.objects.get_by_natural_key('add_course', 'noticeapp', 'course')
    except (Permission.DoesNotExist, ContentType.DoesNotExist):
        return
    instance.user_permissions.add(add_post_permission, add_course_permission)
    instance.save()
    if util.get_noticeapp_profile_model() == Profile:
        Profile(user=instance).save()


def setup():
    post_save.connect(post_saved, sender=Post)
    post_delete.connect(post_deleted, sender=Post)
    if defaults.PYBB_AUTO_USER_PERMISSIONS:
        post_save.connect(user_saved, sender=compat.get_user_model())