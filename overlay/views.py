from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.shortcuts import render

# Create your views here.
def process_req(request, user_hash):
    if request.method == "POST":
        return JsonResponse(request.method, user_hash)
    else:
        return render(request, "overlay/ytoverlay.html", context={'username': user_hash})