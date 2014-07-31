from responsive_dashboard.dashboard import Dashboard, Dashlet, ListDashlet, RssFeedDashlet, AdminListDashlet, dashboards
from .models import Course, MarkingPeriod
import datetime

class CourseDashlet(ListDashlet):
    model = Course
    fields = ('__str__', 'number_of_students',)
    order_by = ('-marking_period__start_date',)
    require_apps = ('schedule',)


class GradesDashlet(Dashlet):
    template_name = 'schedule/grade_dashlet.html'
    require_apps = ('grades',)
    require_permissions_or = ('grades.check_own_grade', 'grades.change_grade',)

    def get_context_data(self, **kwargs):
        context = super(GradesDashlet, self).get_context_data(**kwargs)
        today = datetime.date.today()
        marking_periods = MarkingPeriod.objects.filter(end_date__gte=today).order_by('start_date')
        if marking_periods:
            marking_period = marking_periods[0]
            due_in = (marking_period.end_date - today).days
        else:
            due_in = None
        context['due_in'] = due_in
        return context


class CourseDashboard(Dashboard):
    app = 'schedule'
    dashlets = [
        CourseDashlet(title="Courses"),
        GradesDashlet(title="Grades"),
        AdminListDashlet(title="Schedule", app_label="schedule"),
        AdminListDashlet(title="GradesList", verbose_name="Grades", app_label="grades"),
    ]

dashboards.register('schedule', CourseDashboard)
