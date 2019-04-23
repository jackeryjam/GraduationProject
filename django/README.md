# 服务端

### 预置环境安装
* python
* django
    pip install django
* caffe
    caffe安装详见  
    https://www.baidu.com/s?ie=UTF-8&wd=caffe%20%E5%AE%89%E8%A3%85  
* caffe模型下载
    下载http://dl.caffe.berkeleyvision.org/fcn8s-heavy-pascal.caffemodel到django/Server/FCN/voc-fcn8s目录下  
* 创建static/image文件夹
    mkdir -p static/image

### django启动方式  
python manage.py runserver 0.0.0.0:8000  
