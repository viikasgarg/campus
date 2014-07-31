#   Copyright 2010-2011 Burke Software and Consulting LLC
#   Author David M Burke <david@burkesoftware.com>
#   
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#     
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#      
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#   MA 02110-1301, USA.

from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings

from profiles.models import Student, Faculty

import datetime

class DisciplineAction(models.Model):
    name = models.CharField(max_length=255, unique=True)
    major_offense = models.BooleanField(default=False, 
        help_text="This can be filtered by Grade Analytics and other reports.")
    
    def __unicode__(self): 
        return unicode(self.name)


class DisciplineActionInstance(models.Model):
    action = models.ForeignKey(DisciplineAction)
    student_discipline = models.ForeignKey('StudentDiscipline')
    quantity = models.IntegerField(default=1)
    def __unicode__(self): 
        return unicode(self.action) + " (" + unicode(self.quantity) + ")"


class Infraction(models.Model):
    """ Infractions are things like  """
    comment = models.CharField(
        max_length=255,
        help_text='If comment is "Case note" these infractions will not be counted as a discipline issue in reports')
    
    def __unicode__(self):
        if len(self.comment) < 42:
            return self.comment
        else:
            return unicode(self.comment[:42]) + ".."
        
    def all_actions(self):
        ordering = ('comment',)


class StudentDiscipline(models.Model):
    students = models.ManyToManyField(Student, limit_choices_to={'is_active': True})
    date = models.DateField(default=datetime.datetime.today, validators=settings.DATE_VALIDATORS)
    infraction = models.ForeignKey(Infraction, blank=True, null=True)
    action = models.ManyToManyField(DisciplineAction, through='DisciplineActionInstance')
    comments = models.TextField(blank=True)
    private_note = models.TextField(blank=True)
    teacher = models.ForeignKey(Faculty, blank=True, null=True)
    
    def show_students(self):
        if self.students.count() == 1:
            return self.students.all()[0]
        elif self.students.count() > 1:
            return "Multiple students"
        else:
            return None
    show_students.short_description = "Students"

    def comment_brief(self):
        return self.comments[:100]
     
    class Meta:
        ordering = ('-date',)
        
    def __unicode__(self):
        if self.students.count() == 1:
            stu = self.students.all()[0]
            return unicode(stu) + " " + unicode(self.date)
        return "Multiple Students " + unicode(self.date)
    
    def all_actions(self):
        action = ""
        for a in self.disciplineactioninstance_set.all():
            action += unicode(a) + " "
        return action
    
    def get_active(self):
        """Returns all active discipline records for the school year. 
        If schedule is not installed it returns all records
        Does not return case notes"""
        try:
            school_start = SchoolYear.objects.get(active_year=True).start_date
            school_end = SchoolYear.objects.get(active_year=True).end_date
            case_note = PresetComment.objects.get(comment="Case note")
            return StudentDiscipline.objects.filter(date__range=(school_start, school_end)).exclude(infraction=case_note)
        except:
            case_note = PresetComment.objects.get(comment="Case note")
            return StudentDiscipline.objects.all().exclude(infraction=case_note)
