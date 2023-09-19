import re

class UsernameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        username = None

        match = re.match(r'^/([^/]+)/dashboard/', request.path)

        if match:
            username = match.group(1)

        request.username = username
        return self.get_response(request)