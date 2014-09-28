# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import math

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import F, Q
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest,\
    HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import ModelFormMixin
from django.views.decorators.csrf import csrf_protect
from django.views import generic
from noticeapp import compat, defaults, util
from noticeapp.forms import PostForm, AdminPostForm, AttachmentFormSet, PollAnswerFormSet, PollForm
from noticeapp.models import Category, Notice, Course, Post, CourseReadTracker, NoticeReadTracker, PollAnswerUser
from noticeapp.permissions import perms
from noticeapp.templatetags.noticeapp_tags import noticeapp_course_poll_not_voted


User = compat.get_user_model()
username_field = compat.get_username_field()
Paginator, pure_pagination = compat.get_paginator_class()


class PaginatorMixin(object):
    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        kwargs = {}
        if pure_pagination:
            kwargs['request'] = self.request
        return Paginator(queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs)

class RedirectToLoginMixin(object):
    """ mixin which redirects to settings.LOGIN_URL if the view encounters an PermissionDenied exception
        and the user is not authenticated. Views inheriting from this need to implement
        get_login_redirect_url(), which returns the URL to redirect to after login (parameter "next")
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(RedirectToLoginMixin, self).dispatch(request, *args, **kwargs)
        except PermissionDenied:
            if not request.user.is_authenticated():
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(self.get_login_redirect_url())
            else:
                return HttpResponseForbidden()

    def get_login_redirect_url(self):
        """ get the url to which we redirect after the user logs in. subclasses should override this """
        return '/'

class UserNotices(PaginatorMixin, generic.ListView):
    model = Post
    paginate_by = defaults.NOTICE_APP_PAGE_SIZE
    template_name = 'noticeapp/user_notices.html'

    def dispatch(self, request, *args, **kwargs):
        return super(UserNotices, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(UserNotices, self).get_queryset()
        qs = qs.filter(user=self.request.user)
        qs = qs.order_by('-updated', '-created', '-id')
        return qs

    def get_context_data(self, **kwargs):
        context = super(UserNotices, self).get_context_data(**kwargs)
        context['target_user'] = self.request.user
        context['course_list'] = Course.objects.filter(user=self.request.user).order_by('-updated', '-created', '-id')
        return context


class IndexView(generic.ListView):

    template_name = 'noticeapp/index.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)
        categories = ctx['categories']
        for category in categories:
            category.notices_accessed = perms.filter_notices(self.request.user, category.notices.filter(parent=None))
        ctx['categories'] = categories
        return ctx

    def get_queryset(self):
        return perms.filter_categories(self.request.user, Category.objects.all())


class CategoryView(RedirectToLoginMixin, generic.DetailView):

    template_name = 'noticeapp/index.html'
    context_object_name = 'category'

    def get_login_redirect_url(self):
        return reverse('noticeapp:category', args=(self.kwargs['pk'],))

    def get_queryset(self):
        return Category.objects.all()

    def get_object(self, queryset=None):
        obj = super(CategoryView, self).get_object(queryset)
        if not perms.may_view_category(self.request.user, obj):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super(CategoryView, self).get_context_data(**kwargs)
        ctx['category'].notices_accessed = perms.filter_notices(self.request.user, ctx['category'].notices.filter(parent=None))
        ctx['categories'] = [ctx['category']]
        return ctx


class NoticeView(RedirectToLoginMixin, PaginatorMixin, generic.ListView):

    paginate_by = defaults.NOTICE_APP_PAGE_SIZE
    context_object_name = 'course_list'
    template_name = 'noticeapp/notice.html'

    def get_context_data(self, **kwargs):
        ctx = super(NoticeView, self).get_context_data(**kwargs)
        ctx['notice'] = self.notice
        ctx['notice'].notices_accessed = perms.filter_notices(self.request.user, self.notice.child_notices.all())
        return ctx

    def get_queryset(self):
        self.notice = Notice.objects.all()[0]
        qs = self.notice.courses.filter(user=self.request.user).order_by('-sticky', '-updated', '-id').select_related()
        return qs


class LatestCoursesView(PaginatorMixin, generic.ListView):

    paginate_by = defaults.NOTICE_APP_PAGE_SIZE
    context_object_name = 'course_list'
    template_name = 'noticeapp/latest_courses.html'

    def get_queryset(self):
        qs = Course.objects.all().select_related()
        qs = perms.filter_courses(self.request.user, qs)
        return qs.order_by('-updated', '-id')


class CourseView(RedirectToLoginMixin, PaginatorMixin, generic.ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    template_object_name = 'post_list'
    template_name = 'noticeapp/course.html'

    post_form_class = PostForm
    admin_post_form_class = AdminPostForm
    poll_form_class = PollForm
    attachment_formset_class = AttachmentFormSet

    def get_login_redirect_url(self):
        return reverse('noticeapp:course', args=(self.kwargs['pk'],))

    def get_post_form_class(self):
        return self.post_form_class

    def get_admin_post_form_class(self):
        return self.admin_post_form_class

    def get_poll_form_class(self):
        return self.poll_form_class

    def get_attachment_formset_class(self):
        return self.attachment_formset_class

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course.objects.select_related('notice'), pk=kwargs['pk'])

        if request.GET.get('first-unread'):
            if request.user.is_authenticated():
                read_dates = []
                try:
                    read_dates.append(CourseReadTracker.objects.get(user=request.user, course=self.course).time_stamp)
                except CourseReadTracker.DoesNotExist:
                    pass
                try:
                    read_dates.append(NoticeReadTracker.objects.get(user=request.user, notice=self.course.notice).time_stamp)
                except NoticeReadTracker.DoesNotExist:
                    pass

                read_date = read_dates and max(read_dates)
                if read_date:
                    try:
                        first_unread_course = self.course.posts.filter(created__gt=read_date).order_by('created', 'id')[0]
                    except IndexError:
                        first_unread_course = self.course.last_post
                else:
                    first_unread_course = self.course.head
                return HttpResponseRedirect(reverse('noticeapp:post', kwargs={'pk': first_unread_course.id}))

        return super(CourseView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if not perms.may_view_course(self.request.user, self.course):
            raise PermissionDenied
        if self.request.user.is_authenticated() or not defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER:
            Course.objects.filter(id=self.course.id).update(views=F('views') + 1)
        else:
            cache_key = util.build_cache_key('anonymous_course_views', course_id=self.course.id)
            cache.add(cache_key, 0)
            if cache.incr(cache_key) % defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER == 0:
                Course.objects.filter(id=self.course.id).update(views=F('views') +
                                                                    defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER)
                cache.set(cache_key, 0)
        qs = self.course.posts.all().select_related('user')
        if defaults.PYBB_PROFILE_RELATED_NAME:
            qs = qs.select_related('user__%s' % defaults.PYBB_PROFILE_RELATED_NAME)
        if not perms.may_moderate_course(self.request.user, self.course):
            qs = perms.filter_posts(self.request.user, qs)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(CourseView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            self.request.user.is_moderator = perms.may_moderate_course(self.request.user, self.course)
            self.request.user.is_subscribed = self.request.user in self.course.subscribers.all()
            if perms.may_post_as_admin(self.request.user):
                ctx['form'] = self.get_admin_post_form_class()(
                    initial={'login': getattr(self.request.user, username_field)},
                    course=self.course)
            else:
                ctx['form'] = self.get_post_form_class()(course=self.course)
            self.mark_read(self.request.user, self.course)
        elif defaults.PYBB_ENABLE_ANONYMOUS_POST:
            ctx['form'] = self.get_post_form_class()(course=self.course)
        else:
            ctx['form'] = None
            ctx['next'] = self.get_login_redirect_url()
        if perms.may_attach_files(self.request.user):
            aformset = self.get_attachment_formset_class()()
            ctx['aformset'] = aformset
        if defaults.PYBB_FREEZE_FIRST_POST:
            ctx['first_post'] = self.course.head
        else:
            ctx['first_post'] = None
        ctx['course'] = self.course

        if perms.may_vote_in_course(self.request.user, self.course) and \
                noticeapp_course_poll_not_voted(self.course, self.request.user):
            ctx['poll_form'] = self.get_poll_form_class()(self.course)

        return ctx

    def mark_read(self, user, course):
        try:
            notice_mark = NoticeReadTracker.objects.get(notice=course.notice, user=user)
        except NoticeReadTracker.DoesNotExist:
            notice_mark = None
        if (notice_mark is None) or (notice_mark.time_stamp < course.updated):
            # Mark course as readed
            course_mark, new = CourseReadTracker.objects.get_or_create_tracker(course=course, user=user)
            if not new:
                course_mark.save()

            # Check, if there are any unread courses in notice
            readed = course.notice.courses.filter((Q(coursereadtracker__user=user,
                                                  coursereadtracker__time_stamp__gte=F('updated'))) |
                                                Q(notice__noticereadtracker__user=user,
                                                  notice__noticereadtracker__time_stamp__gte=F('updated')))\
                                       .only('id').order_by()

            not_readed = course.notice.courses.exclude(id__in=readed)
            if not not_readed.exists():
                # Clear all course marks for this notice, mark notice as readed
                CourseReadTracker.objects.filter(user=user, course__notice=course.notice).delete()
                notice_mark, new = NoticeReadTracker.objects.get_or_create_tracker(notice=course.notice, user=user)
                notice_mark.save()


class PostEditMixin(object):

    poll_answer_formset_class = PollAnswerFormSet

    def get_poll_answer_formset_class(self):
        return self.poll_answer_formset_class

    def get_form_class(self):
        if perms.may_post_as_admin(self.request.user):
            return AdminPostForm
        else:
            return PostForm

    def get_context_data(self, **kwargs):
        ctx = super(PostEditMixin, self).get_context_data(**kwargs)
        if perms.may_attach_files(self.request.user) and (not 'aformset' in kwargs):
            ctx['aformset'] = AttachmentFormSet(instance=self.object if getattr(self, 'object') else None)
        if perms.may_create_poll(self.request.user) and ('pollformset' not in kwargs):
            ctx['pollformset'] = self.get_poll_answer_formset_class()(
                instance=self.object.course if getattr(self, 'object') else None
            )
        return ctx

    def form_valid(self, form):
        success = True
        save_attachments = False
        save_poll_answers = False
        self.object = form.save(commit=False)

        if perms.may_attach_files(self.request.user):
            aformset = AttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object)
            if aformset.is_valid():
                save_attachments = True
            else:
                success = False
        else:
            aformset = None

        if perms.may_create_poll(self.request.user):
            pollformset = self.get_poll_answer_formset_class()()
            if getattr(self, 'notice', None) or self.object.course.head == self.object:
                if self.object.course.poll_type != Course.POLL_TYPE_NONE:
                    pollformset = self.get_poll_answer_formset_class()(self.request.POST,
                                                                       instance=self.object.course)
                    if pollformset.is_valid():
                        save_poll_answers = True
                    else:
                        success = False
                else:
                    self.object.course.poll_question = None
                    self.object.course.poll_answers.all().delete()
        else:
            pollformset = None

        if success:
            self.object.course.save()
            self.object.course = self.object.course
            self.object.save()
            if save_attachments:
                aformset.save()
            if save_poll_answers:
                pollformset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, aformset=aformset, pollformset=pollformset))


class AddPostView(PostEditMixin, generic.CreateView):

    template_name = 'noticeapp/add_post.html'

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            self.user = request.user
        else:
            if defaults.PYBB_ENABLE_ANONYMOUS_POST:
                self.user, new = User.objects.get_or_create(**{username_field: defaults.PYBB_ANONYMOUS_USERNAME})
            else:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())

        self.notice = None
        self.course = None
        if 'notice_id' in kwargs:
            self.notice = get_object_or_404(perms.filter_notices(request.user, Notice.objects.all()), pk=kwargs['notice_id'])
            if not perms.may_create_course(self.user, self.notice):
                raise PermissionDenied
        elif 'course_id' in kwargs:
            self.course = get_object_or_404(perms.filter_courses(request.user, Course.objects.all()), pk=kwargs['course_id'])
            if not perms.may_create_post(self.user, self.course):
                raise PermissionDenied

            self.quote = ''
            if 'quote_id' in request.GET:
                try:
                    quote_id = int(request.GET.get('quote_id'))
                except TypeError:
                    raise Http404
                else:
                    post = get_object_or_404(Post, pk=quote_id)
                    self.quote = defaults.PYBB_QUOTE_ENGINES[defaults.PYBB_MARKUP](post.body, getattr(post.user, username_field))

                if self.quote and request.is_ajax():
                    return HttpResponse(self.quote)
        return super(AddPostView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        ip = self.request.META.get('REMOTE_ADDR', '')
        form_kwargs = super(AddPostView, self).get_form_kwargs()
        form_kwargs.update(dict(course=self.course, notice=self.notice, user=self.user,
                           ip=ip, initial={}))
        if getattr(self, 'quote', None):
            form_kwargs['initial']['body'] = self.quote
        if perms.may_post_as_admin(self.user):
            form_kwargs['initial']['login'] = getattr(self.user, username_field)
        form_kwargs['may_create_poll'] = perms.may_create_poll(self.user)
        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super(AddPostView, self).get_context_data(**kwargs)
        ctx['notice'] = self.notice
        ctx['course'] = self.course
        return ctx

    def get_success_url(self):
        if (not self.request.user.is_authenticated()) and defaults.PYBB_PREMODERATION:
            return reverse('noticeapp:index')
        return super(AddPostView, self).get_success_url()


class EditPostView(PostEditMixin, generic.UpdateView):

    model = Post

    context_object_name = 'post'
    template_name = 'noticeapp/edit_post.html'

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(EditPostView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super(EditPostView, self).get_form_kwargs()
        form_kwargs['may_create_poll'] = perms.may_create_poll(self.request.user)
        return form_kwargs

    def get_object(self, queryset=None):
        post = super(EditPostView, self).get_object(queryset)
        if not perms.may_edit_post(self.request.user, post):
            raise PermissionDenied
        return post


class UserView(generic.DetailView):
    model = User
    template_name = 'noticeapp/user.html'
    context_object_name = 'target_user'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, **{username_field: self.kwargs['username']})

    def get_context_data(self, **kwargs):
        ctx = super(UserView, self).get_context_data(**kwargs)
        ctx['course_count'] = Course.objects.filter(user=ctx['target_user']).count()
        return ctx


class UserPosts(PaginatorMixin, generic.ListView):
    model = Post
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    template_name = 'noticeapp/user_posts.html'

    def dispatch(self, request, *args, **kwargs):
        username = kwargs.pop('username')
        self.user = get_object_or_404(**{'klass': User, username_field: username})
        return super(UserPosts, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(UserPosts, self).get_queryset()
        qs = qs.filter(user=self.user)
        qs = perms.filter_posts(self.request.user, qs).select_related('course')
        qs = qs.order_by('-created', '-updated', '-id')
        return qs

    def get_context_data(self, **kwargs):
        context = super(UserPosts, self).get_context_data(**kwargs)
        context['target_user'] = self.user
        return context





class PostView(RedirectToLoginMixin, generic.RedirectView):

    def get_login_redirect_url(self):
        return reverse('noticeapp:post', args=(self.kwargs['pk'],))

    def get_redirect_url(self, **kwargs):
        post = get_object_or_404(Post.objects.all(), pk=self.kwargs['pk'])
        if not perms.may_view_post(self.request.user, post):
            raise PermissionDenied
        count = post.course.posts.filter(created__lt=post.created).count() + 1
        page = math.ceil(count / float(defaults.PYBB_TOPIC_PAGE_SIZE))
        return '%s?page=%d#post-%d' % (reverse('noticeapp:course', args=[post.course.id]), page, post.id)


class ModeratePost(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if not perms.may_moderate_course(self.request.user, post.course):
            raise PermissionDenied
        post.on_moderation = False
        post.save()
        return post.get_absolute_url()


class ProfileEditView(generic.UpdateView):

    template_name = 'noticeapp/edit_profile.html'

    def get_object(self, queryset=None):
        return util.get_noticeapp_profile(self.request.user)

    def get_form_class(self):
        if not self.form_class:
            from noticeapp.forms import EditProfileForm
            return EditProfileForm
        else:
            return super(ProfileEditView, self).get_form_class()

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(ProfileEditView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('noticeapp:edit_profile')


class DeletePostView(generic.DeleteView):

    template_name = 'noticeapp/delete_post.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post.objects.select_related('course', 'course__notice'), pk=self.kwargs['pk'])
        if not perms.may_delete_post(self.request.user, post):
            raise PermissionDenied
        self.course = post.course
        self.notice = post.course.notice
        if not perms.may_moderate_course(self.request.user, self.course):
            raise PermissionDenied
        return post

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        redirect_url = self.get_success_url()
        if not request.is_ajax():
            return HttpResponseRedirect(redirect_url)
        else:
            return HttpResponse(redirect_url)

    def get_success_url(self):
        try:
            Course.objects.get(pk=self.course.id)
        except Course.DoesNotExist:
            return self.notice.get_absolute_url()
        else:
            if not self.request.is_ajax():
                return self.course.get_absolute_url()
            else:
                return ""


class CourseActionBaseView(generic.View):

    def get_course(self):
        return get_object_or_404(Course, pk=self.kwargs['pk'])

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        self.course = self.get_course()
        self.action(self.course)
        return HttpResponseRedirect(self.course.get_absolute_url())


class StickCourseView(CourseActionBaseView):

    def action(self, course):
        if not perms.may_stick_course(self.request.user, course):
            raise PermissionDenied
        course.sticky = True
        course.save()


class UnstickCourseView(CourseActionBaseView):

    def action(self, course):
        if not perms.may_unstick_course(self.request.user, course):
            raise PermissionDenied
        course.sticky = False
        course.save()


class CloseCourseView(CourseActionBaseView):

    def action(self, course):
        if not perms.may_close_course(self.request.user, course):
            raise PermissionDenied
        course.closed = True
        course.save()


class OpenCourseView(CourseActionBaseView):
    def action(self, course):
        if not perms.may_open_course(self.request.user, course):
            raise PermissionDenied
        course.closed = False
        course.save()


class CoursePollVoteView(generic.UpdateView):
    model = Course
    http_method_names = ['post', ]
    form_class = PollForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CoursePollVoteView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        kwargs['course'] = self.object
        return kwargs

    def form_valid(self, form):
        # already voted
        if not perms.may_vote_in_course(self.request.user, self.object) or \
           not noticeapp_course_poll_not_voted(self.object, self.request.user):
            return HttpResponseForbidden()

        answers = form.cleaned_data['answers']
        for answer in answers:
            # poll answer from another course
            if answer.course != self.object:
                return HttpResponseBadRequest()

            PollAnswerUser.objects.create(poll_answer=answer, user=self.request.user)
        return super(ModelFormMixin, self).form_valid(form)

    def form_invalid(self, form):
        return redirect(self.object)

    def get_success_url(self):
        return self.object.get_absolute_url()


@login_required
def course_cancel_poll_vote(request, pk):
    course = get_object_or_404(Course, pk=pk)
    PollAnswerUser.objects.filter(user=request.user, poll_answer__course_id=course.id).delete()
    return HttpResponseRedirect(course.get_absolute_url())


@login_required
def delete_subscription(request, course_id):
    course = get_object_or_404(perms.filter_courses(request.user, Course.objects.all()), pk=course_id)
    course.subscribers.remove(request.user)
    return HttpResponseRedirect(course.get_absolute_url())


@login_required
def add_subscription(request, course_id):
    course = get_object_or_404(perms.filter_courses(request.user, Course.objects.all()), pk=course_id)
    course.subscribers.add(request.user)
    return HttpResponseRedirect(course.get_absolute_url())


@login_required
def post_ajax_preview(request):
    content = request.POST.get('data')
    html = defaults.PYBB_MARKUP_ENGINES[defaults.PYBB_MARKUP](content)
    return render(request, 'noticeapp/_markitup_preview.html', {'html': html})


@login_required
def mark_all_as_read(request):
    for notice in perms.filter_notices(request.user, Notice.objects.all()):
        notice_mark, new = NoticeReadTracker.objects.get_or_create_tracker(notice=notice, user=request.user)
        notice_mark.save()
    CourseReadTracker.objects.filter(user=request.user).delete()
    msg = _('All notices marked as read')
    messages.success(request, msg, fail_silently=True)
    return redirect(reverse('noticeapp:index'))


@login_required
@require_POST
def block_user(request, username):
    user = get_object_or_404(User, **{username_field: username})
    if not perms.may_block_user(request.user, user):
        raise PermissionDenied
    user.is_active = False
    user.save()
    if 'block_and_delete_messages' in request.POST:
        # individually delete each post and empty course to fire method
        # with notice/course counters recalculation
        posts = Post.objects.filter(user=user)
        courses = posts.values('course_id').distinct()
        notices = posts.values('course__notice_id').distinct()
        posts.delete()
        Course.objects.filter(user=user).delete()
        for t in courses:
            try:
                Course.objects.get(id=t['course_id']).update_counters()
            except Course.DoesNotExist:
                pass
        for f in notices:
            try:
                Notice.objects.get(id=f['course__notice_id']).update_counters()
            except Notice.DoesNotExist:
                pass


    msg = _('User successfuly blocked')
    messages.success(request, msg, fail_silently=True)
    return redirect('noticeapp:index')


@login_required
@require_POST
def unblock_user(request, username):
    user = get_object_or_404(User, **{username_field: username})
    if not perms.may_block_user(request.user, user):
        raise PermissionDenied
    user.is_active = True
    user.save()
    msg = _('User successfuly unblocked')
    messages.success(request, msg, fail_silently=True)
    return redirect('noticeapp:index')

