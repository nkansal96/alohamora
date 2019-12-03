var imagesInViewPort = []



function isElementInViewport (el) {
    //special bonus for those using jQuery
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }
    var rect = el.getBoundingClientRect();
    var topIsVisible = rect.top >= 0 && (rect.top <= (window.innerHeight || document.documentElement.clientHeight));
	var botIsVisible = rect.top < 0 && rect.bottom >= 0;
	var vertInView = topIsVisible || botIsVisible;

	var leftIsVisible = rect.left >= 0 && (rect.left <= (window.innerWidth || document.documentElement.clientWidth));
	var rightIsVisible = rect.left < 0 && rect.right >= 0;
	var horzInView = leftIsVisible || rightIsVisible;

	return vertInView && horzInView;
}


function getCriticalRequests() {
    var importantRequests = []
    importantRequests = imagesInViewPort.map(function(url) {return url;});
    if (typeof(urlRequestors) == 'undefined' || urlRequestors == null) return importantRequests;
    urlRequestors.forEach(function(k) {
        if (imagesInViewPort.indexOf(k.url) >= 0) {
            importantRequests = importantRequests.concat(k.initiator)
        }
    })
    return importantRequests
}


function findAndPrintImagesInViewport(ele) {
    ele.querySelectorAll('*').forEach(function(node) {
        try {
            if (isElementInViewport(node)) {
                var url = null;
                if(node.tagName == "IMG") {
                    if (typeof node.href != 'undefined') {
                        url = node.href;
                    }
                    if(typeof node.src != 'undefined') {
                        url = node.src;
                    }
                    if (url != null) {
                        imagesInViewPort.push(url)
                    }
            } else {
                var style = window.getComputedStyle(node)
                for (var i = style.length - 1; i >= 0; i--) {
                    var cssName = style[i]
                    var cssPropertyValue = style.getPropertyValue(cssName)
                    if (cssPropertyValue.indexOf("url") >= 0) {
                        var potentialURL = cssPropertyValue;
                        var startIndex = potentialURL.indexOf('url(')
                        var urlWithSpace = false;
                        if (startIndex < 0) {
                            startIndex = potentialURL.indexOf('url (')
                            urlWithSpace = true;
                        } 
                        if (startIndex < 0) {
                            continue;
                        }
                        var endIndex = potentialURL.indexOf(')', startIndex)
                        if (endIndex < 0) {
                            continue
                        }
                        var potentialURL = potentialURL.substring(startIndex + (urlWithSpace ? 5 : 4), endIndex)
                        var t=potentialURL.length;
                        if (potentialURL.charAt(0)=='"'||potentialURL.charAt(0)=="'") {
                            potentialURL = potentialURL.substring(1);
                            t--;
                        }
                        if (potentialURL.charAt(t-1)=='"'||potentialURL.charAt(t-1)=="'") {
                            potentialURL = potentialURL.substring(0,t-1);
                        }
    
                        var link = document.createElement("a");
                        link.href = potentialURL;
                        if(potentialURL.index("data:image") < 0)
                            imagesInViewPort.push(link.href)
                    }
                }
            }  
            }           
        } catch (error) {
            console.error("ignoring node due to error ", error)
        }

    });
    var answer = getCriticalRequests()
    console.log(JSON.stringify({'alohomora_output': answer}))
}


window.addEventListener('load', function (event) {
    try {
        findAndPrintImagesInViewport(document)
        var listOfIframes = document.querySelectorAll("iframe");
        for (var index = 0; listOfIframes && index < listOfIframes.length; index++) {
            const iframeElement = listOfIframes[index];
            if(typeof(iframeElement) == 'undefined') {
                continue;
            }
            if(iframeElement && isElementInViewport(iframeElement)) {
                try {
                    var innerDoc = (iframeElement.contentDocument) ? iframeElement.contentDocument : iframeElement.contentWindow.document;    
                    findAndPrintImagesInViewport(innerDoc)
                } catch (error) {
                    console.error('avoid processing iframe due to an exception ', error)
                }
            }
        }    
    } catch (error) {
        console.error("skipping due to error ", error)
    }    
  });

