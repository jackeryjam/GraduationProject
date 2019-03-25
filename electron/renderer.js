// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
(function () {
    this.$ =  require('./lib/jquery-3.3.1.min.js');
    require('./lib/unslider/unslider.min.js')(this.$, false);

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
                    dom.append(img);
                }
                reader.readAsDataURL(file);
            } else {
                console.log("Not a pic");
            }
        }
    }

    var unslider05 = $('#b05').unslider({
		dots: true
	});

	var data05 = unslider05.data('unslider');

	$('.unslider-arrow05').click(function() {
        var fn = this.className.split(' ')[1];
        data05[fn]();

    });

	$("#stop").click(function() {
		data05.stop();

	});


	$("#start").click(function() {
		this.data05.start();
	});

	$("#move").click(function() {
		data05.move(1, function() {});
	});
}).call(window)