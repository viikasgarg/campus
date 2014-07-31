from django import forms
from django.forms.widgets import CheckboxSelectMultiple, TextInput
from django.contrib.auth.models import User
from localflavor.us.forms import *

from .models import *
from schedule.models import MarkingPeriod

class SetupCoursesForm(forms.Form):
    marking_period = forms.ModelChoiceField(MarkingPeriod.objects.all())
    
class GradeSyncForm(forms.Form):
    marking_period = forms.ModelChoiceField(MarkingPeriod.objects.all())
    teachers = forms.ModelMultipleChoiceField(Faculty.objects.filter(is_active=True,teacher=True))
    include_comments = forms.BooleanField(required=False,initial=True)
