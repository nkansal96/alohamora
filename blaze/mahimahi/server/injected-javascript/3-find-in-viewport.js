var imagesInViewPort = []



function isElementInViewport (el) {
    //special bonus for those using jQuery
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }
    var rect = el.getBoundingClientRect();
    let vertInView = rect.top <= window.innerHeight && rect.bottom > rect.top && rect.top >= 0;
    let horzInView = rect.left <= window.innerWidth && rect.right > rect.left && rect.left >= 0;
    return vertInView && horzInView;
}

function isAnyPartOfElementInViewport(el) {
    var rect = el.getBoundingClientRect();
    var windowHeight = (window.innerHeight);
    var windowWidth = (window.innerWidth);
    var vertInView = (rect.top < windowHeight) && ((rect.top + rect.height) >= 0);
    var horInView = (rect.left < windowWidth) && ((rect.left + rect.width) >= 0);
    return (vertInView && horInView);
}

function printCriticalRequests() {
    urlRequestors.forEach(function(k) {
        if (imagesInViewPort.includes(k.url)) {
            console.log(`${k.url} is requested by ${k.initiator}`)
        } else {
            console.log(`${k.url} is not in viewport.`)
        }
    })
}

function getCriticalRequests() {
    importantRequests = []
    importantRequests = imagesInViewPort.map(function(url) {return url;});
    urlRequestors.forEach(function(k) {
        if (imagesInViewPort.indexOf(k.url) >= 0) {
            importantRequests = importantRequests.concat(k.initiator)
        }
    })
    return importantRequests
}


function findAndPrintImagesInViewport(ele) {
    ele.querySelectorAll('*').forEach(function(node) {
        if (node.tagName == "IMG") {
            let url = null;
            if(isElementInViewport(node)) {
                if (typeof node.href != 'undefined') {
                    url = node.href;
                }
                if(typeof node.src != 'undefined') {
                    url = node.src;
                }
                if (url != null) {
                    imagesInViewPort.push(url)
                }
            } 
            }
    });
    let answer = getCriticalRequests()
    console.log("alohomora: this is the answer")
    console.log(JSON.stringify({'alohomora_output': answer}))
    console.log("alohomora: that was the the answer")
}

window.addEventListener('load', function (event) {
    var listOfIframes = document.querySelectorAll("iframe");
    for (var index = 0; listOfIframes && index < listOfIframes.length; index++) {
        const iframeElement = listOfIframes[index];
        if(typeof(iframeElement) == 'undefined') {
            continue;
        }
        if(iframeElement && isAnyPartOfElementInViewport(iframeElement)) {
            try {
                var innerDoc = (iframeElement.contentDocument) ? iframeElement.contentDocument : iframeElement.contentWindow.document;    
                findAndPrintImagesInViewport(innerDoc)
            } catch (error) {
                console.log('avoid processing iframe due to an exception ', error)
            }
        }
    }
    findAndPrintImagesInViewport(document)
  });

