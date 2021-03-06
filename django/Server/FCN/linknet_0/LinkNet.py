import caffe
from caffe import layers as L, params as P
from caffe.coord_map import crop
from string import Template

def max_pool(bottom, ks=2, stride=2):
    return L.Pooling(bottom, pool=P.Pooling.MAX, kernel_size=ks, stride=stride)

def conv_relu(bottom, nout, ks=3, stride=1, pad=1):
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad, bias_term=False,
        weight_filler=dict(type="msra") )
        #param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)]
    return conv, L.ReLU(conv, in_place=True)

def conv_BN_scale(bottom, nout, ks=3, stride=1, pad=1):
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad, bias_term=False,
        weight_filler=dict(type="msra") )
    return conv, L.BatchNorm(conv, in_place=True), L.Scale(conv, in_place=True, bias_term=True)

def conv_BN_scale_relu(bottom, nout, ks=3, stride=1, pad=1):
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad, bias_term=False,
        weight_filler=dict(type="msra") )
    return conv, L.BatchNorm(conv, in_place=True), L.Scale(conv, in_place=True, bias_term=True), L.ReLU(conv, in_place=True)

def deconv_BN_scale_relu(bottom, nout, ks=3, stride=1, pad=1, bias_term=True):
    deconv = L.Deconvolution(bottom,
        convolution_param=dict(num_output=nout, kernel_size=ks, stride=stride, pad=pad,
            bias_term=bias_term, weight_filler=dict(type="bilinear") ), param=[dict(lr_mult=0, decay_mult=1)] )
    return deconv, L.BatchNorm(deconv, in_place=bias_term), L.Scale(deconv, in_place=True, bias_term=bias_term), L.ReLU(deconv, in_place=True)

def max_pool(bottom, ks=2, stride=2):
    return L.Pooling(bottom, pool=P.Pooling.MAX, kernel_size=ks, stride=stride)

class LinkNet:
    def __init__(self, data, label, class_n=21):
        self.net = caffe.NetSpec()
        n = self.net
        self.createDataLayer(data, label)
        self.in_block = self.creatInitBlock()

        self.encoder1 = self.createEncoder("res2", self.in_block["top"], 64)
        self.encoder2 = self.createEncoder("res3", self.encoder1["top"], 128, stride=2)
        self.encoder3 = self.createEncoder("res4", self.encoder2["top"], 256, stride=2)
        self.encoder4 = self.createEncoder("res5", self.encoder3["top"], 512, stride=2)

        # self.decoder4 = self.createDecoder("decoder4", self.encoder4["top"], 512, 256, 2, pad=0)
        # d4_crop = crop(self.decoder4["top"], self.encoder3["top"])
        # d3_in = L.Eltwise(self.encoder3["top"], d4_crop, operation=P.Eltwise.SUM)

        # self.decoder3 = self.createDecoder("decoder3", d3_in, 256, 128, 2, pad=0)
        # d3_crop = crop(self.decoder3["top"], self.encoder2["top"])
        # d2_in = L.Eltwise(self.encoder2["top"], d3_crop, operation=P.Eltwise.SUM)

        # self.decoder2 = self.createDecoder("decoder2", d2_in, 128, 64, 2, pad=0)
        # d2_crop = crop(self.decoder2["top"], self.encoder1["top"])
        # d1_in = L.Eltwise(self.encoder1["top"], d2_crop, operation=P.Eltwise.SUM)

        # self.decoder1 = self.createDecoder("decoder1", d1_in, 64, 64, 1, pad=0)
        # d1_crop = crop(self.decoder1["top"], self.in_block["top"])

        # self.endblock = self.createEndBlock(d1_crop, 64, class_n)
        # end_crop = crop(self.endblock["top"], data)

        n.score_fr = L.Convolution(self.encoder4["top"], num_output=21, kernel_size=1, pad=0,
            param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)])

        n.upscore = L.Deconvolution(n.score_fr,
            convolution_param=dict(num_output=21, kernel_size=64, stride=32,
                bias_term=False, weight_filler=dict(type="bilinear") ),
                param=[dict(lr_mult=0)])
        
        n.score = crop(n.upscore, n.data)
        n.loss = L.SoftmaxWithLoss(n.score, n.label,
                loss_param=dict(normalize=False, ignore_label=255))
    
    def createDataLayer(self, data, label):
        self.net.data = data
        self.net.label = label
        return {"data": self.net.data, "label": self.net.label}

    def creatInitBlock(self):
        n = self.net
        # init block
        n.conv1, n.bn_conv1, n.scale_conv1, n.conv1_relu = conv_BN_scale_relu(n.data, 64, pad=3, stride=2, ks=7)
        n.pool1 = max_pool(n.conv1_relu)
        return {"bottom": n.data, "top": n.pool1}
    
    def createEncoder(self, name, bottom, nout, stride=1, pad=1):
        n = self.net

        prefix = name + "a_branch1"
        n[prefix], n[prefix.replace("res","bn")], n[prefix.replace("res","scale")] = conv_BN_scale(bottom, nout, 1, stride=stride, pad=0)

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

    def createDecoder(self, name, bottom, nin, nout, stride=1, pad=1):
        n = self.net

        n[name+"_conv1"], n[name+"_BN1"], n[name+"_scale1"], n[name+"_relu1"] = conv_BN_scale_relu(bottom, nin // 4, ks=1, stride=1, pad=0)
        n[name+"_deconv"], n[name+"_BN2"], n[name+"_scale2"], n[name+"_relu2"] = deconv_BN_scale_relu(n[name+"_relu1"], nin // 4, ks=3, stride=stride, pad=pad)
        n[name+"_conv3"], n[name+"_BN3"], n[name+"_scale3"], n[name+"_relu3"] = conv_BN_scale_relu(n[name+"_relu2"], nout, ks=1, stride=1, pad=0)

        return {
            "bottom": bottom,
            "top": n[name+"_relu3"]
        }

    def createEndBlock(self, bottom, nin, nout, pad=0):
        n = self.net
        name = "end_block"
        n[name+"_deconv1"], n[name+"_BN1"], n[name+"_scale1"], n[name+"_relu1"] = deconv_BN_scale_relu(bottom, nin // 2, ks=3, stride=2, pad=0)
        n[name+"_conv2"], n[name+"_BN2"], n[name+"_scale2"], n[name+"_relu2"] = conv_BN_scale_relu(n[name+"_relu1"], nin // 2, ks=3, stride=1, pad=1)
        n[name+"_deconv3"], n[name+"_BN3"], n[name+"_scale3"], n[name+"_relu3"] = deconv_BN_scale_relu(n[name+"_relu2"], nout, ks=3, stride=2, pad=0)

        return {
            "bottom": bottom,
            "top": n[name+"_relu3"]
        }

    def to_proto(self):
        return self.net.to_proto()

def createLinkNet(split):
    # n = caffe.NetSpec()
    pydata_params = dict(split=split, mean=(104.00699, 116.66877, 122.67892),
            seed=1337)
    if split == 'train':
        pydata_params['sbdd_dir'] = '../data/sbdd/dataset'
        pylayer = 'SBDDSegDataLayer'
    else:
        pydata_params['voc_dir'] = '../data/pascal/VOC2011'
        pylayer = 'VOCSegDataLayer'
    data, label = L.Python(module='voc_layers', layer=pylayer,
            ntop=2, param_str=str(pydata_params))
    linkNet = LinkNet(data, label)

    return linkNet.to_proto()

def make_net():
    with open('train.prototxt', 'w') as f:
        f.write(str(createLinkNet('train')))

    with open('val.prototxt', 'w') as f:
        f.write(str(createLinkNet('seg11valid')))

if __name__ == '__main__':
    make_net()


