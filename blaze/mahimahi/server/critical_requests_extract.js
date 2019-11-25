function htmlToElement(t){try{var e=document.createElement("template");return void 0!==t.trim&&(t=t.trim()),e.innerHTML=t,e.content.firstChild}catch(e){return t}}let open=window.XMLHttpRequest.prototype.open,urlRequestors=[],stackInterceptCallback=(t,e)=>{t.length>0&&"https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js"!=e&&"https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js"!=t[t.length-1].fileName&&urlRequestors.push({url:e,initiator:t[t.length-1].fileName+":"+t[t.length-2].fileName})},stackInterceptErrBack=t=>{console.log(t.message)};function openReplacement(t,e,c,r,a){return this._url=e,StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)}),open.apply(this,arguments)}window.XMLHttpRequest.prototype.open=openReplacement;const _fetch=window.fetch;function getURLfromString(t){let e=null;try{if(t.indexOf("<")>=0&&t.indexOf(">")>=0){let c=(t=(t=t.replace("= ","=").replace("= ","=")).replace(/["']/g,"")).indexOf("src=");if(c>=0){let r=t.indexOf(" ",c);r<0&&(r=t.indexOf(">",c));let a=t.substring(c,r);e=(a=(a=a.replace(" ","")).replace("src=","")).trim()}else if((c=t.indexOf("href="))>=0){let r=t.indexOf(" ",c);r<0&&(r=t.indexOf(">",c));let a=t.substring(c,r);e=(a=(a=a.replace(" ","")).replace("href=","")).trim()}}}catch(t){return e}return e}window.fetch=function(){let t=arguments[0];return console.log(`fetch basic intercepted. ${t}`),StackTrace.get().then(e=>{stackInterceptCallback(e,t)}).catch(t=>{stackInterceptErrBack(t)}),_fetch.apply(this,arguments)},document.old_write=document.write,document.write=function(t){let e=htmlToElement(t);void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)}),document.old_write(t)},document.old_writeln=document.writeln,document.writeln=function(t){console.log("document.writeln intercepted.");let e=htmlToElement(t);void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)}),document.old_writeln(t)},function(){var t=Object.getOwnPropertyDescriptor(Element.prototype,"innerHTML").set;Object.defineProperty(Element.prototype,"innerHTML",{set:function(e){var c=function(t){let e=getURLfromString(t);null!=e&&StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});return t}(e);return t.call(this,c)}})}(),old_appendChild=Element.prototype.appendChild,Element.prototype.appendChild=function(){console.log("element.appendChild intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_appendChild.apply(this,arguments)},old_append=Element.prototype.append,Element.prototype.append=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_append.apply(this,arguments)},old_prepend=Element.prototype.prepend,Element.prototype.prepend=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_prepend.apply(this,arguments)},old_before=Element.prototype.before,Element.prototype.before=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_before.apply(this,arguments)},old_after=Element.prototype.after,Element.prototype.after=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_after.apply(this,arguments)},old_insertBefore=Element.prototype.insertBefore,Element.prototype.insertBefore=function(){console.log("element.insertBefore intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_insertBefore.apply(this,arguments)},old_replaceWith=Element.prototype.replaceWith,Element.prototype.replaceWith=function(){console.log("element.replaceWith intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_replaceWith.apply(this,arguments)},old_insertAdjacentHTML=Element.prototype.insertAdjacentHTML,Element.prototype.insertAdjacentHTML=function(){let t=arguments[1]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[1]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_insertAdjacentHTML.apply(this,arguments)},old_insertAdjacentText=Element.prototype.insertAdjacentText,Element.prototype.insertAdjacentText=function(){let t=arguments[1]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[1]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_insertAdjacentText.apply(this,arguments)},old_insertAdjacentElement=Element.prototype.insertAdjacentElement,Element.prototype.insertAdjacentElement=function(){let t=arguments[1]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[1]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_insertAdjacentElement.apply(this,arguments)},old_replaceChild=Element.prototype.replaceChild,Element.prototype.replaceChild=function(){console.log("element.replaceChild intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_replaceChild.apply(this,arguments)};

var imagesInViewPort = []

function isElementInViewport (el) {
    //special bonus for those using jQuery
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }
    var rect = el.getBoundingClientRect();
    console.log("alohomoradebug: isElementInViewport window height is " + window.innerHeight)
    console.log("alohomoradebug: isElementInViewport window width is " + window.innerWidth)
    
    let vertInView = rect.top <= window.innerHeight && rect.bottom > rect.top && rect.top >= 0;
    let horzInView = rect.left <= window.innerWidth && rect.right > rect.left && rect.left >= 0;
    return vertInView && horzInView;
}

function isAnyPartOfElementInViewport(el) {
    var rect = el.getBoundingClientRect();
    var windowHeight = (window.innerHeight);
    var windowWidth = (window.innerWidth);
    console.log("alohomoradebug: window height is " + windowHeight)
    console.log("alohomoradebug: window width is " + windowWidth)
    var vertInView = (rect.top < windowHeight) && ((rect.top + rect.height) >= 0);
    var horInView = (rect.left < windowWidth) && ((rect.left + rect.width) >= 0);
    return (vertInView && horInView);
}


function getCriticalRequests() {
    importantRequests = []
    importantRequests = imagesInViewPort.map((url) => (url));

    urlRequestors.forEach((k) => {
        if (imagesInViewPort.includes(k.url)) {
            importantRequests = importantRequests.concat(k.initiator)
        }
    })
    return importantRequests
}


function findAndPrintImagesInViewport(ele) {
    ele.querySelectorAll('*').forEach(function(node) {
        if (node.tagName == "IMG") {
            let url = null;
            console.log("alohomoradebug checking node " + JSON.stringify(node))
            if(isElementInViewport(node)) {
                console.log("alohomoradebug: element is in viewport")
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
                console.log("alohomoradebug: element not in viewport")
            }
        }
    });
    let answer = getCriticalRequests()
    console.log("alohomoradebug: this is the answer")
    console.log(JSON.stringify({'alohomora_output': answer}))
    console.log("alohomoradebug: that was the the answer")
}

window.addEventListener('load', (event) => {
    console.log("alohomoradebug: extracting critical elements")
	document.querySelectorAll("iframe").forEach((ele) => {
		var iframeID = ele.id;
        iframeElement = document.getElementById(iframeID)
        if(isAnyPartOfElementInViewport(iframeElement)) {
            var innerDoc = (iframeElement.contentDocument) ? iframeElement.contentDocument : iframeElement.contentWindow.document;
            findAndPrintImagesInViewport(innerDoc)
        }
	});
	findAndPrintImagesInViewport(document)
  });


