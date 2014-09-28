# coding: utf-8

from __future__ import unicode_literals
import time
import datetime
import os

from django.contrib.auth.models import Permission
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import timezone
from noticeapp import permissions, views as noticeapp_views
from noticeapp.templatetags.noticeapp_tags import noticeapp_is_course_unread, noticeapp_course_unread, noticeapp_notice_unread, \
    noticeapp_get_latest_courses, noticeapp_get_latest_posts

from noticeapp import compat, util

User = compat.get_user_model()
username_field = compat.get_username_field()

try:
    from lxml import html
except ImportError:
    raise Exception('PyBB requires lxml for self testing')

from noticeapp import defaults
from noticeapp.models import Course, CourseReadTracker, Notice, NoticeReadTracker, Post, Category, PollAnswer, Profile

__author__ = 'zeus'


class SharedTestModule(object):
    def create_user(self):
        self.user = User.objects.create_user('zeus', 'zeus@localhost', 'zeus')

    def login_client(self, username='zeus', password='zeus'):
        self.client.login(username=username, password=password)

    def create_initial(self, post=True):
        self.category = Category.objects.create(name='foo')
        self.notice = Notice.objects.create(name='xfoo', description='bar', category=self.category)
        self.course = Course.objects.create(name='ecourse', notice=self.notice, user=self.user)
        if post:
            self.post = Post.objects.create(course=self.course, user=self.user, body='bbcode [b]test[/b]')

    def get_form_values(self, response, form="post-form"):
        return dict(html.fromstring(response.content).xpath('//form[@class="%s"]' % form)[0].form_values())

    def get_with_user(self, url, username=None, password=None):
        if username:
            self.client.login(username=username, password=password)
        r = self.client.get(url)
        self.client.logout()
        return r


class FeaturesTest(TestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = False
        defaults.PYBB_ENABLE_ANONYMOUS_POST = False
        self.create_user()
        self.create_initial()
        mail.outbox = []

    def test_base(self):
        # Check index page
        Notice.objects.create(name='xfoo1', description='bar1', category=self.category, parent=self.notice)
        url = reverse('noticeapp:index')
        response = self.client.get(url)
        parser = html.HTMLParser(encoding='utf8')
        tree = html.fromstring(response.content, parser=parser)
        self.assertContains(response, 'foo')
        self.assertContains(response, self.notice.get_absolute_url())
        self.assertTrue(defaults.PYBB_DEFAULT_TITLE in tree.xpath('//title')[0].text_content())
        self.assertEqual(len(response.context['categories']), 1)
        self.assertEqual(len(response.context['categories'][0].notices_accessed), 1)

    def test_notice_page(self):
        # Check notice page
        response = self.client.get(self.notice.get_absolute_url())
        self.assertEqual(response.context['notice'], self.notice)
        tree = html.fromstring(response.content)
        self.assertTrue(tree.xpath('//a[@href="%s"]' % self.course.get_absolute_url()))
        self.assertTrue(tree.xpath('//title[contains(text(),"%s")]' % self.notice.name))
        self.assertFalse(tree.xpath('//a[contains(@href,"?page=")]'))
        self.assertFalse(response.context['is_paginated'])

    def test_category_page(self):
        Notice.objects.create(name='xfoo1', description='bar1', category=self.category, parent=self.notice)
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.notice.get_absolute_url())
        self.assertEqual(len(response.context['object'].notices_accessed), 1)

    def test_profile_language_default(self):
        user = User.objects.create_user(username='user2', password='user2', email='user2@example.com')
        self.assertEqual(util.get_noticeapp_profile(user).language, settings.LANGUAGE_CODE)

    def test_profile_edit(self):
        # Self profile edit
        self.login_client()
        response = self.client.get(reverse('noticeapp:edit_profile'))
        self.assertEqual(response.status_code, 200)
        values = self.get_form_values(response, 'profile-edit')
        values['signature'] = 'test signature'
        response = self.client.post(reverse('noticeapp:edit_profile'), data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test signature')
        # Test empty signature
        values['signature'] = ''
        response = self.client.post(reverse('noticeapp:edit_profile'), data=values, follow=True)
        self.assertEqual(len(response.context['form'].errors), 0)

    def test_pagination_and_course_addition(self):
        for i in range(0, defaults.NOTICE_APP_PAGE_SIZE + 3):
            course = Course(name='course_%s_' % i, notice=self.notice, user=self.user)
            course.save()
        url = reverse('noticeapp:notice', args=[self.notice.id])
        response = self.client.get(url)
        self.assertEqual(len(response.context['course_list']), defaults.NOTICE_APP_PAGE_SIZE)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['paginator'].num_pages,
                         int((defaults.NOTICE_APP_PAGE_SIZE + 3) / defaults.NOTICE_APP_PAGE_SIZE) + 1)

    def test_default_bbcode_processor(self):
        bbcode_to_html_map = [
            ['[b]bold[/b]', '<strong>bold</strong>'],
            ['[i]italic[/i]', '<em>italic</em>'],
            ['[u]underline[/u]', '<u>underline</u>'],
            ['[s]striked[/s]', '<strike>striked</strike>'],
            ['[img]http://domain.com/image.png[/img]', '<img src="http://domain.com/image.png"></img>',
                                                       '<img src="http://domain.com/image.png">'],
            ['[url=google.com]search in google[/url]', '<a href="http://google.com">search in google</a>'],
            ['http://google.com', '<a href="http://google.com">http://google.com</a>'],
            ['[list][*]1[*]2[/list]', '<ul><li>1</li><li>2</li></ul>'],
            ['[list=1][*]1[*]2[/list]', '<ol><li>1</li><li>2</li></ol>',
                                        '<ol style="list-style-type:decimal;"><li>1</li><li>2</li></ol>'],
            ['[quote="post author"]quote[/quote]', '<blockquote><em>post author</em><br>quote</blockquote>'],
            ['[code]code[/code]', '<div class="code"><pre>code</pre></div>',
                                  '<pre><code>code</code></pre>'],
        ]

        for item in bbcode_to_html_map:
            self.assertIn(defaults.PYBB_MARKUP_ENGINES['bbcode'](item[0]), item[1:])

    def test_bbcode_and_course_title(self):
        response = self.client.get(self.course.get_absolute_url())
        tree = html.fromstring(response.content)
        self.assertTrue(self.course.name in tree.xpath('//title')[0].text_content())
        self.assertContains(response, self.post.body_html)
        self.assertContains(response, 'bbcode <strong>test</strong>')

    def test_course_addition(self):
        self.login_client()
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        response = self.client.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'new course test'
        values['name'] = 'new course name'
        values['poll_type'] = 0
        response = self.client.post(add_course_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Course.objects.filter(name='new course name').exists())

    def test_post_deletion(self):
        post = Post(course=self.course, user=self.user, body='bbcode [b]test[/b]')
        post.save()
        post.delete()
        Course.objects.get(id=self.course.id)
        Notice.objects.get(id=self.notice.id)

    def test_course_deletion(self):
        course = Course(name='xcourse', notice=self.notice, user=self.user)
        course.save()
        post = Post(course=course, user=self.user, body='one')
        post.save()
        post = Post(course=course, user=self.user, body='two')
        post.save()
        post.delete()
        Course.objects.get(id=course.id)
        Notice.objects.get(id=self.notice.id)
        course.delete()
        Notice.objects.get(id=self.notice.id)

    def test_notice_updated(self):
        time.sleep(1)
        course = Course(name='xcourse', notice=self.notice, user=self.user)
        course.save()
        post = Post(course=course, user=self.user, body='one')
        post.save()
        post = Post.objects.get(id=post.id)
        self.assertTrue(self.notice.updated == post.created)

    def test_read_tracking(self):
        course = Course(name='xcourse', notice=self.notice, user=self.user)
        course.save()
        post = Post(course=course, user=self.user, body='one')
        post.save()
        client = Client()
        client.login(username='zeus', password='zeus')
        # Course status
        tree = html.fromstring(client.get(course.notice.get_absolute_url()).content)
        self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.get_absolute_url()))
        # Notice status
        tree = html.fromstring(client.get(reverse('noticeapp:index')).content)
        self.assertTrue(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.notice.get_absolute_url()))
        # Visit it
        client.get(course.get_absolute_url())
        # Course status - readed
        tree = html.fromstring(client.get(course.notice.get_absolute_url()).content)
        # Visit others
        for t in course.notice.courses.all():
            client.get(t.get_absolute_url())
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.get_absolute_url()))
        # Notice status - readed
        tree = html.fromstring(client.get(reverse('noticeapp:index')).content)
        self.assertFalse(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.notice.get_absolute_url()))
        # Post message
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': course.id})
        response = client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test tracking'
        response = client.post(add_post_url, values, follow=True)
        self.assertContains(response, 'test tracking')
        # Course status - readed
        tree = html.fromstring(client.get(course.notice.get_absolute_url()).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.get_absolute_url()))
        # Notice status - readed
        tree = html.fromstring(client.get(reverse('noticeapp:index')).content)
        self.assertFalse(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.notice.get_absolute_url()))
        post = Post(course=course, user=self.user, body='one')
        post.save()
        client.get(reverse('noticeapp:mark_all_as_read'))
        tree = html.fromstring(client.get(reverse('noticeapp:index')).content)
        self.assertFalse(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % course.notice.get_absolute_url()))
        # Empty notice - readed
        f = Notice(name='empty', category=self.category)
        f.save()
        tree = html.fromstring(client.get(reverse('noticeapp:index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % f.get_absolute_url()))

    def test_read_tracking_multi_user(self):
        course_1 = self.course
        course_2 = Course(name='course_2', notice=self.notice, user=self.user)
        course_2.save()

        Post(course=course_2, user=self.user, body='one').save()

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        user_bob = User.objects.create_user('bob', 'bob@localhost', 'bob')
        client_bob = Client()
        client_bob.login(username='bob', password='bob')

        # Two courses, each with one post. everything is unread, so the db should reflect that:
        self.assertEqual(CourseReadTracker.objects.all().count(), 0)
        self.assertEqual(NoticeReadTracker.objects.all().count(), 0)

        # user_ann reads course_1, she should get one course read tracker, there should be no notice read trackers
        time.sleep(1)
        client_ann.get(course_1.get_absolute_url())
        self.assertEqual(CourseReadTracker.objects.all().count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_ann).count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_ann, course=course_1).count(), 1)
        self.assertEqual(NoticeReadTracker.objects.all().count(), 0)

        # user_bob reads course_1, he should get one course read tracker, there should be no notice read trackers
        time.sleep(1)
        client_bob.get(course_1.get_absolute_url())
        self.assertEqual(CourseReadTracker.objects.all().count(), 2)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_bob, course=course_1).count(), 1)

        # user_bob reads course_2, he should get a notice read tracker,
        #  there should be no course read trackers for user_bob
        time.sleep(1)
        client_bob.get(course_2.get_absolute_url())
        self.assertEqual(CourseReadTracker.objects.all().count(), 1)
        self.assertEqual(NoticeReadTracker.objects.all().count(), 1)
        self.assertEqual(NoticeReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(NoticeReadTracker.objects.filter(user=user_bob, notice=self.notice).count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_bob).count(), 0)
        self.assertListEqual([t.unread for t in noticeapp_course_unread([course_1, course_2], user_bob)], [False, False])

        # user_ann creates course_3, they should get a new course read tracker in the db
        time.sleep(1)
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        response = client_ann.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'course_3'
        values['name'] = 'course_3'
        values['poll_type'] = 0
        response = client_ann.post(add_course_url, data=values, follow=True)
        self.assertEqual(CourseReadTracker.objects.all().count(), 2)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(NoticeReadTracker.objects.all().count(), 1)
        course_3 = Course.objects.order_by('-updated', '-id')[0]
        self.assertEqual(course_3.name, 'course_3')

        # user_ann posts to course_1, a course they've already read, no new trackers should be created
        time.sleep(1)
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': course_1.id})
        response = client_ann.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test tracking'
        response = client_ann.post(add_post_url, values, follow=True)
        self.assertEqual(CourseReadTracker.objects.all().count(), 2)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(NoticeReadTracker.objects.all().count(), 1)

        # user_bob has two unread courses, 'course_1' and 'course_3'.
        #   This is because user_ann created a new course and posted to an existing course,
        #   after user_bob got his notice read tracker.

        # user_bob reads 'course_1'
        #   user_bob gets a new course read tracker, and the existing notice read tracker stays the same.
        #   'course_3' appears unread for user_bob
        #
        previous_time = NoticeReadTracker.objects.all()[0].time_stamp
        time.sleep(1)
        client_bob.get(course_1.get_absolute_url())
        self.assertEqual(NoticeReadTracker.objects.all().count(), 1)
        self.assertEqual(NoticeReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(CourseReadTracker.objects.all().count(), 3)

        # user_bob reads the last unread course, 'course_3'.
        # user_bob's existing notice read tracker updates and his course read tracker disappears
        #
        previous_time = NoticeReadTracker.objects.all()[0].time_stamp
        time.sleep(1)
        client_bob.get(course_3.get_absolute_url())
        self.assertEqual(NoticeReadTracker.objects.all().count(), 1)
        self.assertGreater(NoticeReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(CourseReadTracker.objects.all().count(), 2)
        self.assertEqual(CourseReadTracker.objects.filter(user=user_bob).count(), 0)

    def test_read_tracking_multi_notice(self):
        course_1 = self.course
        course_2 = Course(name='course_2', notice=self.notice, user=self.user)
        course_2.save()

        Post(course=course_2, user=self.user, body='one').save()

        notice_1 = self.notice
        notice_2 = Notice(name='notice_2', description='bar', category=self.category)
        notice_2.save()

        Course(name='garbage', notice=notice_2, user=self.user).save()

        client = Client()
        client.login(username='zeus', password='zeus')

        # everything starts unread
        self.assertEqual(NoticeReadTracker.objects.all().count(), 0)
        self.assertEqual(CourseReadTracker.objects.all().count(), 0)

        # user reads course_1, they should get one course read tracker, there should be no notice read trackers
        client.get(course_1.get_absolute_url())
        self.assertEqual(CourseReadTracker.objects.all().count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=self.user).count(), 1)
        self.assertEqual(CourseReadTracker.objects.filter(user=self.user, course=course_1).count(), 1)

        # user reads course_2, they should get a notice read tracker,
        #  there should be no course read trackers for the user
        client.get(course_2.get_absolute_url())
        self.assertEqual(CourseReadTracker.objects.all().count(), 0)
        self.assertEqual(NoticeReadTracker.objects.all().count(), 1)
        self.assertEqual(NoticeReadTracker.objects.filter(user=self.user).count(), 1)
        self.assertEqual(NoticeReadTracker.objects.filter(user=self.user, notice=self.notice).count(), 1)

    def test_read_tracker_after_posting(self):
        client = Client()
        client.login(username='zeus', password='zeus')
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        response = client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test tracking'
        response = client.post(add_post_url, values, follow=True)

        # after posting in course it should be readed
        # because there is only one course, so whole notice should be marked as readed
        self.assertEqual(CourseReadTracker.objects.filter(user=self.user, course=self.course).count(), 0)
        self.assertEqual(NoticeReadTracker.objects.filter(user=self.user, notice=self.notice).count(), 1)

    def test_noticeapp_is_course_unread_filter(self):
        notice_1 = self.notice
        course_1 = self.course
        course_2 = Course.objects.create(name='course_2', notice=notice_1, user=self.user)

        notice_2 = Notice.objects.create(name='notice_2', description='notice2', category=self.category)
        course_3 = Course.objects.create(name='course_2', notice=notice_2, user=self.user)

        Post(course=course_1, user=self.user, body='one').save()
        Post(course=course_2, user=self.user, body='two').save()
        Post(course=course_3, user=self.user, body='three').save()

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        # Two courses, each with one post. everything is unread, so the db should reflect that:
        self.assertTrue(noticeapp_is_course_unread(course_1, user_ann))
        self.assertTrue(noticeapp_is_course_unread(course_2, user_ann))
        self.assertTrue(noticeapp_is_course_unread(course_3, user_ann))
        self.assertListEqual(
            [t.unread for t in noticeapp_course_unread([course_1, course_2, course_3], user_ann)],
            [True, True, True])

        client_ann.get(course_1.get_absolute_url())
        course_1 = Course.objects.get(id=course_1.id)
        course_2 = Course.objects.get(id=course_2.id)
        course_3 = Course.objects.get(id=course_3.id)
        self.assertFalse(noticeapp_is_course_unread(course_1, user_ann))
        self.assertTrue(noticeapp_is_course_unread(course_2, user_ann))
        self.assertTrue(noticeapp_is_course_unread(course_3, user_ann))
        self.assertListEqual(
            [t.unread for t in noticeapp_course_unread([course_1, course_2, course_3], user_ann)],
            [False, True, True])

        client_ann.get(course_2.get_absolute_url())
        course_1 = Course.objects.get(id=course_1.id)
        course_2 = Course.objects.get(id=course_2.id)
        course_3 = Course.objects.get(id=course_3.id)
        self.assertFalse(noticeapp_is_course_unread(course_1, user_ann))
        self.assertFalse(noticeapp_is_course_unread(course_2, user_ann))
        self.assertTrue(noticeapp_is_course_unread(course_3, user_ann))
        self.assertListEqual(
            [t.unread for t in noticeapp_course_unread([course_1, course_2, course_3], user_ann)],
            [False, False, True])

        client_ann.get(course_3.get_absolute_url())
        course_1 = Course.objects.get(id=course_1.id)
        course_2 = Course.objects.get(id=course_2.id)
        course_3 = Course.objects.get(id=course_3.id)
        self.assertFalse(noticeapp_is_course_unread(course_1, user_ann))
        self.assertFalse(noticeapp_is_course_unread(course_2, user_ann))
        self.assertFalse(noticeapp_is_course_unread(course_3, user_ann))
        self.assertListEqual(
            [t.unread for t in noticeapp_course_unread([course_1, course_2, course_3], user_ann)],
            [False, False, False])

    def test_is_notice_unread_filter(self):
        Notice.objects.all().delete()

        notice_parent = Notice.objects.create(name='f1', category=self.category)
        notice_child1 = Notice.objects.create(name='f2', category=self.category, parent=notice_parent)
        notice_child2 = Notice.objects.create(name='f3', category=self.category, parent=notice_parent)
        course_1 = Course.objects.create(name='course_1', notice=notice_parent, user=self.user)
        course_2 = Course.objects.create(name='course_2', notice=notice_child1, user=self.user)
        course_3 = Course.objects.create(name='course_3', notice=notice_child2, user=self.user)

        Post(course=course_1, user=self.user, body='one').save()
        Post(course=course_2, user=self.user, body='two').save()
        Post(course=course_3, user=self.user, body='three').save()

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        notice_parent = Notice.objects.get(id=notice_parent.id)
        notice_child1 = Notice.objects.get(id=notice_child1.id)
        notice_child2 = Notice.objects.get(id=notice_child2.id)
        self.assertListEqual([f.unread for f in noticeapp_notice_unread([notice_parent, notice_child1, notice_child2], user_ann)],
                             [True, True, True])

        # unless we read parent course, there is unreaded courses in child notices
        client_ann.get(course_1.get_absolute_url())
        notice_parent = Notice.objects.get(id=notice_parent.id)
        notice_child1 = Notice.objects.get(id=notice_child1.id)
        notice_child2 = Notice.objects.get(id=notice_child2.id)
        self.assertListEqual([f.unread for f in noticeapp_notice_unread([notice_parent, notice_child1, notice_child2], user_ann)],
                             [True, True, True])

        # still unreaded course in one of the child notices
        client_ann.get(course_2.get_absolute_url())
        notice_parent = Notice.objects.get(id=notice_parent.id)
        notice_child1 = Notice.objects.get(id=notice_child1.id)
        notice_child2 = Notice.objects.get(id=notice_child2.id)
        self.assertListEqual([f.unread for f in noticeapp_notice_unread([notice_parent, notice_child1, notice_child2], user_ann)],
                             [True, False, True])

        # all courses readed
        client_ann.get(course_3.get_absolute_url())
        notice_parent = Notice.objects.get(id=notice_parent.id)
        notice_child1 = Notice.objects.get(id=notice_child1.id)
        notice_child2 = Notice.objects.get(id=notice_child2.id)
        self.assertListEqual([f.unread for f in noticeapp_notice_unread([notice_parent, notice_child1, notice_child2], user_ann)],
                             [False, False, False])

    def test_read_tracker_when_courses_notice_changed(self):
        notice_1 = Notice.objects.create(name='f1', description='bar', category=self.category)
        notice_2 = Notice.objects.create(name='f2', description='bar', category=self.category)
        course_1 = Course.objects.create(name='t1', notice=notice_1, user=self.user)
        course_2 = Course.objects.create(name='t2', notice=notice_2, user=self.user)

        Post.objects.create(course=course_1, user=self.user, body='one')
        Post.objects.create(course=course_2, user=self.user, body='two')

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        # Everything is unread
        self.assertListEqual([t.unread for t in noticeapp_course_unread([course_1, course_2], user_ann)], [True, True])
        self.assertListEqual([t.unread for t in noticeapp_notice_unread([notice_1, notice_2], user_ann)], [True, True])

        # read all
        client_ann.get(reverse('noticeapp:mark_all_as_read'))
        self.assertListEqual([t.unread for t in noticeapp_course_unread([course_1, course_2], user_ann)], [False, False])
        self.assertListEqual([t.unread for t in noticeapp_notice_unread([notice_1, notice_2], user_ann)], [False, False])

        time.sleep(1)
        post = Post.objects.create(course=course_1, user=self.user, body='three')
        post = Post.objects.get(id=post.id)  # get post with timestamp from DB

        course_1 = Course.objects.get(id=course_1.id)
        course_2 = Course.objects.get(id=course_2.id)
        self.assertEqual(course_1.updated, post.updated or post.created)
        self.assertEqual(notice_1.updated, post.updated or post.created)
        self.assertListEqual([t.unread for t in noticeapp_course_unread([course_1, course_2], user_ann)], [True, False])
        self.assertListEqual([t.unread for t in noticeapp_notice_unread([notice_1, notice_2], user_ann)], [True, False])

        time.sleep(1)
        post.course = course_2
        post.save()
        course_1 = Course.objects.get(id=course_1.id)
        course_2 = Course.objects.get(id=course_2.id)
        notice_1 = Notice.objects.get(id=notice_1.id)
        notice_2 = Notice.objects.get(id=notice_2.id)
        self.assertEqual(course_2.updated, post.updated or post.created)
        self.assertEqual(notice_2.updated, post.updated or post.created)
        self.assertListEqual([t.unread for t in noticeapp_course_unread([course_1, course_2], user_ann)], [False, True])
        self.assertListEqual([t.unread for t in noticeapp_notice_unread([notice_1, notice_2], user_ann)], [False, True])

        time.sleep(1)
        course_2.notice = notice_1
        course_2.save()
        course_1 = Course.objects.get(id=course_1.id)
        course_2 = Course.objects.get(id=course_2.id)
        notice_1 = Notice.objects.get(id=notice_1.id)
        notice_2 = Notice.objects.get(id=notice_2.id)
        self.assertEqual(notice_1.updated, post.updated or post.created)
        self.assertListEqual([t.unread for t in noticeapp_course_unread([course_1, course_2], user_ann)], [False, True])
        self.assertListEqual([t.unread for t in noticeapp_notice_unread([notice_1, notice_2], user_ann)], [True, False])

    def test_open_first_unread_post(self):
        notice_1 = self.notice
        course_1 = Course.objects.create(name='course_1', notice=notice_1, user=self.user)
        course_2 = Course.objects.create(name='course_2', notice=notice_1, user=self.user)

        post_1_1 = Post.objects.create(course=course_1, user=self.user, body='1_1')
        post_1_2 = Post.objects.create(course=course_1, user=self.user, body='1_2')
        post_2_1 = Post.objects.create(course=course_2, user=self.user, body='2_1')

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        response = client_ann.get(course_1.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (course_1.get_absolute_url(), 1, post_1_1.id))

        response = client_ann.get(course_1.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (course_1.get_absolute_url(), 1, post_1_2.id))

        response = client_ann.get(course_2.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (course_2.get_absolute_url(), 1, post_2_1.id))

        time.sleep(1)
        post_1_3 = Post.objects.create(course=course_1, user=self.user, body='1_3')
        post_1_4 = Post.objects.create(course=course_1, user=self.user, body='1_4')

        response = client_ann.get(course_1.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (course_1.get_absolute_url(), 1, post_1_3.id))

    def test_latest_courses(self):
        course_1 = self.course
        course_1.updated = timezone.now()
        course_1.save()
        course_2 = Course.objects.create(name='course_2', notice=self.notice, user=self.user)
        course_2.updated = timezone.now() + datetime.timedelta(days=-1)
        course_2.save()

        category_2 = Category.objects.create(name='cat2')
        notice_2 = Notice.objects.create(name='notice_2', category=category_2)
        course_3 = Course.objects.create(name='course_3', notice=notice_2, user=self.user)
        course_3.updated = timezone.now() + datetime.timedelta(days=-2)
        course_3.save()

        self.login_client()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.context['course_list']), [course_1, course_2, course_3])

        course_2.notice.hidden = True
        course_2.notice.save()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_3])

        course_2.notice.hidden = False
        course_2.notice.save()
        category_2.hidden = True
        category_2.save()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_1, course_2])

        course_2.notice.hidden = False
        course_2.notice.save()
        category_2.hidden = False
        category_2.save()
        course_1.on_moderation = True
        course_1.save()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_1, course_2, course_3])

        course_1.user = User.objects.create_user('another', 'another@localhost', 'another')
        course_1.save()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_2, course_3])

        course_1.notice.moderators.add(self.user)
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_1, course_2, course_3])

        course_1.notice.moderators.remove(self.user)
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_1, course_2, course_3])

        self.client.logout()
        response = self.client.get(reverse('noticeapp:course_latest'))
        self.assertListEqual(list(response.context['course_list']), [course_2, course_3])

    def test_hidden(self):
        client = Client()
        category = Category(name='hcat', hidden=True)
        category.save()
        notice_in_hidden = Notice(name='in_hidden', category=category)
        notice_in_hidden.save()
        course_in_hidden = Course(notice=notice_in_hidden, name='in_hidden', user=self.user)
        course_in_hidden.save()

        notice_hidden = Notice(name='hidden', category=self.category, hidden=True)
        notice_hidden.save()
        course_hidden = Course(notice=notice_hidden, name='hidden', user=self.user)
        course_hidden.save()

        post_hidden = Post(course=course_hidden, user=self.user, body='hidden')
        post_hidden.save()

        post_in_hidden = Post(course=course_in_hidden, user=self.user, body='hidden')
        post_in_hidden.save()

        self.assertFalse(category.id in [c.id for c in client.get(reverse('noticeapp:index')).context['categories']])
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(notice_in_hidden.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(course_in_hidden.get_absolute_url()).status_code, 302)

        self.assertNotContains(client.get(reverse('noticeapp:index')), notice_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('noticeapp:feed_courses')), course_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('noticeapp:feed_courses')), course_in_hidden.get_absolute_url())

        self.assertNotContains(client.get(reverse('noticeapp:feed_posts')), post_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('noticeapp:feed_posts')), post_in_hidden.get_absolute_url())
        self.assertEqual(client.get(notice_hidden.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(course_hidden.get_absolute_url()).status_code, 302)

        client.login(username='zeus', password='zeus')
        self.assertFalse(category.id in [c.id for c in client.get(reverse('noticeapp:index')).context['categories']])
        self.assertNotContains(client.get(reverse('noticeapp:index')), notice_hidden.get_absolute_url())
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(notice_in_hidden.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(course_in_hidden.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(notice_hidden.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(course_hidden.get_absolute_url()).status_code, 403)
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(category.id in [c.id for c in client.get(reverse('noticeapp:index')).context['categories']])
        self.assertContains(client.get(reverse('noticeapp:index')), notice_hidden.get_absolute_url())
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(notice_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(course_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(notice_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(course_hidden.get_absolute_url()).status_code, 200)

    def test_inactive(self):
        self.login_client()
        url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        values = self.get_form_values(response)
        values['body'] = 'test ban'
        response = self.client.post(url, values, follow=True)
        self.assertEqual(len(Post.objects.filter(body='test ban')), 1)
        self.user.is_active = False
        self.user.save()
        values['body'] = 'test ban 2'
        self.client.post(url, values, follow=True)
        self.assertEqual(len(Post.objects.filter(body='test ban 2')), 0)

    def get_csrf(self, form):
        return form.xpath('//input[@name="csrfmiddlewaretoken"]/@value')[0]

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username='zeus', password='zeus')
        post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        response = client.get(post_url)
        values = self.get_form_values(response)
        del values['csrfmiddlewaretoken']
        response = client.post(post_url, values, follow=True)
        self.assertNotEqual(response.status_code, 200)
        response = client.get(self.course.get_absolute_url())
        values = self.get_form_values(response)
        response = client.post(reverse('noticeapp:add_post', kwargs={'course_id': self.course.id}), values, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_user_blocking(self):
        user = User.objects.create_user('test', 'test@localhost', 'test')
        course = Course.objects.create(name='course', notice=self.notice, user=user)
        p1 = Post.objects.create(course=course, user=user, body='bbcode [b]test[/b]')
        p2 = Post.objects.create(course=course, user=user, body='bbcode [b]test[/b]')
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.get(reverse('noticeapp:block_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('noticeapp:block_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.is_active)
        self.assertEqual(Course.objects.filter().count(), 2)
        self.assertEqual(Post.objects.filter(user=user).count(), 2)

        user.is_active = True
        user.save()
        self.assertEqual(Course.objects.count(), 2)
        response = self.client.post(reverse('noticeapp:block_user', args=[user.username]),
                                    data={'block_and_delete_messages': 'block_and_delete_messages'}, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.is_active)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Post.objects.filter(user=user).count(), 0)

    def test_user_unblocking(self):
        user = User.objects.create_user('test', 'test@localhost', 'test')
        user.is_active=False
        user.save()
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.get(reverse('noticeapp:unblock_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('noticeapp:unblock_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertTrue(user.is_active)

    def test_ajax_preview(self):
        self.login_client()
        response = self.client.post(reverse('noticeapp:post_ajax_preview'), data={'data': '[b]test bbcode ajax preview[/b]'})
        self.assertContains(response, '<strong>test bbcode ajax preview</strong>')

    def test_headline(self):
        self.notice.headline = 'test <b>headline</b>'
        self.notice.save()
        client = Client()
        self.assertContains(client.get(self.notice.get_absolute_url()), 'test <b>headline</b>')

    def test_quote(self):
        self.login_client()
        response = self.client.get(reverse('noticeapp:add_post', kwargs={'course_id': self.course.id}),
                                   data={'quote_id': self.post.id, 'body': 'test tracking'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.body)

    def test_edit_post(self):
        self.login_client()
        edit_post_url = reverse('noticeapp:edit_post', kwargs={'pk': self.post.id})
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Post.objects.get(id=self.post.id).updated)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(pk=self.post.id).body, 'test edit')
        response = self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test edit')
        self.assertIsNotNone(Post.objects.get(id=self.post.id).updated)

        # Check admin form
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        values['login'] = 'new_login'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test edit')

    def test_admin_post_add(self):
        self.user.is_staff = True
        self.user.save()
        self.login_client()
        response = self.client.post(reverse('noticeapp:add_post', kwargs={'course_id': self.course.id}),
                                    data={'quote_id': self.post.id, 'body': 'test admin post', 'user': 'zeus'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test admin post')

    def test_stick(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        self.assertEqual(
            self.client.get(reverse('noticeapp:stick_course', kwargs={'pk': self.course.id}), follow=True).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('noticeapp:unstick_course', kwargs={'pk': self.course.id}), follow=True).status_code, 200)

    def test_delete_view(self):
        post = Post(course=self.course, user=self.user, body='test to delete')
        post.save()
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.post(reverse('noticeapp:delete_post', args=[post.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        # Check that course and notice exists ;)
        self.assertEqual(Course.objects.filter(id=self.course.id).count(), 1)
        self.assertEqual(Notice.objects.filter(id=self.notice.id).count(), 1)

        # Delete course
        response = self.client.post(reverse('noticeapp:delete_post', args=[self.post.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.filter(id=self.post.id).count(), 0)
        self.assertEqual(Course.objects.filter(id=self.course.id).count(), 0)
        self.assertEqual(Notice.objects.filter(id=self.notice.id).count(), 1)

    def test_open_close(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        add_post_url = reverse('noticeapp:add_post', args=[self.course.id])
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test closed'
        response = self.client.get(reverse('noticeapp:close_course', args=[self.course.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('noticeapp:open_course', args=[self.course.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_subscription(self):
        user2 = User.objects.create_user(username='user2', password='user2', email='user2@someserver.com')
        user3 = User.objects.create_user(username='user3', password='user3', email='user3@example.com')
        client = Client()
        client.login(username='user2', password='user2')
        response = client.get(reverse('noticeapp:add_subscription', args=[self.course.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(user2, self.course.subscribers.all())

        self.course.subscribers.add(user3)

        # create a new reply (with another user)
        self.client.login(username='zeus', password='zeus')
        add_post_url = reverse('noticeapp:add_post', args=[self.course.id])
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test subscribtion юникод'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.order_by('-id')[0]

        # there should only be one email in the outbox (to user2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], user2.email)
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])

        # unsubscribe
        client.login(username='user2', password='user2')
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])
        response = client.get(reverse('noticeapp:delete_subscription', args=[self.course.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(user2, self.course.subscribers.all())

    def test_course_updated(self):
        course = Course(name='ecourse', notice=self.notice, user=self.user)
        course.save()
        time.sleep(1)
        post = Post(course=course, user=self.user, body='bbcode [b]test[/b]')
        post.save()
        client = Client()
        response = client.get(self.notice.get_absolute_url())
        self.assertEqual(response.context['course_list'][0], course)
        time.sleep(1)
        post = Post(course=self.course, user=self.user, body='bbcode [b]test[/b]')
        post.save()
        client = Client()
        response = client.get(self.notice.get_absolute_url())
        self.assertEqual(response.context['course_list'][0], self.course)

    def test_course_deleted(self):
        notice_1 = Notice.objects.create(name='new notice', category=self.category)
        course_1 = Course.objects.create(name='new course', notice=notice_1, user=self.user)
        post_1 = Post.objects.create(course=course_1, user=self.user, body='test')
        post_1 = Post.objects.get(id=post_1.id)

        self.assertEqual(course_1.updated, post_1.created)
        self.assertEqual(notice_1.updated, post_1.created)

        course_2 = Course.objects.create(name='another course', notice=notice_1, user=self.user)
        post_2 = Post.objects.create(course=course_2, user=self.user, body='another test')
        post_2 = Post.objects.get(id=post_2.id)

        self.assertEqual(course_2.updated, post_2.created)
        self.assertEqual(notice_1.updated, post_2.created)

        course_2.delete()
        notice_1 = Notice.objects.get(id=notice_1.id)
        self.assertEqual(notice_1.updated, post_1.created)
        self.assertEqual(notice_1.course_count, 1)
        self.assertEqual(notice_1.post_count, 1)

        post_1.delete()
        notice_1 = Notice.objects.get(id=notice_1.id)
        self.assertEqual(notice_1.course_count, 0)
        self.assertEqual(notice_1.post_count, 0)

    def test_user_views(self):
        response = self.client.get(reverse('noticeapp:user', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('noticeapp:user_posts', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 1)

        response = self.client.get(reverse('noticeapp:user_notices'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 1)

        self.course.notice.hidden = True
        self.course.notice.save()

        self.client.logout()

        response = self.client.get(reverse('noticeapp:user_posts', kwargs={'username': self.user.username}))
        self.assertEqual(response.context['object_list'].count(), 0)

        response = self.client.get(reverse('noticeapp:user_notices'))
        self.assertEqual(response.context['object_list'].count(), 0)

    def test_post_count(self):
        course = Course(name='ecourse', notice=self.notice, user=self.user)
        course.save()
        post = Post(course=course, user=self.user, body='test') # another post
        post.save()
        self.assertEqual(util.get_noticeapp_profile(self.user).post_count, 2)
        post.body = 'test2'
        post.save()
        self.assertEqual(Profile.objects.get(pk=util.get_noticeapp_profile(self.user).pk).post_count, 2)
        post.delete()
        self.assertEqual(Profile.objects.get(pk=util.get_noticeapp_profile(self.user).pk).post_count, 1)

    def test_latest_courses_tag(self):
        Course.objects.all().delete()
        for i in range(10):
            Course.objects.create(name='course%s' % i, user=self.user, notice=self.notice)
        latest_courses = noticeapp_get_latest_courses(context=None, user=self.user)
        self.assertEqual(len(latest_courses), 5)
        self.assertEqual(latest_courses[0].name, 'course9')
        self.assertEqual(latest_courses[4].name, 'course5')

    def test_latest_posts_tag(self):
        Post.objects.all().delete()
        for i in range(10):
            Post.objects.create(body='post%s' % i, user=self.user, course=self.course)
        latest_courses = noticeapp_get_latest_posts(context=None, user=self.user)
        self.assertEqual(len(latest_courses), 5)
        self.assertEqual(latest_courses[0].body, 'post9')
        self.assertEqual(latest_courses[4].body, 'post5')

    def test_multiple_objects_returned(self):
        """
        see issue #87: https://github.com/hovel/noticeappm/issues/87
        """
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.course.on_moderation)
        self.assertEqual(self.course.user, self.user)
        user1 = User.objects.create_user('geyser', 'geyser@localhost', 'geyser')
        self.course.notice.moderators.add(self.user)
        self.course.notice.moderators.add(user1)

        self.login_client()
        response = self.client.get(reverse('noticeapp:add_post', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION


class AnonymousTest(TestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_ANONYMOUS_USERNAME = defaults.PYBB_ANONYMOUS_USERNAME
        self.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER

        defaults.PYBB_ENABLE_ANONYMOUS_POST = True
        defaults.PYBB_ANONYMOUS_USERNAME = 'Anonymous'
        self.user = User.objects.create_user('Anonymous', 'Anonymous@localhost', 'Anonymous')
        self.category = Category.objects.create(name='foo')
        self.notice = Notice.objects.create(name='xfoo', description='bar', category=self.category)
        self.course = Course.objects.create(name='ecourse', notice=self.notice, user=self.user)
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'noticeapp', 'post')
        self.user.user_permissions.add(add_post_permission)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_ANONYMOUS_USERNAME = self.ORIG_PYBB_ANONYMOUS_USERNAME
        defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = self.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER

    def test_anonymous_posting(self):
        post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        response = self.client.get(post_url)
        values = self.get_form_values(response)
        values['body'] = 'test anonymous'
        response = self.client.post(post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Post.objects.filter(body='test anonymous')), 1)
        self.assertEqual(Post.objects.get(body='test anonymous').user, self.user)

    def test_anonymous_cache_course_views(self):
        self.assertNotIn(util.build_cache_key('anonymous_course_views', course_id=self.course.id), cache)
        url = self.course.get_absolute_url()
        self.client.get(url)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_course_views', course_id=self.course.id)), 1)
        for _ in range(defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER - 2):
            self.client.get(url)
        self.assertEqual(Course.objects.get(id=self.course.id).views, 0)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_course_views', course_id=self.course.id)),
                         defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER - 1)
        self.client.get(url)
        self.assertEqual(Course.objects.get(id=self.course.id).views, defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_course_views', course_id=self.course.id)), 0)

        views = Course.objects.get(id=self.course.id).views

        defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = None
        self.client.get(url)
        self.assertEqual(Course.objects.get(id=self.course.id).views, views + 1)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_course_views', course_id=self.course.id)), 0)


def premoderate_test(user, post):
    """
    Test premoderate function
    Allow post without moderation for staff users only
    """
    if user.username.startswith('allowed'):
        return True
    return False


class PreModerationTest(TestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = premoderate_test
        self.create_user()
        self.create_initial()
        mail.outbox = []

    def test_premoderation(self):
        self.client.login(username='zeus', password='zeus')
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation')
        self.assertEqual(post.on_moderation, True)

        # Post is visible by author
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # Post is not visible by anonymous user
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertRedirects(response, settings.LOGIN_URL + '?next=%s' % post.get_absolute_url())
        response = client.get(self.course.get_absolute_url(), follow=True)
        self.assertNotContains(response, 'test premoderation')

        # But visible by superuser (with permissions)
        user = User.objects.create_user('admin', 'admin@localhost', 'admin')
        user.is_superuser = True
        user.save()
        client.login(username='admin', password='admin')
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # user with names stats with allowed can post without premoderation
        user = User.objects.create_user('allowed_zeus', 'allowed_zeus@localhost', 'allowed_zeus')
        client.login(username='allowed_zeus', password='allowed_zeus')
        response = client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation staff'
        response = client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation staff')
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test premoderation staff')

        # Superuser can moderate
        user.is_superuser = True
        user.save()
        admin_client = Client()
        admin_client.login(username='admin', password='admin')
        post = Post.objects.get(body='test premoderation')
        response = admin_client.get(reverse('noticeapp:moderate_post', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 200)

        # Now all can see this post:
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # Other users can't moderate
        post.on_moderation = True
        post.save()
        client.login(username='zeus', password='zeus')
        response = client.get(reverse('noticeapp:moderate_post', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 403)

        # If user create new course it goes to moderation if MODERATION_ENABLE
        # When first post is moderated, course becomes moderated too
        self.client.login(username='zeus', password='zeus')
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        response = self.client.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'new course test'
        values['name'] = 'new course name'
        values['poll_type'] = 0
        response = self.client.post(add_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new course test')

        client = Client()
        response = client.get(self.notice.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'new course name')
        response = client.get(Course.objects.get(name='new course name').get_absolute_url())
        self.assertEqual(response.status_code, 302)
        response = admin_client.get(reverse('noticeapp:moderate_post',
                                            kwargs={'pk': Post.objects.get(body='new course test').id}),
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        response = client.get(self.notice.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new course name')
        response = client.get(Course.objects.get(name='new course name').get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION


class AttachmentTest(TestCase, SharedTestModule):
    def setUp(self):
        self.PYBB_ATTACHMENT_ENABLE = defaults.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_ATTACHMENT_ENABLE = True
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = False
        self.file_name = os.path.join(os.path.dirname(__file__), 'static', 'noticeapp', 'img', 'attachment.png')
        self.create_user()
        self.create_initial()

    def test_attachment_one(self):
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        self.login_client()
        response = self.client.get(add_post_url)
        with open(self.file_name, 'rb') as fp:
            values = self.get_form_values(response)
            values['body'] = 'test attachment'
            values['attachments-0-file'] = fp
            response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(body='test attachment').exists())

    def test_attachment_two(self):
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        self.login_client()
        response = self.client.get(add_post_url)
        with open(self.file_name, 'rb') as fp:
            values = self.get_form_values(response)
            values['body'] = 'test attachment'
            values['attachments-0-file'] = fp
            del values['attachments-INITIAL_FORMS']
            del values['attachments-TOTAL_FORMS']
            with self.assertRaises(ValidationError):
                self.client.post(add_post_url, values, follow=True)

    def tearDown(self):
        defaults.PYBB_ATTACHMENT_ENABLE = self.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION


class PollTest(TestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()
        self.PYBB_POLL_MAX_ANSWERS = defaults.PYBB_POLL_MAX_ANSWERS
        defaults.PYBB_POLL_MAX_ANSWERS = 2

    def test_poll_add(self):
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        self.login_client()
        response = self.client.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 0 # poll_type = None, create course without poll answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1'
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_course = Course.objects.get(name='test poll name')
        self.assertIsNone(new_course.poll_question)
        self.assertFalse(PollAnswer.objects.filter(course=new_course).exists()) # no answers here

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['poll_answers-0-text'] = 'answer1' # not enough answers
        values['poll_answers-TOTAL_FORMS'] = 1
        response = self.client.post(add_course_url, values, follow=True)
        self.assertFalse(Course.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['poll_answers-0-text'] = 'answer1' # too many answers
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-2-text'] = 'answer3'
        values['poll_answers-TOTAL_FORMS'] = 3
        response = self.client.post(add_course_url, values, follow=True)
        self.assertFalse(Course.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1 # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1' # two answers - what do we need to create poll
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_course = Course.objects.get(name='test poll name 1')
        self.assertEqual(new_course.poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(course=new_course).count(), 2)

    def test_regression_adding_poll_with_removed_answers(self):
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        self.login_client()
        response = self.client.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = ''
        values['poll_answers-0-DELETE'] = 'on'
        values['poll_answers-1-text'] = ''
        values['poll_answers-1-DELETE'] = 'on'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(name='test poll name').exists())

    def test_regression_poll_deletion_after_second_post(self):
        self.login_client()

        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        response = self.client.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1 # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1' # two answers - what do we need to create poll
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_course = Course.objects.get(name='test poll name')
        self.assertEqual(new_course.poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(course=new_course).count(), 2)

        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': new_course.id})
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test answer body'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(PollAnswer.objects.filter(course=new_course).count(), 2)

    def test_poll_edit(self):
        edit_course_url = reverse('noticeapp:edit_post', kwargs={'pk': self.post.id})
        self.login_client()
        response = self.client.get(edit_course_url)
        values = self.get_form_values(response)
        values['poll_type'] = 1 # add_poll
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1'
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(edit_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.get(id=self.course.id).poll_type, 1)
        self.assertEqual(Course.objects.get(id=self.course.id).poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(course=self.course).count(), 2)

        values = self.get_form_values(self.client.get(edit_course_url))
        values['poll_type'] = 2 # change_poll type
        values['poll_question'] = 'q100' # change poll question
        values['poll_answers-0-text'] = 'answer100' # change poll answers
        values['poll_answers-1-text'] = 'answer200'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(edit_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.get(id=self.course.id).poll_type, 2)
        self.assertEqual(Course.objects.get(id=self.course.id).poll_question, 'q100')
        self.assertEqual(PollAnswer.objects.filter(course=self.course).count(), 2)
        self.assertTrue(PollAnswer.objects.filter(text='answer100').exists())
        self.assertTrue(PollAnswer.objects.filter(text='answer200').exists())
        self.assertFalse(PollAnswer.objects.filter(text='answer1').exists())
        self.assertFalse(PollAnswer.objects.filter(text='answer2').exists())

        values['poll_type'] = 0 # remove poll
        values['poll_answers-0-text'] = 'answer100' # no matter how many answers we provide
        values['poll_answers-TOTAL_FORMS'] = 1
        response = self.client.post(edit_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.get(id=self.course.id).poll_type, 0)
        self.assertIsNone(Course.objects.get(id=self.course.id).poll_question)
        self.assertEqual(PollAnswer.objects.filter(course=self.course).count(), 0)

    def test_poll_voting(self):
        def recreate_poll(poll_type):
            self.course.poll_type = poll_type
            self.course.save()
            PollAnswer.objects.filter(course=self.course).delete()
            PollAnswer.objects.create(course=self.course, text='answer1')
            PollAnswer.objects.create(course=self.course, text='answer2')

        self.login_client()
        recreate_poll(poll_type=Course.POLL_TYPE_SINGLE)
        vote_url = reverse('noticeapp:course_poll_vote', kwargs={'pk': self.course.id})
        my_answer = PollAnswer.objects.all()[0]
        values = {'answers': my_answer.id}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.get(id=self.course.id).poll_votes(), 1)
        self.assertEqual(PollAnswer.objects.get(id=my_answer.id).votes(), 1)
        self.assertEqual(PollAnswer.objects.get(id=my_answer.id).votes_percent(), 100.0)

        # already voted
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 403) # bad request status

        recreate_poll(poll_type=Course.POLL_TYPE_MULTIPLE)
        values = {'answers': [a.id for a in PollAnswer.objects.all()]}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [1, 1])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [50.0, 50.0])

        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 403)  # already voted

        cancel_vote_url = reverse('noticeapp:course_cancel_poll_vote', kwargs={'pk': self.course.id})
        response = self.client.post(cancel_vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [0, 0])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [0, 0])

        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [1, 1])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [50.0, 50.0])

    def test_poll_voting_on_closed_course(self):
        self.login_client()
        self.course.poll_type = Course.POLL_TYPE_SINGLE
        self.course.save()
        PollAnswer.objects.create(course=self.course, text='answer1')
        PollAnswer.objects.create(course=self.course, text='answer2')
        self.course.closed = True
        self.course.save()

        vote_url = reverse('noticeapp:course_poll_vote', kwargs={'pk': self.course.id})
        my_answer = PollAnswer.objects.all()[0]
        values = {'answers': my_answer.id}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 403)

    def tearDown(self):
        defaults.PYBB_POLL_MAX_ANSWERS = self.PYBB_POLL_MAX_ANSWERS


class FiltersTest(TestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial(post=False)

    def test_filters(self):
        add_post_url = reverse('noticeapp:add_post', kwargs={'course_id': self.course.id})
        self.login_client()
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test\n \n \n\nmultiple empty lines\n'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.all()[0].body, 'test\nmultiple empty lines')


class CustomPermissionHandler(permissions.DefaultPermissionHandler):
    """
    a custom permission handler which changes the meaning of "hidden" notice:
    "hidden" notice or category is visible for all logged on users, not only staff
    """

    def filter_categories(self, user, qs):
        return qs.filter(hidden=False) if user.is_anonymous() else qs

    def may_view_category(self, user, category):
        return user.is_authenticated() if category.hidden else True

    def filter_notices(self, user, qs):
        if user.is_anonymous():
            qs = qs.filter(Q(hidden=False) & Q(category__hidden=False))
        return qs

    def may_view_notice(self, user, notice):
        return user.is_authenticated() if notice.hidden or notice.category.hidden else True

    def filter_courses(self, user, qs):
        if user.is_anonymous():
            qs = qs.filter(Q(notice__hidden=False) & Q(notice__category__hidden=False))
        qs = qs.filter(closed=False)  # filter out closed courses for test
        return qs

    def may_view_course(self, user, course):
        return self.may_view_notice(user, course.notice)

    def filter_posts(self, user, qs):
        if user.is_anonymous():
            qs = qs.filter(Q(course__notice__hidden=False) & Q(course__notice__category__hidden=False))
        return qs

    def may_view_post(self, user, post):
        return self.may_view_notice(user, post.course.notice)

    def may_create_poll(self, user):
        return False


def _attach_perms_class(class_name):
    """
    override the permission handler. this cannot be done with @override_settings as
    permissions.perms is already imported at import point, instead we got to monkeypatch
    the modules (not really nice, but only an issue in tests)
    """
    noticeapp_views.perms = permissions.perms = permissions._resolve_class(class_name)


def _detach_perms_class():
    """
    reset permission handler (otherwise other tests may fail)
    """
    noticeapp_views.perms = permissions.perms = permissions._resolve_class('noticeapp.permissions.DefaultPermissionHandler')


class CustomPermissionHandlerTest(TestCase, SharedTestModule):
    """ test custom permission handler """

    def setUp(self):
        self.create_user()
        # create public and hidden categories, notices, posts
        c_pub = Category(name='public')
        c_pub.save()
        c_hid = Category(name='private', hidden=True)
        c_hid.save()
        self.notice = Notice.objects.create(name='pub1', category=c_pub)
        Notice.objects.create(name='priv1', category=c_hid)
        Notice.objects.create(name='private_in_public_cat', hidden=True, category=c_pub)
        for f in Notice.objects.all():
            t = Course.objects.create(name='a course', notice=f, user=self.user)
            Post.objects.create(course=t, user=self.user, body='test')
        # make some courses closed => hidden
        for t in Course.objects.all()[0:2]:
            t.closed = True
            t.save()

        _attach_perms_class('noticeapp.tests.CustomPermissionHandler')

    def tearDown(self):
        _detach_perms_class()

    def test_category_permission(self):
        for c in Category.objects.all():
            # anon user may not see category
            r = self.get_with_user(c.get_absolute_url())
            if c.hidden:
                self.assertEqual(r.status_code, 302)
            else:
                self.assertEqual(r.status_code, 200)
                # logged on user may see all categories
            r = self.get_with_user(c.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 200)

    def test_notice_permission(self):
        for f in Notice.objects.all():
            r = self.get_with_user(f.get_absolute_url())
            self.assertEqual(r.status_code, 302 if f.hidden or f.category.hidden else 200)
            r = self.get_with_user(f.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.context['object_list'].count(), f.courses.filter(closed=False).count())

    def test_course_permission(self):
        for t in Course.objects.all():
            r = self.get_with_user(t.get_absolute_url())
            self.assertEqual(r.status_code, 302 if t.notice.hidden or t.notice.category.hidden else 200)
            r = self.get_with_user(t.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 200)

    def test_post_permission(self):
        for p in Post.objects.all():
            r = self.get_with_user(p.get_absolute_url())
            self.assertEqual(r.status_code, 302 if p.course.notice.hidden or p.course.notice.category.hidden else 301)
            r = self.get_with_user(p.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 301)

    def test_poll_add(self):
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        self.login_client()
        response = self.client.get(add_course_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1 # poll_type = 1, create course with poll
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1'
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_course_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_course = Course.objects.get(name='test poll name')
        self.assertIsNone(new_course.poll_question)
        self.assertFalse(PollAnswer.objects.filter(course=new_course).exists()) # no answers here


class RestrictEditingHandler(permissions.DefaultPermissionHandler):
        def may_create_course(self, user, notice):
            return False

        def may_create_post(self, user, course):
            return False

        def may_edit_post(self, user, post):
            return False


class LogonRedirectTest(TestCase, SharedTestModule):
    """ test whether anonymous user gets redirected, whereas unauthorized user gets PermissionDenied """

    def setUp(self):
        # create users
        staff = User.objects.create_user('staff', 'staff@localhost', 'staff')
        staff.is_staff = True
        staff.save()
        nostaff = User.objects.create_user('nostaff', 'nostaff@localhost', 'nostaff')
        nostaff.is_staff = False
        nostaff.save()

        # create course, post in hidden category
        self.category = Category(name='private', hidden=True)
        self.category.save()
        self.notice = Notice(name='priv1', category=self.category)
        self.notice.save()
        self.course = Course(name='a course', notice=self.notice, user=staff)
        self.course.save()
        self.post = Post(body='body post', course=self.course, user=staff, on_moderation=True)
        self.post.save()

    def test_redirect_category(self):
        # access without user should be redirected
        r = self.get_with_user(self.category.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.category.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.category.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.category.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_notice(self):
        # access without user should be redirected
        r = self.get_with_user(self.notice.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.notice.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.notice.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.notice.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_course(self):
        # access without user should be redirected
        r = self.get_with_user(self.course.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.course.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.course.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.course.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_post(self):
        # access without user should be redirected
        r = self.get_with_user(self.post.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.post.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.post.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.post.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 301)

    @override_settings(PYBB_ENABLE_ANONYMOUS_POST=False)
    def test_redirect_course_add(self):
        _attach_perms_class('noticeapp.tests.RestrictEditingHandler')

        # access without user should be redirected
        add_course_url = reverse('noticeapp:add_course', kwargs={'notice_id': self.notice.id})
        r = self.get_with_user(add_course_url)
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % add_course_url)

        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(add_course_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 403)

        _detach_perms_class()

        # allowed user is allowed
        r = self.get_with_user(add_course_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_post_edit(self):
        _attach_perms_class('noticeapp.tests.RestrictEditingHandler')

        # access without user should be redirected
        edit_post_url = reverse('noticeapp:edit_post', kwargs={'pk': self.post.id})
        r = self.get_with_user(edit_post_url)
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % edit_post_url)

        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(edit_post_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 403)

        _detach_perms_class()

        # allowed user is allowed
        r = self.get_with_user(edit_post_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

