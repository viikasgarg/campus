from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from datetime import datetime, time
from schedule.models import CourseMeet, CourseEnrollment
@dajaxice_register
def classes(request,dates):
    selected_dates =[]
    for date in dates.split(","):
        selected_dates.append(datetime.strptime(date, "%m/%d/%Y").weekday())
    courses = [c.course.id for c in CourseEnrollment.objects.filter(user=request.user, course__active=True)]
    coursemeets = CourseMeet.objects.filter(course__in=courses, day__in=selected_dates)

    meetups = []
    days=['Monday', 'Tuesday', 'Wednesday',
          'Thursday', 'Friday', 'Saturday',
           'Sunday']
    for coursemeet in coursemeets:
        meetup = {}
        meetup['courses'] = coursemeet.course.fullname
        meetup['time'] = coursemeet.start_time.strftime('%I:%M %p') + " - " + coursemeet.end_time.strftime('%I:%M %p')
        meetup['location'] = coursemeet.location.name
        meetup['day'] = days[int(coursemeet.day)%7]
        meetups.append(meetup)
    print simplejson.dumps(meetups)
    return simplejson.dumps(meetups)
