import numpy as np
from PIL import Image

import caffe
import vis
import time
import os

print os.path

caffe.set_device(0)
caffe.set_mode_gpu()

# load net
# net = caffe.Net('Server/FCN/voc-fcn8s/deploy.prototxt', 'Server/FCN/voc-fcn8s/fcn8s-heavy-pascal.caffemodel', caffe.TEST)
#net = caffe.Net('voc-fcn32s/deploy.prototxt', 'voc-fcn32s/fcn32s-heavy-pascal.caffemodel', caffe.TEST)
#net = caffe.Net('voc-fcn-alexnet/deploy.prototxt', 'voc-fcn-alexnet/fcn-alexnet-pascal.caffemodel', caffe.TEST)

# the demo image is "2007_000129" from PASCAL VOC

def modifySize(im):
    width, height = im.size
    if (width < 500 and height < 500):
	return im
    if (width > height):
        tmp = width / 500.0
        return im.resize((500, int(height/tmp)), Image.ANTIALIAS)
    else:
        tmp = height / 500.0
        return im.resize((int(width/tmp), 500), Image.ANTIALIAS)

def segment(img):
    # load image, switch to BGR, subtract mean, and make dims C x H x W for Caffe
    print "start"
    im = modifySize(Image.open(img))
    in_ = np.array(im, dtype=np.float32)
    in_ = in_[:,:,::-1]
    in_ -= np.array((104.00698793,116.66876762,122.67891434))
    in_ = in_.transpose((2,0,1))

    net = caffe.Net('Server/FCN/voc-fcn8s/deploy.prototxt', 'Server/FCN/voc-fcn8s/fcn8s-heavy-pascal.caffemodel', caffe.TEST)

    time_start=time.time()
    # shape for input (data blob is N x C x H x W), set data
    net.blobs['data'].reshape(1, *in_.shape)
    net.blobs['data'].data[...] = in_
    # run net and take argmax for prediction
    print "forward"
    net.forward()
    out = net.blobs['score'].data[0].argmax(axis=0)
    
    print "end forward"
    # visualize segmentation in PASCAL VOC colors
    voc_palette = vis.make_palette(21)
    out_im = Image.fromarray(vis.color_seg(out, voc_palette))
    time_end=time.time()
    print('totally cost',time_end-time_start)
    imgNames = img.split('.')
    output = os.path.join("./static/image",imgNames[0] + "output.png")
    out_im.save(output)
    masked_im = Image.fromarray(vis.vis_seg(im, out, voc_palette))
    visualization = output = os.path.join("./static/image",imgNames[0] + "visualization.jpg")
    masked_im.save(visualization)
