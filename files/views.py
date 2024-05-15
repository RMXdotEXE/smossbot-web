from .forms import UploadForm
from .models import UploadedFile
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.http import HttpRequest, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response as RESTResponse
from utils import views


def index(request):
    user = request.user
    if request.method == "POST":
        upload_form = UploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            doc = UploadedFile(
                file = request.FILES['file'],
                user = user,
                tag = request.POST['tag']
            )
            doc.save()
            messages.success(request, "Uploaded file successfully!")
            return HttpResponseRedirect(reverse('files:index'))
        else:
            errors = upload_form.errors.get_json_data()
            listed_errors = ''.join([fielddata[0]['message'] for fielddata in errors.values()])
            messages.error(request, "Error occured uploading: {}.".format(listed_errors))
    
    uploaded_files = UploadedFile.objects.filter(user=user).order_by('upload_date')
    max_uploads = False
    if len(uploaded_files) >= 10:
        max_uploads = True

    ctx = views.buildBaseContext(user)
    ctx.update({
        'form': UploadForm(), 
        'maxuploads': max_uploads, 
        'uploaded_files': uploaded_files
    })

    return render(request, "files/index.html", context=ctx)


@api_view(["GET", "PATCH", "DELETE"])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def files(request, format=None):
    if request.method == "GET":
        uploaded_files = UploadedFile.objects.filter(user=request.user).order_by('upload_date')
        return RESTResponse(data={'uploaded_files': uploaded_files}, template_name="files/file_viewer.html")
    if request.method == "PATCH":
        file_id = request.data.get("fileID", None)
        new_tag = request.data.get("tag", None)
        if None in [file_id, new_tag]:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        try:
            alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
            alphanumeric(new_tag)
        except ValidationError:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        file = UploadedFile.objects.filter(user=request.user, id=file_id).first()
        file.tag = new_tag
        file.save()
        return RESTResponse(status=status.HTTP_200_OK)
    if request.method == "DELETE":
        file_id = request.data.get("fileID", None)
        if file_id is None:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        file = UploadedFile.objects.filter(user=request.user, id=file_id).first()
        file.delete()
    return RESTResponse(status=status.HTTP_204_NO_CONTENT)



