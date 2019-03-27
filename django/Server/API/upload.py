# encoding: utf-8
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import base64
from urllib import quote
import time
import hashlib   
import sys
import settings
reload(sys)
sys.setdefaultencoding('utf8')  

def md5name(name):
    arr = name.split(".")
    tmp = name.split(";")
#    tmp = "quote(str(name))" + str(time.time())
    m2 = hashlib.md5()   
    m2.update(tmp[1])
    return m2.hexdigest() + ".jpg"
# tmp[0].split("/")[1]
    
def upload_POST(request):
    myFile = request.POST.get("file")
   # print myFile
    if not myFile: 
        return HttpResponse("no files for upload!") 
    fileName = md5name(myFile)
    print myFile.split(",")[1]
    
    with open(os.path.join(settings.BASE_DIR,"static/image",fileName),'wb+') as f:
        f.write(base64.b64decode(myFile.split(",")[1]))
    #destination = open(os.path.join(settings.BASE_DIR,"static/image",fileName),'wb+')
    #for chunk in myFile.chunks():
    #    destination.write(chunk) 
    #destination.close() 
    resp = {'code': 200, 'data': {'fileName': fileName} }
    return HttpResponse(json.dumps(resp), content_type="application/json")

@csrf_exempt
def upload(request):
    if request.method == "POST":
        return upload_POST(request)
    else:
        return HttpResponse("Hello world ! ")
