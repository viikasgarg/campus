from django.conf.urls import patterns
from .views import transcript_nonofficial, photo_flash_card, thumbnail, paper_attendance
from .views import user_preferences, view_student, ajax_include_deleted, \
                     import_naviance, increment_year, increment_year_confirm, \
                    StudentViewDashletView, prof_home, student_home

urlpatterns = patterns('',
    (r'^reports/transcript_nonofficial/(?P<student_id>\d+)/$', transcript_nonofficial),
    (r'^flashcard/$', photo_flash_card),
    (r'^flashcard/(?P<year>\d+)/$', photo_flash_card),
    (r'^preferences/$', user_preferences),
    (r'^view_student/$', view_student),
    (r'^view_student/(?P<id>\d+)/$', view_student),
    (r'^ajax_view_student_dashlet/(?P<pk>\d+)/$', StudentViewDashletView.as_view()),
    (r'^ajax_include_deleted/$', ajax_include_deleted),
    (r'^student/naviance/$', import_naviance),
    (r'^increment_year/$', increment_year),
    (r'^increment_year_confirm/(?P<year_id>\d+)/$', increment_year_confirm),
    (r'^thumbnail/(?P<year>\d+)/$', thumbnail),
    (r'^paper_attendance/(?P<day>\d+)/$', paper_attendance),
    (r'^prof/home/$', prof_home),
    (r'^student/home/$', student_home),
)
# -*- coding: utf-8 -*-

from django.conf.urls import *
from views import *

student_patterns= patterns(
    '',
    url(r'^list/page(?P<page>[0-9]+)/(\?.*)?$',
        StudentListView.as_view(),
        name='list'),
    url(r'^update/(?P<pk>\d+)/$',
        StudentUpdateView.as_view(),
        name='update'),
    url(r'^create/$',
        StudentCreateView.as_view(),
        name='create'),
    url(r'^delete/(?P<pk>[0-9]+)/$',
        StudentDeleteView.as_view(),
        name='delete'))


newpatterns = patterns(
    '',
    url(r'^student/', include(student_patterns,
        namespace="student")))


try:
    urlpatterns += newpatterns
except NameError:
    urlpatterns = newpatterns
