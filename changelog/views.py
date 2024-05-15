from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from .forms import ChangelogForm
from .models import PatchNote
from django.contrib import messages
from django.shortcuts import render
from utils.users import getUser
from utils.views import buildBaseContext


def index(request):
    user = request.user
    if request.method == "POST":
        form = ChangelogForm(request.POST)
        if form.is_valid():
            title = request.POST['title']
            version = request.POST['version']
            joke_note = request.POST['joke_note']
            date = request.POST['date']
            notes = request.POST['notes'].split('&&&')

            patch_note = PatchNote(
                title = title,
                version = version,
                notes = notes,
                date = date,
                joke_note = joke_note,
            )
            patch_note.save()
            messages.success(request, "Added new patch notes!")
            return HttpResponseRedirect(reverse('changelog:index'))

    changelog = PatchNote.objects.all().order_by('-date')
    versions = changelog.values("version", "title")

    ctx = {
        'form': ChangelogForm(),
        'versions': versions,
        'changelog': changelog,
    }
    ctx.update(buildBaseContext(user))
    
    return render(request, "changelog/index.html", context=ctx)