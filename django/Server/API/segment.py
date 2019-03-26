# encoding: utf-8
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from Server.FCN.segment import segment as caffeSegment
import os
from Server import settings
 
import sys
reload(sys)
sys.setdefaultencoding('utf8')  

def segment_POST(request):
    resp = {'code': 200, 'data': 'Get success'}
    return HttpResponse(json.dumps(resp), content_type="application/json")

def segment_GET(request):
    image = request.GET.get('image')  
    caffeSegment(os.path.join(settings.BASE_DIR,"static/image",image))
    resp = {'code': 200, 'data': 'Get success'}
    return HttpResponse(json.dumps(resp), content_type="application/json")

@csrf_exempt
def segment(request):
    print request
    if request.method == "POST":
        return segment_POST(request)
    else:
 	return segment_GET(request)
