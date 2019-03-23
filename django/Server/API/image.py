from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import sys
sys.path.append("./Server")
import settings

def image_POST(request):
    resp = {'code': 200, 'data': 'Post image'}
    return HttpResponse(json.dumps(resp), content_type="application/json")

def image_GET(request):
    resp = {'code': 200, 'data': 'Get Image'}
    try:
        data = request.GET
        file_name = data.get("img")
        imagepath = os.path.join(settings.BASE_DIR, "image/{}".format(file_name))
        print imagepath
        with open(imagepath, 'rb') as f:
            image_data = f.read()
        return HttpResponse(image_data, content_type="image/png")
    except Exception as e:
        return HttpResponse(str(e))

@csrf_exempt
def image(request):
    if request.POST:
        return segment_POST(request)
    else:
        return image_GET(request)