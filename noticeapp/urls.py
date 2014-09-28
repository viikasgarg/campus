# -*- coding: utf-8 -*-

from __future__ import unicode_literals
try:
    from django.conf.urls import patterns, include, url
except ImportError:
    from django.conf.urls.defaults import patterns, include, url

from noticeapp.feeds import LastPosts, LastCourses
from noticeapp.views import IndexView, CategoryView, NoticeView, CourseView,\
    AddPostView, EditPostView, UserView, PostView, ProfileEditView,\
    DeletePostView, StickCourseView, UnstickCourseView, CloseCourseView,\
    OpenCourseView, ModeratePost, CoursePollVoteView, LatestCoursesView,\
    UserNotices, UserPosts, course_cancel_poll_vote


urlpatterns = patterns('',
                       # Syndication feeds
                       url('^feeds/posts/$', LastPosts(), name='feed_posts'),
                       url('^feeds/courses/$', LastCourses(), name='feed_courses'),
                       )

urlpatterns += patterns('noticeapp.views',
                        # Index, Category, notice
                        url('^$', UserNotices.as_view(), name='user_notices'),
                        url('^course/(?P<course_id>\d+)/post/add/$', AddPostView.as_view(), name='add_post'),

                        # Post
                        url('^post/(?P<pk>\d+)/$', PostView.as_view(), name='post'),
                        url('^post/(?P<pk>\d+)/edit/$', EditPostView.as_view(), name='edit_post'),
                        url('^post/(?P<pk>\d+)/delete/$', DeletePostView.as_view(), name='delete_post'),



                        url(r'^notifications/$', IndexView.as_view(), name='index'),
                        url('^category/(?P<pk>\d+)/$', CategoryView.as_view(), name='category'),
                        url('^notice/(?P<pk>\d+)/$', NoticeView.as_view(), name='notice'),

                        # User
                        url('^users/(?P<username>[^/]+)/$', UserView.as_view(), name='user'),
                        url('^block_user/([^/]+)/$', 'block_user', name='block_user'),
                        url('^unblock_user/([^/]+)/$', 'unblock_user', name='unblock_user'),

                        url(r'^users/(?P<username>[^/]+)/posts/$', UserPosts.as_view(), name='user_posts'),

                        # Profile
                        url('^profile/edit/$', ProfileEditView.as_view(), name='edit_profile'),

                        # Course
                        url('^course/(?P<pk>\d+)/$', CourseView.as_view(), name='course'),
                        url('^course/(?P<pk>\d+)/stick/$', StickCourseView.as_view(), name='stick_course'),
                        url('^course/(?P<pk>\d+)/unstick/$', UnstickCourseView.as_view(), name='unstick_course'),
                        url('^course/(?P<pk>\d+)/close/$', CloseCourseView.as_view(), name='close_course'),
                        url('^course/(?P<pk>\d+)/open/$', OpenCourseView.as_view(), name='open_course'),
                        url('^course/(?P<pk>\d+)/poll_vote/$', CoursePollVoteView.as_view(), name='course_poll_vote'),
                        url('^course/(?P<pk>\d+)/cancel_poll_vote/$', course_cancel_poll_vote, name='course_cancel_poll_vote'),
                        url('^course/latest/$', LatestCoursesView.as_view(), name='course_latest'),

                        # Add course/post
                        url('^notice/(?P<notice_id>\d+)/course/add/$', AddPostView.as_view(), name='add_course'),
                        url('^course/(?P<course_id>\d+)/post/add/$', AddPostView.as_view(), name='add_post'),

                        # Post
                        url('^post/(?P<pk>\d+)/$', PostView.as_view(), name='post'),
                        url('^post/(?P<pk>\d+)/edit/$', EditPostView.as_view(), name='edit_post'),
                        url('^post/(?P<pk>\d+)/delete/$', DeletePostView.as_view(), name='delete_post'),
                        url('^post/(?P<pk>\d+)/moderate/$', ModeratePost.as_view(), name='moderate_post'),

                        # Attachment
                        #url('^attachment/(\w+)/$', 'show_attachment', name='noticeapp_attachment'),

                        # Subscription
                        url('^subscription/course/(\d+)/delete/$',
                            'delete_subscription', name='delete_subscription'),
                        url('^subscription/course/(\d+)/add/$',
                            'add_subscription', name='add_subscription'),

                        # API
                        url('^api/post_ajax_preview/$', 'post_ajax_preview', name='post_ajax_preview'),

                        # Commands
                        url('^mark_all_as_read/$', 'mark_all_as_read', name='mark_all_as_read')
                        )
