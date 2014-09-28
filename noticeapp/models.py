# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import django

from django.core.urlresolvers import reverse
from django.db import models, transaction, DatabaseError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now as tznow

from noticeapp.compat import get_user_model_path, get_username_field, get_atomic_func
from noticeapp import defaults
from noticeapp.profiles import NoticeappProfile
from noticeapp.util import unescape, FilePathGenerator

from annoying.fields import AutoOneToOneField

try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["^annoying\.fields\.JSONField"])
    add_introspection_rules([], ["^annoying\.fields\.AutoOneToOneField"])
except ImportError:
    pass


@python_2_unicode_compatible
class Category(models.Model):
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    hidden = models.BooleanField(_('Hidden'), blank=False, null=False, default=False,
                                 help_text=_('If checked, this category will be visible only for staff'))

    class Meta(object):
        ordering = ['position']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.name

    def notice_count(self):
        return self.notices.all().count()

    def get_absolute_url(self):
        return reverse('noticeapp:category', kwargs={'pk': self.id})

    @property
    def courses(self):
        return Course.objects.filter(notice__category=self).select_related()

    @property
    def posts(self):
        return Post.objects.filter(course__notice__category=self).select_related()


@python_2_unicode_compatible
class Notice(models.Model):
    category = models.ForeignKey(Category, related_name='notices', verbose_name=_('Category'))
    parent = models.ForeignKey('self', related_name='child_notices', verbose_name=_('Parent notice'),
                               blank=True, null=True)
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    description = models.TextField(_('Description'), blank=True)
    moderators = models.ManyToManyField(get_user_model_path(), blank=True, null=True, verbose_name=_('Moderators'))
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    course_count = models.IntegerField(_('Course count'), blank=True, default=0)
    hidden = models.BooleanField(_('Hidden'), blank=False, null=False, default=False)
    readed_by = models.ManyToManyField(get_user_model_path(), through='NoticeReadTracker', related_name='readed_notices')
    headline = models.TextField(_('Headline'), blank=True, null=True)

    class Meta(object):
        ordering = ['position']
        verbose_name = _('Notice')
        verbose_name_plural = _('Notices')

    def __str__(self):
        return self.name

    def update_counters(self):
        posts = Post.objects.filter(course__notice_id=self.id)
        self.post_count = posts.count()
        self.course_count = Course.objects.filter(notice=self).count()
        try:
            last_post = posts.order_by('-created', '-id')[0]
            self.updated = last_post.updated or last_post.created
        except IndexError:
            pass

        self.save()

    def get_absolute_url(self):
        return reverse('noticeapp:notice', kwargs={'pk': self.id})

    @property
    def posts(self):
        return Post.objects.filter(course__notice=self).select_related()

    @property
    def last_post(self):
        try:
            return self.posts.order_by('-created', '-id')[0]
        except IndexError:
            return None

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        parents = [self.category]
        parent = self.parent
        while parent is not None:
            parents.insert(1, parent)
            parent = parent.parent
        return parents


@python_2_unicode_compatible
class Course(models.Model):
    POLL_TYPE_NONE = 0
    POLL_TYPE_SINGLE = 1
    POLL_TYPE_MULTIPLE = 2

    POLL_TYPE_CHOICES = (
        (POLL_TYPE_NONE, _('None')),
        (POLL_TYPE_SINGLE, _('Single answer')),
        (POLL_TYPE_MULTIPLE, _('Multiple answers')),
    )

    notice = models.ForeignKey(Notice, related_name='courses', verbose_name=_('Notice'))
    name = models.CharField(_('Subject'), max_length=255)
    created = models.DateTimeField(_('Created'), null=True)
    updated = models.DateTimeField(_('Updated'), null=True)
    user = models.ForeignKey(get_user_model_path(), verbose_name=_('User'), related_name='notice_user')
    views = models.IntegerField(_('Views count'), blank=True, default=0)
    sticky = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed = models.BooleanField(_('Closed'), blank=True, default=False)
    subscribers = models.ManyToManyField(get_user_model_path(), related_name='subscriptions',
                                         verbose_name=_('Subscribers'), blank=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    readed_by = models.ManyToManyField(get_user_model_path(), through='CourseReadTracker', related_name='readed_courses')
    on_moderation = models.BooleanField(_('On moderation'), default=False)
    poll_type = models.IntegerField(_('Poll type'), choices=POLL_TYPE_CHOICES, default=POLL_TYPE_NONE)
    poll_question = models.TextField(_('Poll question'), blank=True, null=True)

    class Meta(object):
        ordering = ['-created']
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')

    def __str__(self):
        return self.name

    @property
    def head(self):
        """
        Get first post and cache it for request
        """
        if not hasattr(self, "_head"):
            self._head = self.posts.all().order_by('created', 'id')
        if not len(self._head):
            return None
        return self._head[0]

    @property
    def last_post(self):
        if not getattr(self, '_last_post', None):
            self._last_post = self.posts.order_by('-created', '-id').select_related('user')[0]
        return self._last_post

    def get_absolute_url(self):
        return reverse('noticeapp:course', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created = tznow()
            self.updated = tznow()

        notice_changed = False
        old_course = None
        if self.id is not None:
            old_course = Course.objects.get(id=self.id)
            if self.notice != old_course.notice:
                notice_changed = True

        super(Course, self).save(*args, **kwargs)

        if notice_changed:
            old_course.notice.update_counters()
            self.notice.update_counters()

    def delete(self, using=None):
        super(Course, self).delete(using)
        self.notice.update_counters()

    def update_counters(self):
        self.post_count = self.posts.count()
        last_post = Post.objects.filter(course_id=self.id).order_by('-created', '-id')[0]
        self.updated = last_post.updated or last_post.created
        self.save()

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        parents = self.notice.get_parents()
        parents.append(self.notice)
        return parents

    def poll_votes(self):
        if self.poll_type != self.POLL_TYPE_NONE:
            return PollAnswerUser.objects.filter(poll_answer__course=self).count()
        else:
            return None


class RenderableItem(models.Model):
    """
    Base class for models that has markup, body, body_text and body_html fields.
    """

    class Meta(object):
        abstract = True

    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))

    def render(self):
        self.body_html = defaults.PYBB_MARKUP_ENGINES[defaults.PYBB_MARKUP](self.body)
        # Remove tags which was generated with the markup processor
        text = strip_tags(self.body_html)
        # Unescape entities which was generated with the markup processor
        self.body_text = unescape(text)


@python_2_unicode_compatible
class Post(RenderableItem):
    course = models.ForeignKey(Course, related_name='posts', verbose_name=_('Course'))
    user = models.ForeignKey(get_user_model_path(), related_name='posts', verbose_name=_('User'))
    created = models.DateTimeField(_('Created'), blank=True, db_index=True)
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    user_ip = models.IPAddressField(_('User IP'), blank=True, default='0.0.0.0')
    on_moderation = models.BooleanField(_('On moderation'), default=False)

    class Meta(object):
        ordering = ['created']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def summary(self):
        limit = 50
        tail = len(self.body) > limit and '...' or ''
        return self.body[:limit] + tail

    def __str__(self):
        return self.summary()

    def save(self, *args, **kwargs):
        created_at = tznow()
        if self.created is None:
            self.created = created_at
        self.render()

        new = self.pk is None

        course_changed = False
        old_post = None
        if not new:
            old_post = Post.objects.get(pk=self.pk)
            if old_post.course != self.course:
                course_changed = True

        super(Post, self).save(*args, **kwargs)

        # If post is course head and moderated, moderate course too
        if self.course.head == self and not self.on_moderation and self.course.on_moderation:
            self.course.on_moderation = False

        self.course.update_counters()
        self.course.notice.update_counters()

        if course_changed:
            old_post.course.update_counters()
            old_post.course.notice.update_counters()

    def get_absolute_url(self):
        return reverse('noticeapp:post', kwargs={'pk': self.id})

    def delete(self, *args, **kwargs):
        self_id = self.id
        head_post_id = self.course.posts.order_by('created', 'id')[0].id

        if self_id == head_post_id:
            self.course.delete()
        else:
            super(Post, self).delete(*args, **kwargs)
            self.course.update_counters()
            self.course.notice.update_counters()

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        return self.course.notice.category, self.course.notice, self.course,


class Profile(NoticeappProfile):
    """
    Profile class that can be used if you doesn't have
    your site profile.
    """
    user = AutoOneToOneField(get_user_model_path(), related_name='noticeapp_profile', verbose_name=_('User'))

    class Meta(object):
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def get_absolute_url(self):
        return reverse('noticeapp:user', kwargs={'username': getattr(self.user, get_username_field())})


class Attachment(models.Model):
    class Meta(object):
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    post = models.ForeignKey(Post, verbose_name=_('Post'), related_name='attachments')
    size = models.IntegerField(_('Size'))
    file = models.FileField(_('File'),
                            upload_to=FilePathGenerator(to=defaults.PYBB_ATTACHMENT_UPLOAD_TO))

    def save(self, *args, **kwargs):
        self.size = self.file.size
        super(Attachment, self).save(*args, **kwargs)

    def size_display(self):
        size = self.size
        if size < 1024:
            return '%db' % size
        elif size < 1024 * 1024:
            return '%dKb' % int(size / 1024)
        else:
            return '%.2fMb' % (size / float(1024 * 1024))


class CourseReadTrackerManager(models.Manager):
    def get_or_create_tracker(self, user, course):
        """
        Correctly create tracker in mysql db on default REPEATABLE READ transaction mode

        It's known problem when standrard get_or_create method return can raise exception
        with correct data in mysql database.
        See http://stackoverflow.com/questions/2235318/how-do-i-deal-with-this-race-condition-in-django/2235624
        """
        is_new = True
        sid = transaction.savepoint(using=self.db)
        try:
            with get_atomic_func()():
                obj = CourseReadTracker.objects.create(user=user, course=course)
            transaction.savepoint_commit(sid)
        except DatabaseError:
            transaction.savepoint_rollback(sid)
            obj = CourseReadTracker.objects.get(user=user, course=course)
            is_new = False
        return obj, is_new


class CourseReadTracker(models.Model):
    """
    Save per user course read tracking
    """
    user = models.ForeignKey(get_user_model_path(), blank=False, null=False)
    course = models.ForeignKey(Course, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now=True)

    objects = CourseReadTrackerManager()

    class Meta(object):
        verbose_name = _('Course read tracker')
        verbose_name_plural = _('Course read trackers')
        unique_together = ('user', 'course')


class NoticeReadTrackerManager(models.Manager):
    def get_or_create_tracker(self, user, notice):
        """
        Correctly create tracker in mysql db on default REPEATABLE READ transaction mode

        It's known problem when standrard get_or_create method return can raise exception
        with correct data in mysql database.
        See http://stackoverflow.com/questions/2235318/how-do-i-deal-with-this-race-condition-in-django/2235624
        """
        is_new = True
        sid = transaction.savepoint(using=self.db)
        try:
            with get_atomic_func()():
                obj = NoticeReadTracker.objects.create(user=user, notice=notice)
            transaction.savepoint_commit(sid)
        except DatabaseError:
            transaction.savepoint_rollback(sid)
            is_new = False
            obj = NoticeReadTracker.objects.get(user=user, notice=notice)
        return obj, is_new


class NoticeReadTracker(models.Model):
    """
    Save per user notice read tracking
    """
    user = models.ForeignKey(get_user_model_path(), blank=False, null=False)
    notice = models.ForeignKey(Notice, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now=True)

    objects = NoticeReadTrackerManager()

    class Meta(object):
        verbose_name = _('Notice read tracker')
        verbose_name_plural = _('Notice read trackers')
        unique_together = ('user', 'notice')


@python_2_unicode_compatible
class PollAnswer(models.Model):
    course = models.ForeignKey(Course, related_name='poll_answers', verbose_name=_('Course'))
    text = models.CharField(max_length=255, verbose_name=_('Text'))

    class Meta:
        verbose_name = _('Poll answer')
        verbose_name_plural = _('Polls answers')

    def __str__(self):
        return self.text

    def votes(self):
        return self.users.count()

    def votes_percent(self):
        course_votes = self.course.poll_votes()
        if course_votes > 0:
            return 1.0 * self.votes() / course_votes * 100
        else:
            return 0


@python_2_unicode_compatible
class PollAnswerUser(models.Model):
    poll_answer = models.ForeignKey(PollAnswer, related_name='users', verbose_name=_('Poll answer'))
    user = models.ForeignKey(get_user_model_path(), related_name='poll_answers', verbose_name=_('User'))
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Poll answer user')
        verbose_name_plural = _('Polls answers users')
        unique_together = (('poll_answer', 'user', ), )

    def __str__(self):
        return '%s - %s' % (self.poll_answer.course, self.user)


if django.VERSION[:2] < (1, 7):
    from noticeapp import signals
    signals.setup()
