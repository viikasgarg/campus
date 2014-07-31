from django.template import RequestContext,loader
from main.forms import LoginForm
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, get_user
from django.contrib.auth.models import User
from django.shortcuts import redirect

def homepage(request,user):
    if len(user.groups.filter(name='students')) > 0:
        return redirect('/profiles/student/home')
        ## redirect to student home
        print "user is valid and active"
    if len(user.groups.filter(name='faculty')) > 0:
        return redirect('/profiles/prof/home')
        ## redirect to prof home
        print "user is valid and active"
    if request.user.is_superuser:
        print "redirect to admin"
        return redirect('/administration/dashboard/')

def home(request):
    # This view is missing all form handling logic for simplicity of the example
    if "POST" == request.method:
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return homepage(request,user)
                else:
                    print "password is valid but account is disabled"
            else:
                print "username and password are incorrect"
    else:
        if request.user.is_authenticated():
            user = get_user(request)

            return homepage(request,user)
        login_form = LoginForm()


    #if 'GET' == request.method:
    t = loader.get_template('main.html')
    c = RequestContext(request,{'login_form': login_form,})
    resp = t.render(c)

    return HttpResponse(resp)

