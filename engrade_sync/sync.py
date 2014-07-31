#       Copyright 2011 David M Burke <david@davidmburke.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from engrade_sync.python_engrade import *
from engrade_sync.models import *

class EngradeSync:
    def __init__(self):
        """ Login and get session from Engrade """
        self.api = PythonEngrade()
        
    def get_engrade_teacher(self, teacher):
        """ Get an engrade teacher id, create if non existant
        teacher: sis.models.Faculty
        returns teacher's engrade id """
        teacher_sync = TeacherSync.objects.filter(teacher=teacher)
        if not teacher_sync.count():
            pass # Must figure out user creation first
        return teacher_sync.engrade_teacher_id 
        
    def get_engrade_course(self, course, marking_period):
        """ Get an engrade course id, create if non existant. Creates teacher if
        non existant.
        course: schedule.models.Course
        marking_period: unlike SWORD, engrade considers different marking
        periods as different courses
        returns engrade course id"""
        course_sync = CourseSync.objects.filter(course=course, marking_period=marking_period)
        if not course_sync.count():
            name = course.fullname
            syr = course.marking_period.all()[0].school_year.name
            # Figure out gp by determining the order in which the SWORD marking
            # periods occure
            gp = 0
            for mp in course.marking_period.order_by('start_date'):
                gp += 1
                if mp == marking_period:
                    break
            students = ""
            for student in Student.objects.filter(courseenrollment__course=course):
                students += "%s %s %s\n" % (student.fname, student.lname, student.id)
            priteach = self.get_engrade_teacher(course.teacher)
            engrade_id = self.api.schoolclassnew(name, syr, gp, students, priteach)
            course_sync = CourseSync(sword_course=course, engrade_course=engrade_id)
            course_sync.save()
        return course_sync.engrade_teacher_id 
