from django.conf.urls import *
from views import *

urlpatterns = patterns('',
    (r'^disc/$', enter_discipline),
    (r'^disc/list$', discipline_list),
    (r'^disc/view$', view_discipline),
    (r'^disc/list/(?P<type>[a-z]+)$', discipline_list),
    (r'^disc/report/(?P<student_id>\d+)/$', discipline_report),
    (r'^disc/stats/$', discipline_report_view),
    (r'^generate_from_attendance/$', generate_from_attendance),
)
