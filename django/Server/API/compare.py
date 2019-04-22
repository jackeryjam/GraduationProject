from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import sys
sys.path.append("./Server")
import settings
import numpy as np
from PIL import Image

def phash(img):
    img = img.resize((8, 8), Image.ANTIALIAS).convert('L')
    avg = reduce(lambda x, y: x + y, img.getdata()) / 64.
    return reduce(
        lambda x, (y, z): x | (z << y),
        enumerate(map(lambda i: 0 if i < avg else 1, img.getdata())),
        0
    )

def hamming_distance(a, b):
    return bin(a^b).count('1')

def distance(img1,img2):
    return hamming_distance(phash(img1),phash(img2))

def compare_POST(request):
    resp = {'code': 200, 'data': 'Post image'}
    return HttpResponse(json.dumps(resp), content_type="application/json")

def compare_GET(request):
    resp = {'code': 200, 'data': 'Get Image'}
    data = request.GET
    img1 = "static/image/" + data.get("img1")
    img2 = "static/image/" + data.get("img2")
    im1 = Image.open(img1)
    im2 = Image.open(img2)
    resp = {'code': 200, 'data': {'distance': distance(im1, im2)}}
    return HttpResponse(json.dumps(resp), content_type="application/json")

@csrf_exempt
def compare(request):
    if request.POST:
        return compare_POST(request)
    else:
        return compare_GET(request)
