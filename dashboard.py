from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.modules import DashboardModule

from profiles.forms import *

class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for Campus.
    """
    def __init__(self, **kwargs):
        Dashboard.__init__(self, **kwargs)
        
        self.children.append(modules.Group(
            column=1,
            title='CWSP',
            children=[
                modules.ModelList(
                    models=(
                        'work_study.models.StudentWorker',
                        'work_study.models.StudentInteraction',
                        'work_study.models.Attendance',
                        'work_study.models.PickupLocation',
                        'work_study.models.CraContact',
                        'work_study.models.Personality',
                        'work_study.models.Handout33',
                        'work_study.models.PresetComment',
                        'work_study.models.AttendanceFee',
                        'work_study.models.AttendanceReason',
                    ),
                ),
                modules.ModelList(
                    title="Company Data",
                    models=(
                        'work_study.models.Company',
                        'work_study.models.WorkTeam',
                        'work_study.models.WorkTeamUser',
                        'work_study.models.TimeSheet',
                        'work_study.models.TimeSheetPerformanceChoice',
                        'work_study.models.Contact',
                        'work_study.models.CompanyContract',
                        'work_study.models.CompanyHistory',
                        'work_study.models.ClientVisit',
                        'work_study.models.PaymentOption',
                        'work_study.models.StudentDesiredSkill',
                        'work_study.models.StudentFunctionalResponsibility',
                        'work_study.models.CompContract',
                        'work_study.models.MessageToSupervisor',
                    ),
                ),
            ]
        ))
        
        self.children.append(modules.ModelList(
            title=_('School Information'),
            column=1,
            models=(
                'profiles.models.SchoolYear',
                'profiles.models.Student',
                'profiles.models.EmergencyContact',
                'profiles.models.Cohort',
                'profiles.models.PerCourseCohort',
                'profiles.models.ReasonLeft',
                'profiles.models.Faculty',
                'profiles.models.MessageToStudent',
                'profiles.models.FamilyAccessUser',
            ),
        ))

        self.children.append(modules.ModelList(
            title=('Volunteer Tracking'),
            column=1,
            models=(
                'volunteer_track.*',
            ),
        ))

        self.children.append(modules.ModelList(
            title=_('Attendance'),
            column=1,
            models=('profiles.models.StudentAttendance',
                    'profiles.models.AttendanceStatus',
                    'profiles.models.ASPAttendance',
                ),
        ))
        
        self.children.append(modules.ModelList(
            title = 'Discipline',
            column=1,
            models=(
                'discipline.models.StudentDiscipline',
                'discipline.models.DisciplineAction',
                'discipline.models.PresetComment',
            ),
        ))
        
        self.children.append(modules.ModelList(
            title = 'Attendance',
            column=1,
            models=(
                'attendance.*',
            ),
        ))
    
        self.children.append(modules.ModelList(
            title='Courses and Grades',
            column=1,
            models=('schedule.*','grades.*','benchmark_grade.*','benchmarks.*'),
        ))
        
        self.children.append(modules.ModelList(
            title='Standard Tests',
            column=1,
            models=('standard_test.*',),
        ))
        
        self.children.append(modules.ModelList(
            title='Admissions',
            column=1,
            models=('admissions.*',),
        ))
        
        self.children.append(modules.ModelList(
            title='Counseling',
            column=1,
            models=('counseling.*',),
        ))
        
        self.children.append(modules.ModelList(
            title='Alumni',
            column=1,
            models=('alumni.*',),
        ))
        
        self.children.append(modules.ModelList(
            title='OpenMetricRecognition',
            column=1,
            models=('omr.*',),
        ))
        
        self.children.append(modules.AppList(
            title='Administration',
            column=2,
            models=(
                'django.contrib.*',
                'administration.*',
                'engrade_sync.*',
                'ldap_groups.*',
                'google_auth.*',
            )
        ))
        
        # append a recent actions module
        self.children.append(modules.RecentActions(
            title='Recent Actions',
            column=2,
            limit=5
        ))
        
        self.children.append(modules.LinkList(
            column=2,
            children=(
                {
                    'title': 'Campus Management Wiki and Manual',
                    'url': 'https://campusmgmt.readthedocs.org',
                    'external': True,
                },
                {
                    'title': 'Campus Management Code',
                    'url': 'http://no-source',
                    'external': True,
                },
                {
                    'title': 'Campus Management',
                    'url': 'http://campusmgmt.com',
                    'external': True,
                },
            )
        ))
