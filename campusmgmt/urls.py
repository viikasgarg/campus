from django.conf.urls import patterns, include, url
from profiles import views as profile_views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import admin
from dajaxice.core import dajaxice_autodiscover, dajaxice_config


# from xadmin.plugins import xversion
# xversion.register_models()

admin.autodiscover()
dajaxice_autodiscover()
'''
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'campusmgmt.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    # Examples:
    url(r'^$', 'main.views.home', name='main.home'),
    #(r'^admin/', include("massadmin.urls")),
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),

)
'''

urlpatterns = patterns('',
    (r'^admin/', include("massadmin.urls")),
    (r'^admin_export/', include("admin_export.urls")),
    (r'^ckeditor/', include('ckeditor.urls')),# 1.6 compat  include('ckeditor.urls')),
    (r'^grappelli/', include('grappelli.urls')),
    #(r'^$', 'profiles.views.index'),
    url(r'^$', 'main.views.home', name='main.home'),
    #url(r'^campus/', include(xadmin.site.urls)),
    #url(r'^testcrud/', include('testcrud.urls', namespace='testcrud')),
    url(r'^profiles/', include('profiles.urls')),
    (r'^admin/jsi18n', 'django.views.i18n.javascript_catalog'),

    (r'^report_builder/', include('report_builder.urls')),
    #(r'^simple_import/', include('simple_import.urls')),
    url(r'^accounts/password_change/$', 'django.contrib.auth.views.password_change'),
    url(r'^accounts/password_change_done/$', 'django.contrib.auth.views.password_change_done', name="password_change_done"),

    url(r'^logout/$', profile_views.logout_view, name='logout'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/jsi18n/$', 'django.views.i18n.javascript_catalog'),
    (r'^admin/', include(admin.site.urls) ),
    (r'^ajax_select/', include('ajax_select.urls')),
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    #(r'^reports/', include('scaffold_report.urls')),
    url(r"^su/", include("django_su.urls")),
)

if settings.GAPPS:
    urlpatterns += patterns('', (r'^accounts/login/$', 'google_auth.views.login'), )
else:
    urlpatterns += patterns('', (r'^accounts/login/$', 'django.contrib.auth.views.login'), )

if 'ldap_groups' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',(r'^ldap_grp/', include('ldap_groups.urls')),)
if 'discipline' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^discipline/', include('discipline.urls')), )
if 'attendance' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^attendance/', include('attendance.urls')), )
if 'schedule' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^schedule/', include('schedule.urls',namespace='schedule')), )
if 'work_study' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^work_study/', include('work_study.urls')), )
if 'admissions' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^admissions/', include('admissions.urls')), )
if 'omr' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^omr/', include('omr.urls')), )
if 'volunteer_track' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^volunteer_track/', include('volunteer_track.urls')), )
if 'benchmark_grade' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^benchmark_grade/', include('benchmark_grade.urls')), )
if 'inventory' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^inventory/', include('inventory.urls')), )
if 'engrade_sync' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^engrade_sync/', include('engrade_sync.urls')), )
if 'grades' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^grades/', include('grades.urls')), )
if 'naviance_sso' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^naviance_sso/', include('naviance_sso.urls')), )
if 'alumni' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^alumni/', include('alumni.urls')), )
if 'integrations.canvas_sync' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^canvas_sync/', include('integrations.canvas_sync.urls')), )
if 'integrations.schoolreach' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', (r'^schoolreach/', include('integrations.schoolreach.urls')), )
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )
if 'social.apps.django_app.default' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', url('', include('social.apps.django_app.urls', namespace='social')),)

urlpatterns += patterns('', (r'^', include('responsive_dashboard.urls')), )

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT,})
    )
