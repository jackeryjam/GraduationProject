// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
var serverUrl = 'http://node02.jackjam.xyz:8000/';
var API = {
    upload: serverUrl + 'API/upload',
    segment: serverUrl + 'API/segment',
    compare: serverUrl + 'API/compare',
    image: serverUrl + 'static/image/'
};
(function () {
    this.$ = require('../lib/jquery-3.3.1.min.js');
    let img1 = "";
    let img2 = "";

    this.selectPic = function (index) {
        document.querySelector("#fileSelector" + index).click();
    }

    this.preventDefault = function (e) {
        if (e && e.stopPropagation)
            e.stopPropagation();
        else
            window.event.cancelBubble = true;
    }

    this.readFile = function (files, index) {
        const segment = fileName => {
            $.get(API.segment, { image: fileName }, res => {
                var arr = ['output.png', 'vis.jpg'].map(val => API.image + fileName.split('.')[0] + '.' + val);
                console.log(arr)
                if (index === 1) {
                    this.carouselVm.$data.results.splice(0, 1, arr[0])
                }
                else {
                    this.carouselVm.$data.results.splice(1, 1, arr[0])
                }
            })
        }

        if (files.length) {
            var file = files[0];
            var reader = new FileReader();//new一个FileReader实例

            if (/image+/.test(file.type)) {//判断文件是不是imgage类型
                reader.onload = function () {
                    var dom = document.querySelector(`.upload .box${index} .upload-box`);
                    dom.innerHTML = "";
                    var img = document.createElement("img");
                    img.src = this.result;
                    dom.append(img);
                    $.post(API.upload, {
                        file: this.result
                    }, function (res) {
                        if (res.code == 200) {
                            if (index === 1) {
                                img1 = res.data.fileName;
                            }
                            else {
                                img2 = res.data.fileName;
                            }
                            segment(res.data.fileName)
                        }
                    })
                }
                reader.readAsDataURL(file);
            } else {
                console.log("Not a pic");
            }
        }
    }

    this.uploadImage = function () {
        const update = arr => {
            console.log(arr)
            console.log(this.carouselVm)
            console.log(this.carouselVm.$data)
            this.carouselVm.$data.results = arr
        }

        const segment = fileName => {
            $.get(API.segment, { image: fileName }, res => {
                console.log(res)
                console.log(fileName)
                var arr = ['output.png', 'vis.jpg'].map(val => API.image + fileName.split('.')[0] + '.' + val);
                update(arr)
            })
        }

        $.post(API.upload, {
            file: base64Img
        }, function (res) {
            console.log(res)
            if (res.code == 200) {
                segment(res.data.fileName)
            }
            uploading = false;
        })
    }

    this.compare = function (btn) {
        if (btn === 1) {
            im1 = img1
            im2 = img2
        } else {
            im1 = this.carouselVm.$data.results[0].split("/").pop()
            im2 = this.carouselVm.$data.results[1].split("/").pop()
        }
        $.get(API.compare, { img1: im1, img2: im2 }, res => {
           console.log(res)
           same = `相${btn === 1 ? '同' : '似' }的`
           this.carouselVm.open(btn === 1 ? "直接对比的结果" : "分割后对比的结果",
           `这两张图是${res.data.distance <= 5 ? '' : '不'}${same}`) 
        })
    }
}).call(window)