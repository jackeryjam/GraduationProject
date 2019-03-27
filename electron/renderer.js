// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
var serverUrl = 'http://tx.jackeryjam.xyz:8000/';
var API = {
    upload: serverUrl + 'API/upload',
    segment: serverUrl + 'API/segment',
    image: serverUrl + 'static/image/'
};
(function () {
    this.$ =  require('./lib/jquery-3.3.1.min.js');
    require('./lib/unslider/unslider.min.js')(this.$, false);
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
            var ul = document.querySelector("#b05 ul");
            ul.innerHTML = ''
            arr.map(val => {
                var li = document.createElement('li')
                var img = document.createElement('img')
                img.src = val
                img.height = 480
                li.appendChild(img)
                return li
            }).forEach(dom => ul.appendChild(dom))

            var unslider05 = $('#b05').unslider({
                dots: true,
                delay: 100000,
            });
        
            var data05 = unslider05.data('unslider');
        
            $('.unslider-arrow05').click(function() {
                var fn = this.className.split(' ')[1];
                data05[fn]();
        
            });
        }

        const segment = fileName => {
            $.get(API.segment, {image: fileName}, res => {
                console.log(res)
                console.log(fileName)
                var arr = ['output.png','vis.jpg'].map(val => API.image + fileName.split('.')[0] + '.' + val);
                console.log(arr)
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

        // $.ajax({
        //     url: API.upload,
        //     type: 'POST',
        //     cache: false,
        //     data: new FormData($('#uploadImage')[0]),
        //     processData: false,
        //     contentType: false,
        //     dataType:"json",
        //     beforeSend: function(){
        //         uploading = true;
        //     },
        //     success : function(res) {
        //         console.log(res)
        //         if (res.code == 200) {
        //             segment(res.data.fileName)
        //         } 
        //         uploading = false;
        //     }
        // });
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