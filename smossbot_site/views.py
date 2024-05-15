from django.contrib.auth import logout as _logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from utils.views import buildBaseContext


def home(request):
    return render(request, "home.html", context=buildBaseContext(request.user))


def gatekept(request):
    return render(request, "gatekept.html", context=buildBaseContext(request.user))


def commands(request):
    return render(request, "commands.html", context=buildBaseContext(request.user))


def about(request):
    return render(request, "about.html", context=buildBaseContext(request.user))


def logout(request):
    _logout(request)
    return HttpResponseRedirect(reverse('home'))