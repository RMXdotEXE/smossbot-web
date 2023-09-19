import os

from django.http import JsonResponse
from django.shortcuts import render


# Create your views here.
def process_req(request, user_hash):
    url = None
    if os.getenv('DEBUG') == "True":
        url = "ws://localhost:5000/ws"
    else:
        url = "wss://www.smossbot.com:5000/ws"

    if request.method == "POST":
        return JsonResponse(request.method, user_hash)
    
    ctx = {
        'username': user_hash,
        'url': url,
    }
        
    return render(request, "overlay/overlay.html", context=ctx)