from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

def segment_POST(request):
    resp = {'code': 200, 'data': 'Get success'}
    return HttpResponse(json.dumps(resp), content_type="application/json")

@csrf_exempt
def segment(request):
    if request.POST:
        return segment_POST(request)
    else:
        return HttpResponse("Hello world ! ")