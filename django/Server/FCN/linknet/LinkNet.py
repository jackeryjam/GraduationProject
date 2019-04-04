import caffe
from caffe import layers as L, params as P
from caffe.coord_map import crop
from string import Template

def max_pool(bottom, ks=2, stride=2):
    return L.Pooling(bottom, pool=P.Pooling.MAX, kernel_size=ks, stride=stride)

def conv_relu(bottom, nout, ks=3, stride=1, pad=1):
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad,
        param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)])
    return conv, L.ReLU(conv, in_place=True)

def conv_BN_scale(bottom, nout, ks=3, stride=1, pad=1):
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad,
        param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)])
    return conv, L.BatchNorm(conv, in_place=True), L.Scale(conv, in_place=True, bias_term=True)

def conv_BN_scale_relu(bottom, nout, ks=3, stride=1, pad=1):
    conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
        num_output=nout, pad=pad,
        param=[dict(lr_mult=1, decay_mult=1), dict(lr_mult=2, decay_mult=0)])
    return conv, L.BatchNorm(conv, in_place=True), L.Scale(conv, in_place=True, bias_term=True), L.ReLU(conv, in_place=True)

def deconv_BN_scale_relu(bottom, nout, ks=3, stride=1, pad=1, bias_term=True):
    deconv = L.Deconvolution(bottom, 
        convolution_param=dict(num_output=nout, kernel_size=ks, stride=stride, pad=pad,
            bias_term=bias_term),
        param=[dict(lr_mult=0)])
    return deconv, L.BatchNorm(deconv, in_place=bias_term), L.Scale(deconv, in_place=True, bias_term=bias_term), L.ReLU(deconv, in_place=True)

def max_pool(bottom, ks=2, stride=2):
    return L.Pooling(bottom, pool=P.Pooling.MAX, kernel_size=ks, stride=stride)

class LinkNet:
    def __init__(self, data, label, class_n=21):
        self.net = caffe.NetSpec()
        self.createDataLayer(data, label)
        self.in_block = self.creatInitBlock()

        self.encoder1 = self.createEncoder("encoder1", self.in_block["top"], 64)
        self.encoder2 = self.createEncoder("encoder2", self.encoder1["top"], 128, stride=2)
        self.encoder3 = self.createEncoder("encoder3", self.encoder2["top"], 256, stride=2)
        self.encoder4 = self.createEncoder("encoder4", self.encoder3["top"], 512, stride=2)

        self.decoder4 = self.createDecoder("decoder4", self.encoder4["top"], 512, 256, 2, pad=0)
        d4_crop = crop(self.decoder4["top"], self.encoder3["top"])
        d3_in = L.Eltwise(self.encoder3["top"], d4_crop, operation=P.Eltwise.SUM)

        self.decoder3 = self.createDecoder("decoder3", d3_in, 256, 128, 2, pad=0)
        d3_crop = crop(self.decoder3["top"], self.encoder2["top"])
        d2_in = L.Eltwise(self.encoder2["top"], d3_crop, operation=P.Eltwise.SUM)

        self.decoder2 = self.createDecoder("decoder2", d2_in, 128, 64, 2, pad=0)
        d2_crop = crop(self.decoder2["top"], self.encoder1["top"])
        d1_in = L.Eltwise(self.encoder1["top"], d2_crop, operation=P.Eltwise.SUM)

        self.decoder1 = self.createDecoder("decoder1", d1_in, 64, 64, 1, pad=0)
        d1_crop = crop(self.decoder1["top"], self.in_block["top"])

        self.endblock = self.createEndBlock(d1_crop, 64, class_n)
        end_crop = crop(self.endblock["top"], data)

        n = self.net
        n.loss = L.SoftmaxWithLoss(end_crop, n.label,
                loss_param=dict(normalize=False, ignore_label=255))
    
    def createDataLayer(self, data, label):
        self.net.data = data
        self.net.label = label
        return {"data": self.net.data, "label": self.net.label}

    def creatInitBlock(self):
        n = self.net
        # init block
        n.in_block_conv, n.in_block_BN, n.in_block_scale, n.in_block_relu = conv_BN_scale_relu(n.data, 64, pad=3, stride=2, ks=7)
        n.pool1 = max_pool(n.in_block_relu)
        return {"bottom": n.data, "top": n.pool1}
    
    def createEncoder(self, name, bottom, nout, stride=1, pad=1):
        n = self.net

        n[name+"_conv1"], n[name+"_BN1"], n[name+"_scale1"], n[name+"_relu1"] = conv_BN_scale_relu(bottom, nout, stride=stride)
        n[name+"_conv2"], n[name+"_BN2"], n[name+"_scale2"] = conv_BN_scale(n[name+"_relu1"], nout)
        n[name+"_conv_r"], n[name+"_BN_r"], n[name+"_scale_r"] = conv_BN_scale(bottom, nout, 1, stride=stride, pad=0)
        
        n[name+"_sum1"] = L.Eltwise(n[name+"_scale_r"], n[name+"_scale2"], operation=P.Eltwise.SUM)
        n[name+"_sum_relu1"] = L.ReLU(n[name+"_sum1"], in_place=True)

        n[name+"_conv3"], n[name+"_BN3"], n[name+"_scale3"], n[name+"_relu3"] = conv_BN_scale_relu(n[name+"_sum_relu1"], nout)
        n[name+"_conv4"], n[name+"_BN4"], n[name+"_scale4"] = conv_BN_scale(n[name+"_relu3"], nout)
        n[name+"_sum2"] = L.Eltwise(n[name+"_scale4"], n[name+"_sum_relu1"], operation=P.Eltwise.SUM)
        n[name+"_sum_relu2"] = L.ReLU(n[name+"_sum2"], in_place=True)
        return {
            "bottom": bottom,
            "top": n[name+"_sum_relu2"]
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

