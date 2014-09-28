# -*- coding: utf-8
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.core.urlresolvers import reverse

from noticeapp.models import Category, Notice, Course, Post, Profile, Attachment, PollAnswer

from noticeapp import compat, util
username_field = compat.get_username_field()


class NoticeInlineAdmin(admin.TabularInline):
    model = Notice
    fields = ['name', 'hidden', 'position']
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'hidden', 'notice_count']
    list_per_page = 20
    ordering = ['position']
    search_fields = ['name']
    list_editable = ['position']

    inlines = [NoticeInlineAdmin]


class NoticeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'hidden', 'position', 'course_count', ]
    list_per_page = 20
    raw_id_fields = ['moderators']
    ordering = ['-category']
    search_fields = ['name', 'category__name']
    list_editable = ['position', 'hidden']
    fieldsets = (
        (None, {
                'fields': ('category', 'parent', 'name', 'hidden', 'position', )
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields': ('updated', 'description', 'headline', 'post_count', 'moderators')
                }
            ),
        )


class PollAnswerAdmin(admin.TabularInline):
    model = PollAnswer
    fields = ['text', ]
    extra = 0


class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'notice', 'created', 'head', 'post_count', 'poll_type',]
    list_per_page = 20
    raw_id_fields = ['user', 'subscribers']
    ordering = ['-created']
    date_hierarchy = 'created'
    search_fields = ['name']
    fieldsets = (
        (None, {
                'fields': ('notice', 'name', 'user', ('created', 'updated'), 'poll_type',)
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields': (('views', 'post_count'), ('sticky', 'closed'), 'subscribers')
                }
         ),
        )
    inlines = [PollAnswerAdmin, ]

class CourseReadTrackerAdmin(admin.ModelAdmin):
    list_display = ['course', 'user', 'time_stamp']
    search_fields = ['user__%s' % username_field]

class NoticeReadTrackerAdmin(admin.ModelAdmin):
    list_display = ['notice', 'user', 'time_stamp']
    search_fields = ['user__%s' % username_field]

class PostAdmin(admin.ModelAdmin):
    list_display = ['course', 'user', 'created', 'updated', 'summary']
    list_per_page = 20
    raw_id_fields = ['user', 'course']
    ordering = ['-created']
    date_hierarchy = 'created'
    search_fields = ['body']
    fieldsets = (
        (None, {
                'fields': ('course', 'user')
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields' : (('created', 'updated'), 'user_ip')
                }
         ),
        (_('Message'), {
                'fields': ('body', 'body_html', 'body_text')
                }
         ),
        )


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'time_zone', 'language', 'post_count']
    list_per_page = 20
    ordering = ['-user']
    search_fields = ['user__%s' % username_field]
    fieldsets = (
        (None, {
                'fields': ('time_zone', 'language')
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields' : ('avatar', 'signature', 'show_signatures')
                }
         ),
        )


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file', 'size', 'admin_view_post', 'admin_edit_post']

    def admin_view_post(self, obj):
        return '<a href="%s">view</a>' % obj.post.get_absolute_url()
    admin_view_post.allow_tags = True
    admin_view_post.short_description = _('View post')

    def admin_edit_post(self, obj):
        return '<a href="%s">edit</a>' % reverse('admin:noticeapp_post_change', args=[obj.post.pk])
    admin_edit_post.allow_tags = True
    admin_edit_post.short_description = _('Edit post')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Attachment, AttachmentAdmin)

if util.get_noticeapp_profile_model() == Profile:
    admin.site.register(Profile, ProfileAdmin)

# This can be used to debug read/unread trackers

#admin.site.register(CourseReadTracker, CourseReadTrackerAdmin)
#admin.site.register(NoticeReadTracker, NoticeReadTrackerAdmin)