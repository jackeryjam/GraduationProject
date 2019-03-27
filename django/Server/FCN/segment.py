import numpy as np
from PIL import Image

import caffe
import vis
import time
import os
#import sys
#sys.path.append("./Server/FCN")

net = caffe.Net('Server/FCN/voc-fcn8s/deploy.prototxt', 'Server/FCN/voc-fcn8s/fcn8s-heavy-pascal.caffemodel', caffe.TEST)

def modifySize(im):
    maxSize = 400
    width, height = im.size
    if (width < maxSize and height < maxSize):
	return im
    if (width > height):
        tmp = width / float(maxSize)
        return im.resize((maxSize, int(height/tmp)), Image.ANTIALIAS)
    else:
        tmp = height / float(maxSize)
        return im.resize((int(width/tmp), maxSize), Image.ANTIALIAS)

#caffe.set_device(0)
#caffe.set_mode_gpu()

# the demo image is "2007_000129" from PASCAL VOC

# load image, switch to BGR, subtract mean, and make dims C x H x W for Caffe
def segment(img):
    time_start=time.time()
    caffe.set_device(0)
    caffe.set_mode_gpu()
    im = modifySize(Image.open(img))
    if (im.mode == "RGBA"):
        im = im.convert("RGB")
    in_ = np.array(im, dtype=np.float32)
    in_ = in_[:,:,::-1]
    in_ -= np.array((104.00698793,116.66876762,122.67891434))
    in_ = in_.transpose((2,0,1))

    # load net
    #net = caffe.Net('Server/FCN/voc-fcn8s/deploy.prototxt', 'Server/FCN/voc-fcn8s/fcn8s-heavy-pascal.caffemodel', caffe.TEST)
    # shape for input (data blob is N x C x H x W), set data
    net.blobs['data'].reshape(1, *in_.shape)
    net.blobs['data'].data[...] = in_
    # run net and take argmax for prediction
    net.forward()
    out = net.blobs['score'].data[0].argmax(axis=0)

    # visualize segmentation in PASCAL VOC colors
    voc_palette = vis.make_palette(21)
    out_im = Image.fromarray(vis.color_seg(out, voc_palette))
    imgNames = img.split('.')
    output = os.path.join("./static/image",imgNames[0] + ".output.png")
    out_im.save(output)
    masked_im = Image.fromarray(vis.vis_seg(im, out, voc_palette))
    visualization = os.path.join("./static/image",imgNames[0] + ".vis.jpg")
    masked_im.save(visualization)
    time_end=time.time()
    print('totally cost',time_end-time_start)
    return time_end-time_start
