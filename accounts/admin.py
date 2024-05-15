from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import TwitchUser

admin.site.register(TwitchUser, UserAdmin)