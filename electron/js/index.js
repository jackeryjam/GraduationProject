// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
var serverUrl = 'http://node02.jackjam.xyz:8000/';
var API = {
    upload: serverUrl + 'API/upload',
    segment: serverUrl + 'API/segment',
    image: serverUrl + 'static/image/'
};
(function () {
    this.$ =  require('../lib/jquery-3.3.1.min.js');
    let base64Img = "";

    this.selectPic = function () {
        document.querySelector("#fileSelector").click();
    }

    this.preventDefault = function (e) {
        if (e && e.stopPropagation)
            e.stopPropagation();
        else
            window.event.cancelBubble = true;
    }

    this.readFile = function (files) {
        if (files.length) {
            var file = files[0];
            var reader = new FileReader();//new一个FileReader实例
        
            if (/image+/.test(file.type)) {//判断文件是不是imgage类型
                reader.onload = function () {
                    console.log(this)
                    var dom = document.querySelector(".upload section:first-child .upload-box");
                    dom.innerHTML = "";
                    var img = document.createElement("img");
                    img.src = this.result;
                    base64Img = this.result;
                    dom.append(img);
                }
                reader.readAsDataURL(file);
            } else {
                console.log("Not a pic");
            }
        }
    }
    
    this.uploadImage = function(){
        const update = arr => {
            console.log(arr)
            console.log(this.carouselVm)
            console.log(this.carouselVm.$data)
            this.carouselVm.$data.results = arr
        }

        const segment = fileName => {
            $.get(API.segment, {image: fileName}, res => {
                console.log(res)
                console.log(fileName)
                var arr = ['output.png','vis.jpg'].map(val => API.image + fileName.split('.')[0] + '.' + val);
                update(arr)
            })
        }
        
        $.post(API.upload,{
            file: base64Img
        },function(res) {
            console.log(res)
            if (res.code == 200) {
                segment(res.data.fileName)
            } 
            uploading = false;
        })
    }

    this.takePhoto = function(btn) {
        function openMedia(){
            let dom = document.querySelector(".upload section:first-child .upload-box");
            dom.innerHTML = "";
            let video = document.createElement("video");
            video.id = "video";
            video.autoplay = "autoplay";
            dom.appendChild(video);
            let constraints = {
                video: {width: video.offsetWidth, height: video.offsetHeight},
                audio: false
            };
            navigator.mediaDevices.getUserMedia(constraints)
                .then(function (MediaStream) {
                    video.srcObject = MediaStream;
                    video.play();
                });
        }
        function shot(){
            let video = document.querySelector("#video")
            let canvas = document.createElement("canvas");
            let ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video,0,0);
            base64Img = canvas.toDataURL("image/jpg");
            var dom = document.querySelector(".upload section:first-child .upload-box");
            dom.innerHTML = "";
            var img = document.createElement("img");
            img.src = base64Img;
            dom.append(img);
        }
        if(btn.innerHTML === "立即拍照" || btn.innerHTML === "重新拍照") {
            window.btn = btn
            btn.innerHTML = "确定拍照";
            openMedia();
        }
        else if(btn.innerHTML === "确定拍照") {
            btn.innerHTML = "重新拍照";
            shot();
        } 
        
    }
}).call(window)