from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os

def upload_POST(request):
    print request
    myFile =request.FILES.get("myfile")
    print myFile
    if not myFile: 
        return HttpResponse("no files for upload!") 
    destination = open(os.path.join("./static/image",myFile.name),'wb+')
    for chunk in myFile.chunks():
        destination.write(chunk) 
    destination.close() 
    resp = {'code': 200, 'data': 'upload over!'}
    return HttpResponse(json.dumps(resp), content_type="application/json")

@csrf_exempt
def upload(request):
    print "upload--------------"
    if request.method == "POST":
        print "POST--------------"
        return upload_POST(request)
    else:
        print "GET--------------"
        return HttpResponse("Hello world ! ")