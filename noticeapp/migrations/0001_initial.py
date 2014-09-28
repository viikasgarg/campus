# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
try:
    from sorl.thumbnail.fields import ImageField
except ImportError:
    from django.db.models import ImageField
from django.conf import settings
import noticeapp.util
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('size', models.IntegerField(verbose_name='Size')),
                ('file', models.FileField(upload_to=noticeapp.util.FilePathGenerator(to='noticeapp_upload/attachments'), verbose_name='File')),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='Name')),
                ('position', models.IntegerField(default=0, verbose_name='Position', blank=True)),
                ('hidden', models.BooleanField(default=False, help_text='If checked, this category will be visible only for staff', verbose_name='Hidden')),
            ],
            options={
                'ordering': ['position'],
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='Name')),
                ('position', models.IntegerField(default=0, verbose_name='Position', blank=True)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('updated', models.DateTimeField(null=True, verbose_name='Updated', blank=True)),
                ('post_count', models.IntegerField(default=0, verbose_name='Post count', blank=True)),
                ('course_count', models.IntegerField(default=0, verbose_name='Course count', blank=True)),
                ('hidden', models.BooleanField(default=False, verbose_name='Hidden')),
                ('headline', models.TextField(null=True, verbose_name='Headline', blank=True)),
                ('category', models.ForeignKey(related_name='notices', verbose_name='Category', to='noticeapp.Category')),
                ('moderators', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='Moderators', blank=True)),
                ('parent', models.ForeignKey(related_name='child_notices', verbose_name='Parent notice', blank=True, to='noticeapp.Notice', null=True)),
            ],
            options={
                'ordering': ['position'],
                'verbose_name': 'Notice',
                'verbose_name_plural': 'Notices',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NoticeReadTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_stamp', models.DateTimeField(auto_now=True)),
                ('notice', models.ForeignKey(blank=True, to='noticeapp.Notice', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notice read tracker',
                'verbose_name_plural': 'Notice read trackers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=255, verbose_name='Text')),
            ],
            options={
                'verbose_name': 'Poll answer',
                'verbose_name_plural': 'Polls answers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollAnswerUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('poll_answer', models.ForeignKey(related_name='users', verbose_name='Poll answer', to='noticeapp.PollAnswer')),
                ('user', models.ForeignKey(related_name='poll_answers', verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Poll answer user',
                'verbose_name_plural': 'Polls answers users',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(verbose_name='Message')),
                ('body_html', models.TextField(verbose_name='HTML version')),
                ('body_text', models.TextField(verbose_name='Text version')),
                ('created', models.DateTimeField(db_index=True, verbose_name='Created', blank=True)),
                ('updated', models.DateTimeField(null=True, verbose_name='Updated', blank=True)),
                ('user_ip', models.IPAddressField(default='0.0.0.0', verbose_name='User IP', blank=True)),
                ('on_moderation', models.BooleanField(default=False, verbose_name='On moderation')),
            ],
            options={
                'ordering': ['created'],
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('signature', models.TextField(max_length=1024, verbose_name='Signature', blank=True)),
                ('signature_html', models.TextField(max_length=1054, verbose_name='Signature HTML Version', blank=True)),
                ('time_zone', models.FloatField(default=3.0, verbose_name='Time zone', choices=[(-12.0, b'-12'), (-11.0, b'-11'), (-10.0, b'-10'), (-9.5, b'-09.5'), (-9.0, b'-09'), (-8.5, b'-08.5'), (-8.0, b'-08 PST'), (-7.0, b'-07 MST'), (-6.0, b'-06 CST'), (-5.0, b'-05 EST'), (-4.0, b'-04 AST'), (-3.5, b'-03.5'), (-3.0, b'-03 ADT'), (-2.0, b'-02'), (-1.0, b'-01'), (0.0, b'00 GMT'), (1.0, b'+01 CET'), (2.0, b'+02'), (3.0, b'+03'), (3.5, b'+03.5'), (4.0, b'+04'), (4.5, b'+04.5'), (5.0, b'+05'), (5.5, b'+05.5'), (6.0, b'+06'), (6.5, b'+06.5'), (7.0, b'+07'), (8.0, b'+08'), (9.0, b'+09'), (9.5, b'+09.5'), (10.0, b'+10'), (10.5, b'+10.5'), (11.0, b'+11'), (11.5, b'+11.5'), (12.0, b'+12'), (13.0, b'+13'), (14.0, b'+14')])),
                ('language', models.CharField(default='en-us', max_length=10, verbose_name='Language', blank=True, choices=[(b'af', b'Afrikaans'), (b'ar', b'Arabic'), (b'ast', b'Asturian'), (b'az', b'Azerbaijani'), (b'bg', b'Bulgarian'), (b'be', b'Belarusian'), (b'bn', b'Bengali'), (b'br', b'Breton'), (b'bs', b'Bosnian'), (b'ca', b'Catalan'), (b'cs', b'Czech'), (b'cy', b'Welsh'), (b'da', b'Danish'), (b'de', b'German'), (b'el', b'Greek'), (b'en', b'English'), (b'en-au', b'Australian English'), (b'en-gb', b'British English'), (b'eo', b'Esperanto'), (b'es', b'Spanish'), (b'es-ar', b'Argentinian Spanish'), (b'es-mx', b'Mexican Spanish'), (b'es-ni', b'Nicaraguan Spanish'), (b'es-ve', b'Venezuelan Spanish'), (b'et', b'Estonian'), (b'eu', b'Basque'), (b'fa', b'Persian'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'fy', b'Frisian'), (b'ga', b'Irish'), (b'gl', b'Galician'), (b'he', b'Hebrew'), (b'hi', b'Hindi'), (b'hr', b'Croatian'), (b'hu', b'Hungarian'), (b'ia', b'Interlingua'), (b'id', b'Indonesian'), (b'io', b'Ido'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'ja', b'Japanese'), (b'ka', b'Georgian'), (b'kk', b'Kazakh'), (b'km', b'Khmer'), (b'kn', b'Kannada'), (b'ko', b'Korean'), (b'lb', b'Luxembourgish'), (b'lt', b'Lithuanian'), (b'lv', b'Latvian'), (b'mk', b'Macedonian'), (b'ml', b'Malayalam'), (b'mn', b'Mongolian'), (b'mr', b'Marathi'), (b'my', b'Burmese'), (b'nb', b'Norwegian Bokmal'), (b'ne', b'Nepali'), (b'nl', b'Dutch'), (b'nn', b'Norwegian Nynorsk'), (b'os', b'Ossetic'), (b'pa', b'Punjabi'), (b'pl', b'Polish'), (b'pt', b'Portuguese'), (b'pt-br', b'Brazilian Portuguese'), (b'ro', b'Romanian'), (b'ru', b'Russian'), (b'sk', b'Slovak'), (b'sl', b'Slovenian'), (b'sq', b'Albanian'), (b'sr', b'Serbian'), (b'sr-latn', b'Serbian Latin'), (b'sv', b'Swedish'), (b'sw', b'Swahili'), (b'ta', b'Tamil'), (b'te', b'Telugu'), (b'th', b'Thai'), (b'tr', b'Turkish'), (b'tt', b'Tatar'), (b'udm', b'Udmurt'), (b'uk', b'Ukrainian'), (b'ur', b'Urdu'), (b'vi', b'Vietnamese'), (b'zh-cn', b'Simplified Chinese'), (b'zh-hans', b'Simplified Chinese'), (b'zh-hant', b'Traditional Chinese'), (b'zh-tw', b'Traditional Chinese')])),
                ('show_signatures', models.BooleanField(default=True, verbose_name='Show signatures')),
                ('post_count', models.IntegerField(default=0, verbose_name='Post count', blank=True)),
                ('avatar', ImageField(upload_to=noticeapp.util.FilePathGenerator(to=b'noticeapp/avatar'), null=True, verbose_name='Avatar', blank=True)),
                ('autosubscribe', models.BooleanField(default=True, help_text='Automatically subscribe to courses that you answer', verbose_name='Automatically subscribe')),
                ('user', annoying.fields.AutoOneToOneField(related_name='noticeapp_profile', verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profile',
                'verbose_name_plural': 'Profiles',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Subject')),
                ('created', models.DateTimeField(null=True, verbose_name='Created')),
                ('updated', models.DateTimeField(null=True, verbose_name='Updated')),
                ('views', models.IntegerField(default=0, verbose_name='Views count', blank=True)),
                ('sticky', models.BooleanField(default=False, verbose_name='Sticky')),
                ('closed', models.BooleanField(default=False, verbose_name='Closed')),
                ('post_count', models.IntegerField(default=0, verbose_name='Post count', blank=True)),
                ('on_moderation', models.BooleanField(default=False, verbose_name='On moderation')),
                ('poll_type', models.IntegerField(default=0, verbose_name='Poll type', choices=[(0, 'None'), (1, 'Single answer'), (2, 'Multiple answers')])),
                ('poll_question', models.TextField(null=True, verbose_name='Poll question', blank=True)),
                ('notice', models.ForeignKey(related_name='courses', verbose_name='Notice', to='noticeapp.Notice')),
            ],
            options={
                'ordering': ['-created'],
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseReadTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_stamp', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(blank=True, to='noticeapp.Course', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Course read tracker',
                'verbose_name_plural': 'Course read trackers',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='coursereadtracker',
            unique_together=set([('user', 'course')]),
        ),
        migrations.AddField(
            model_name='course',
            name='readed_by',
            field=models.ManyToManyField(related_name='readed_courses', through='noticeapp.CourseReadTracker', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='subscribers',
            field=models.ManyToManyField(related_name='subscriptions', verbose_name='Subscribers', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='user',
            field=models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='course',
            field=models.ForeignKey(related_name='posts', verbose_name='Course', to='noticeapp.Course'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(related_name='posts', verbose_name='User', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='pollansweruser',
            unique_together=set([('poll_answer', 'user')]),
        ),
        migrations.AddField(
            model_name='pollanswer',
            name='course',
            field=models.ForeignKey(related_name='poll_answers', verbose_name='Course', to='noticeapp.Course'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='noticereadtracker',
            unique_together=set([('user', 'notice')]),
        ),
        migrations.AddField(
            model_name='notice',
            name='readed_by',
            field=models.ManyToManyField(related_name='readed_notices', through='noticeapp.NoticeReadTracker', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='post',
            field=models.ForeignKey(related_name='attachments', verbose_name='Post', to='noticeapp.Post'),
            preserve_default=True,
        ),
    ]
