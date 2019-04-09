import caffe
from caffe import layers as L, params as P
from caffe.coord_map import crop

def conv_relu(bottom, nout, ks=3, stride=1, pad=1, freeze=False):
    param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)]
    if (freeze == True):
        param=[dict(lr_mult=0, decay_mult=0), dict(lr_mult=0, decay_mult=0)]
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad,
        param=param)
    return conv, L.ReLU(conv, in_place=True)

def conv_BN_scale(bottom, nout, ks=3, stride=1, pad=1, freeze=False):
    param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)]
    if (freeze == True):
        param=[dict(lr_mult=0, decay_mult=0), dict(lr_mult=0, decay_mult=0)]
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
    num_output=nout, pad=pad, bias_term=False, param=param,
    weight_filler=dict(type="msra") )
    return conv, L.BatchNorm(conv, in_place=True), L.Scale(conv, in_place=True, bias_term=True)

def conv_BN_scale_relu(bottom, nout, ks=3, stride=1, pad=1, freeze=False):
    param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)]
    if (freeze == True):
        param=[dict(lr_mult=0, decay_mult=0), dict(lr_mult=0, decay_mult=0)]
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad, bias_term=False,
        weight_filler=dict(type="msra"), param=param)
    return conv, L.BatchNorm(conv, in_place=True), L.Scale(conv, in_place=True, bias_term=True), L.ReLU(conv, in_place=True)

def max_pool(bottom, ks=2, stride=2):
    return L.Pooling(bottom, pool=P.Pooling.MAX, kernel_size=ks, stride=stride)

def createEncoder(n, name, bottom, nout, stride=1, pad=1, freeze=False):
    prefix = name + "a_branch1"
    n[prefix], n[prefix.replace("res","bn")], n[prefix.replace("res","scale")] = conv_BN_scale(bottom, nout, 1, stride=stride, pad=0, freeze=freeze)

    prefix_a = name + "a_branch2a"
    n[prefix_a], n[prefix_a.replace("res","bn")], n[prefix_a.replace("res","scale")], n[prefix_a+"_relu"] = conv_BN_scale_relu(bottom, nout, stride=stride)
    prefix_b = name + "a_branch2b"
    n[prefix_b], n[prefix_b.replace("res","bn")], n[prefix_b.replace("res","scale")] = conv_BN_scale(n[prefix_a+"_relu"], nout)

    n[name+"a"] = L.Eltwise(n[prefix.replace("res","scale")], n[prefix_b.replace("res","scale")], operation=P.Eltwise.SUM)
    n[name+"a_relu"] = L.ReLU(n[name+"a"], in_place=True)

    prefix2_a = name + "b_branch2a"
    n[prefix2_a], n[prefix2_a.replace("res","bn")], n[prefix2_a.replace("res","scale")], n[prefix2_a+"_relu"] = conv_BN_scale_relu(n[name+"a_relu"], nout)
    prefix2_b = name + "b_branch2b"
    n[prefix2_b], n[prefix2_b.replace("res","bn")], n[prefix2_b.replace("res","scale")] = conv_BN_scale(n[prefix2_a+"_relu"], nout)
    n[name+"b"] = L.Eltwise(n[name+"a_relu"], n[prefix2_b.replace("res","scale")], operation=P.Eltwise.SUM)
    n[name+"b_relu"] = L.ReLU(n[name+"b"], in_place=True)
    return {
        "bottom": bottom,
        "top": n[name+"b_relu"]
    }

def fcn(split):
    n = caffe.NetSpec()
    pydata_params = dict(split=split, mean=(104.00699, 116.66877, 122.67892),
            seed=1337)
    if split == 'train':
        pydata_params['sbdd_dir'] = '../data/sbdd/dataset'
        pylayer = 'SBDDSegDataLayer'
    else:
        pydata_params['voc_dir'] = '../data/pascal/VOC2011'
        pylayer = 'VOCSegDataLayer'
    n.data, n.label = L.Python(module='voc_layers', layer=pylayer,
            ntop=2, param_str=str(pydata_params))

    # the base net
    n.conv1_1, n.relu1_1 = conv_relu(n.data, 64, pad=100, freeze=True)
    n.conv1_2, n.relu1_2 = conv_relu(n.relu1_1, 64, freeze=True)
    n.pool1 = max_pool(n.relu1_2)

    # n.conv2_1, n.relu2_1 = conv_relu(n.pool1, 128)
    # n.conv2_2, n.relu2_2 = conv_relu(n.relu2_1, 128)
    # n.pool2 = max_pool(n.relu2_2)

    encoder1 = createEncoder(n, "res1", n.pool1, 128, 2, 1, False)

    n.conv3_1, n.relu3_1 = conv_relu(encoder1['top'], 256, freeze=True)
    n.conv3_2, n.relu3_2 = conv_relu(n.relu3_1, 256, freeze=True)
    n.conv3_3, n.relu3_3 = conv_relu(n.relu3_2, 256, freeze=True)
    n.pool3 = max_pool(n.relu3_3)

    n.conv4_1, n.relu4_1 = conv_relu(n.pool3, 512, freeze=True)
    n.conv4_2, n.relu4_2 = conv_relu(n.relu4_1, 512, freeze=True)
    n.conv4_3, n.relu4_3 = conv_relu(n.relu4_2, 512, freeze=True)
    n.pool4 = max_pool(n.relu4_3)

    n.conv5_1, n.relu5_1 = conv_relu(n.pool4, 512, freeze=True)
    n.conv5_2, n.relu5_2 = conv_relu(n.relu5_1, 512, freeze=True)
    n.conv5_3, n.relu5_3 = conv_relu(n.relu5_2, 512, freeze=True)
    n.pool5 = max_pool(n.relu5_3)

    # fully conv
    n.fc6, n.relu6 = conv_relu(n.pool5, 4096, ks=7, pad=0)
    n.drop6 = L.Dropout(n.relu6, dropout_ratio=0.5, in_place=True)
    n.fc7, n.relu7 = conv_relu(n.drop6, 4096, ks=1, pad=0)
    n.drop7 = L.Dropout(n.relu7, dropout_ratio=0.5, in_place=True)
    n.score_fr = L.Convolution(n.drop7, num_output=21, kernel_size=1, pad=0,
        param=[dict(lr_mult=0, decay_mult=0), dict(lr_mult=0, decay_mult=0)])
    n.upscore2 = L.Deconvolution(n.score_fr,
        convolution_param=dict(num_output=21, kernel_size=4, stride=2,
            bias_term=False),
        param=[dict(lr_mult=0)])

    n.score_pool4 = L.Convolution(n.pool4, num_output=21, kernel_size=1, pad=0,
        param=[dict(lr_mult=0, decay_mult=0), dict(lr_mult=0, decay_mult=0)])
    n.score_pool4c = crop(n.score_pool4, n.upscore2)
    n.fuse_pool4 = L.Eltwise(n.upscore2, n.score_pool4c,
            operation=P.Eltwise.SUM)
    n.upscore_pool4 = L.Deconvolution(n.fuse_pool4,
        convolution_param=dict(num_output=21, kernel_size=4, stride=2,
            bias_term=False),
        param=[dict(lr_mult=0)])

    n.score_pool3 = L.Convolution(n.pool3, num_output=21, kernel_size=1, pad=0,
        param=[dict(lr_mult=0, decay_mult=1), dict(lr_mult=2, decay_mult=0)])
    n.score_pool3c = crop(n.score_pool3, n.upscore_pool4)
    n.fuse_pool3 = L.Eltwise(n.upscore_pool4, n.score_pool3c,
            operation=P.Eltwise.SUM)
    n.upscore8 = L.Deconvolution(n.fuse_pool3,
        convolution_param=dict(num_output=21, kernel_size=16, stride=8,
            bias_term=False),
        param=[dict(lr_mult=0)])

    n.score = crop(n.upscore8, n.data)
    n.loss = L.SoftmaxWithLoss(n.score, n.label,
            loss_param=dict(normalize=False, ignore_label=255))

    return n.to_proto()

def make_net():
    with open('train.prototxt', 'w') as f:
        f.write(str(fcn('train')))

    with open('val.prototxt', 'w') as f:
        f.write(str(fcn('seg11valid')))

if __name__ == '__main__':
    make_net()