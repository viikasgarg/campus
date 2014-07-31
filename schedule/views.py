from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from profiles.models import *
from profiles.uno_report import *
from schedule.models import *
from schedule.forms import *
from administration.models import *

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from datetime import date

class struct(): pass

@user_passes_test(lambda u: u.groups.filter(name='faculty').count() > 0 or u.is_superuser, login_url='/')
def schedule(request):
    years = SchoolYear.objects.all().order_by('-start_date')[:3]
    mps = MarkingPeriod.objects.all().order_by('-start_date')[:12]
    periods = Period.objects.all()[:20]
    courses = Course.objects.all().order_by('-startdate')[:20]

    if SchoolYear.objects.count() > 2: years.more = True
    if MarkingPeriod.objects.count() > 3: mps.more = True
    if Period.objects.count() > 6: periods.more = True
    if Course.objects.count() > 6: courses.more = True

    return render_to_response('schedule/schedule.html', {'request': request, 'years': years, 'mps': mps, 'periods': periods, 'courses': courses})

@user_passes_test(lambda u: u.groups.filter(name='faculty').count() > 0 or u.is_superuser, login_url='/')
def schedule_enroll(request, id):
    course = get_object_or_404(Course, pk=id)
    if request.method == 'POST':
        form = EnrollForm(request.POST)
        if form.is_valid():
            CourseEnrollment.objects.filter(course=course, role='student').delete() # start afresh; only students passed in from the form should be enrolled
            # add manually select students first
            selected = form.cleaned_data['students']
            for student in selected:
                # add
                enroll, created = CourseEnrollment.objects.get_or_create(user=student, course=course, role="student")
                # left get_or_create in case another schedule_enroll() is running simultaneously
                if created: enroll.save()
            # add cohort students second
            cohorts = form.cleaned_data['cohorts']
            for cohort in cohorts:
                for student in cohort.student_set.all():
                    enroll, created = CourseEnrollment.objects.get_or_create(user=student, course=course, role="student")

            if 'save' in request.POST:
                return HttpResponseRedirect(reverse('admin:schedule_course_change', args=[id]))

    students = Student.objects.filter(courseenrollment__course=course)
    form = EnrollForm(initial={'students': students})
    return render(request, 'schedule/enroll.html', {'request': request, 'form': form, 'course': course})

class CourseMeetListView(ListView):
    model = CourseMeet
    paginate_by = 20

    def get_queryset(self):
        return CourseMeet.objects.filter(course__teacher=self.request.user)

class CourseMeetDeleteView(DeleteView):
    model = CourseMeet

    def get_object(self, queryset=None):
        """ Only Teacher of course has the right to delete course meet request.user. """
        obj = super(CourseMeetDeleteView, self).get_object()
        #assert False
        if  obj.course.teacher.id != self.request.user.id:
            raise Http404
        return obj

    def get_success_url(self):
        return reverse("schedule:period:list", args=(1,))


class CourseMeetCreateView(CreateView):
    model = CourseMeet
    form_class = CourseMeetForm

    # add the user to the kwargs
    def get_form_kwargs(self):
        kwargs = super(CourseMeetCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("schedule:period:list", args=(1,))


class CourseMeetUpdateView(UpdateView):
    model = CourseMeet
    form_class = CourseMeetForm

    # add the request to the kwargs
    def get_form_kwargs(self):
        kwargs = super(CourseMeetUpdateView, self).get_form_kwargs()
        obj = super(CourseMeetUpdateView, self).get_object()
        if obj.course.teacher.id != self.request.user.id:
            raise Http404
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("schedule:period:list", args=(1,))

class CourseListView(ListView):
    model = Course
    paginate_by = 20

    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user)


class CourseEnrollmentListView(ListView):
    model = CourseEnrollment
    paginate_by = 20

    def get_queryset(self):
        return CourseEnrollment.objects.filter(user=self.request.user, course__active=True)

class StudentCourseMeetListView(ListView):
    model = CourseMeet
    paginate_by = 20
    template_name = 'schedule/studentcoursemeet_list.html'

    def get_queryset(self):
        courses = [c.course.id for c in CourseEnrollment.objects.filter(user=self.request.user, course__active=True)]
        return CourseMeet.objects.filter(course__in=courses)

class TodayCourseMeetListView(ListView):
    model = CourseMeet
    paginate_by = 20
    template_name = 'schedule/today_classes.html'

    def get_queryset(self):
        courses = [c.course.id for c in CourseEnrollment.objects.filter(user=self.request.user, course__active=True)]
        return CourseMeet.objects.filter(course__in=courses, day=date.today().weekday())
