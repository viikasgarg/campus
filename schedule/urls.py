from django.conf.urls import *
from schedule.views import *

urlpatterns = patterns('',
    (r'^enroll/(?P<id>\d+)$', schedule_enroll),
)
# -*- coding: utf-8 -*-

from django.conf.urls import *
from views import *

coursemeet_patterns= patterns(
    '',
    url(r'^list/page(?P<page>[0-9]+)/(\?.*)?$',
        CourseMeetListView.as_view(),
        name='list'),
    url(r'^update/(?P<pk>\d+)/$',
        CourseMeetUpdateView.as_view(),
        name='update'),
    url(r'^create/$',
        CourseMeetCreateView.as_view(),
        name='create'),
    url(r'^delete/(?P<pk>[0-9]+)/$',
        CourseMeetDeleteView.as_view(),
        name='delete'))


newpatterns = patterns(
    '',
    url(r'^period/', include(coursemeet_patterns,
        namespace="period")))


try:
    urlpatterns += newpatterns
except NameError:
    urlpatterns = newpatterns


course_patterns= patterns(
    '',
    url(r'^list/page(?P<page>[0-9]+)/(\?.*)?$',
        CourseListView.as_view(),
        name='list'),)



newpatterns = patterns(
    '',
    url(r'^course/', include(course_patterns,
        namespace="course")))


try:
    urlpatterns += newpatterns
except NameError:
    urlpatterns = newpatterns


courseenrollment_patterns= patterns(
    '',
    url(r'^list/page(?P<page>[0-9]+)/(\?.*)?$',
        CourseEnrollmentListView.as_view(),
        name='list'))


newpatterns = patterns(
    '',
    url(r'^mycourses/', include(courseenrollment_patterns,
        namespace="mucourses")))


try:
    urlpatterns += newpatterns
except NameError:
    urlpatterns = newpatterns


coursemeet_patterns= patterns(
    '',
    url(r'^list/page(?P<page>[0-9]+)/(\?.*)?$',
        StudentCourseMeetListView.as_view(),
        name='list'),
    )


newpatterns = patterns(
    '',
    url(r'^classes/', include(coursemeet_patterns,
        namespace="classes")))


try:
    urlpatterns += newpatterns
except NameError:
    urlpatterns = newpatterns




coursemeet_patterns= patterns(
    '',
    url(r'^list/page(?P<page>[0-9]+)/(\?.*)?$',
        TodayCourseMeetListView.as_view(),
        name='list'),
    )


newpatterns = patterns(
    '',
    url(r'^tclasses/', include(coursemeet_patterns,
        namespace="tclasses")))


try:
    urlpatterns += newpatterns
except NameError:
    urlpatterns = newpatterns