""" Implements the logic to read the file store, generate the server config, and start the servers """

import contextlib
import os
import subprocess
import sys
import tempfile
import gzip
from typing import Optional
from urllib.parse import urlparse
from io import BytesIO

from bs4 import BeautifulSoup

from blaze.action import Policy
from blaze.logger import logger

from blaze.mahimahi.server.dns import DNSServer
from blaze.mahimahi.server.filestore import FileStore
from blaze.mahimahi.server.interfaces import Interfaces
from blaze.mahimahi.server.nginx_config import Config


def prepend_javascript_snippet(input_string: str):
    """
    gets in an html representation of the website
    converts into a beautifulsoup object
    adds a javascript tag to fetch critical requests
    converts back into string and returns
    """
    soup = BeautifulSoup(input_string, "html.parser")
    stack_trace_dependency = soup.new_tag("script")
    stack_trace_dependency["src"] = "https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js"
    critical_catcher = soup.new_tag("script")
    critical_catcher.string = """
   function htmlToElement(t){try{var e=document.createElement("template");return void 0!==t.trim&&(t=t.trim()),e.innerHTML=t,e.content.firstChild}catch(e){return t}}let open=window.XMLHttpRequest.prototype.open,urlRequestors=[],stackInterceptCallback=(t,e)=>{t.length>0&&"https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js"!=e&&"https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js"!=t[t.length-1].fileName&&urlRequestors.push({url:e,initiator:t[t.length-1].fileName+":"+t[t.length-2].fileName})},stackInterceptErrBack=t=>{console.log(t.message)};function openReplacement(t,e,c,r,a){return this._url=e,StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)}),open.apply(this,arguments)}window.XMLHttpRequest.prototype.open=openReplacement;const _fetch=window.fetch;function getURLfromString(t){let e=null;try{if(t.indexOf("<")>=0&&t.indexOf(">")>=0){let c=(t=(t=t.replace("= ","=").replace("= ","=")).replace(/["']/g,"")).indexOf("src=");if(c>=0){let r=t.indexOf(" ",c);r<0&&(r=t.indexOf(">",c));let a=t.substring(c,r);e=(a=(a=a.replace(" ","")).replace("src=","")).trim()}else if((c=t.indexOf("href="))>=0){let r=t.indexOf(" ",c);r<0&&(r=t.indexOf(">",c));let a=t.substring(c,r);e=(a=(a=a.replace(" ","")).replace("href=","")).trim()}}}catch(t){return e}return e}window.fetch=function(){let t=arguments[0];return console.log(`fetch basic intercepted. ${t}`),StackTrace.get().then(e=>{stackInterceptCallback(e,t)}).catch(t=>{stackInterceptErrBack(t)}),_fetch.apply(this,arguments)},document.old_write=document.write,document.write=function(t){let e=htmlToElement(t);void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)}),document.old_write(t)},document.old_writeln=document.writeln,document.writeln=function(t){console.log("document.writeln intercepted.");let e=htmlToElement(t);void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)}),document.old_writeln(t)},function(){var t=Object.getOwnPropertyDescriptor(Element.prototype,"innerHTML").set;Object.defineProperty(Element.prototype,"innerHTML",{set:function(e){var c=function(t){let e=getURLfromString(t);null!=e&&StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});return t}(e);return t.call(this,c)}})}(),old_appendChild=Element.prototype.appendChild,Element.prototype.appendChild=function(){console.log("element.appendChild intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_appendChild.apply(this,arguments)},old_append=Element.prototype.append,Element.prototype.append=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_append.apply(this,arguments)},old_prepend=Element.prototype.prepend,Element.prototype.prepend=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_prepend.apply(this,arguments)},old_before=Element.prototype.before,Element.prototype.before=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_before.apply(this,arguments)},old_after=Element.prototype.after,Element.prototype.after=function(){let t=arguments[0]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[0]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_after.apply(this,arguments)},old_insertBefore=Element.prototype.insertBefore,Element.prototype.insertBefore=function(){console.log("element.insertBefore intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_insertBefore.apply(this,arguments)},old_replaceWith=Element.prototype.replaceWith,Element.prototype.replaceWith=function(){console.log("element.replaceWith intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_replaceWith.apply(this,arguments)},old_insertAdjacentHTML=Element.prototype.insertAdjacentHTML,Element.prototype.insertAdjacentHTML=function(){let t=arguments[1]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[1]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_insertAdjacentHTML.apply(this,arguments)},old_insertAdjacentText=Element.prototype.insertAdjacentText,Element.prototype.insertAdjacentText=function(){let t=arguments[1]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[1]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_insertAdjacentText.apply(this,arguments)},old_insertAdjacentElement=Element.prototype.insertAdjacentElement,Element.prototype.insertAdjacentElement=function(){let t=arguments[1]+"",e=getURLfromString(t);if(null!=e)StackTrace.get().then(t=>{stackInterceptCallback(t,e)}).catch(t=>{stackInterceptErrBack(t)});else{let e=htmlToElement(t=arguments[1]);if(void 0!==e.href)StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)});else if(void 0!==e.src)StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)});else{let e=t;console.log(e),void 0!==e.href&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==e.src&&StackTrace.get().then(t=>{stackInterceptCallback(t,e.src)}).catch(t=>{stackInterceptErrBack(t)})}}old_insertAdjacentElement.apply(this,arguments)},old_replaceChild=Element.prototype.replaceChild,Element.prototype.replaceChild=function(){console.log("element.replaceChild intercepted.");let t=arguments[0];void 0!==t.href&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.href)}).catch(t=>{stackInterceptErrBack(t)}),void 0!==t.src&&StackTrace.get().then(e=>{stackInterceptCallback(e,t.src)}).catch(t=>{stackInterceptErrBack(t)}),old_replaceChild.apply(this,arguments)};var imagesInViewPort=[]
function isElementInViewport(el){if(typeof jQuery==="function"&&el instanceof jQuery){el=el[0]}
var rect=el.getBoundingClientRect();console.log("alohomoradebug: isElementInViewport window height is "+window.innerHeight)
console.log("alohomoradebug: isElementInViewport window width is "+window.innerWidth)
let vertInView=rect.top<=window.innerHeight&&rect.bottom>rect.top&&rect.top>=0;let horzInView=rect.left<=window.innerWidth&&rect.right>rect.left&&rect.left>=0;return vertInView&&horzInView}
function isAnyPartOfElementInViewport(el){var rect=el.getBoundingClientRect();var windowHeight=(window.innerHeight);var windowWidth=(window.innerWidth);console.log("alohomoradebug: window height is "+windowHeight)
console.log("alohomoradebug: window width is "+windowWidth)
var vertInView=(rect.top<windowHeight)&&((rect.top+rect.height)>=0);var horInView=(rect.left<windowWidth)&&((rect.left+rect.width)>=0);return(vertInView&&horInView)}
function getCriticalRequests(){importantRequests=[]
importantRequests=imagesInViewPort.map((url)=>(url));urlRequestors.forEach((k)=>{if(imagesInViewPort.includes(k.url)){importantRequests=importantRequests.concat(k.initiator)}})
return importantRequests}
function findAndPrintImagesInViewport(ele){ele.querySelectorAll('*').forEach(function(node){if(node.tagName=="IMG"){let url=null;console.log("alohomoradebug checking node "+JSON.stringify(node))
if(isElementInViewport(node)){console.log("alohomoradebug: element is in viewport")
if(typeof node.href!='undefined'){url=node.href}
if(typeof node.src!='undefined'){url=node.src}
if(url!=null){imagesInViewPort.push(url)}}else{console.log("alohomoradebug: element not in viewport")}}});let answer=getCriticalRequests()
console.log("alohomoradebug: this is the answer")
console.log(JSON.stringify({'alohomora_output':answer}))
console.log("alohomoradebug: that was the the answer")}
window.addEventListener('load',(event)=>{console.log("alohomoradebug: extracting critical elements")
document.querySelectorAll("iframe").forEach((ele)=>{var iframeID=ele.id;iframeElement=document.getElementById(iframeID)
if(isAnyPartOfElementInViewport(iframeElement)){var innerDoc=(iframeElement.contentDocument)?iframeElement.contentDocument:iframeElement.contentWindow.document;findAndPrintImagesInViewport(innerDoc)}});findAndPrintImagesInViewport(document)})
    """
    soup.html.insert(0, critical_catcher)
    soup.html.insert(0, stack_trace_dependency)
    return str(soup)


@contextlib.contextmanager
def start_server(
    replay_dir: str,
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    policy: Optional[Policy] = None,
    extract_critical_requests: Optional[bool] = False,
):
    """
    Reads the given replay directory and sets up the NGINX server to replay it. This function also
    creates the DNS servers, Interfaces, and writes all necessary temporary files.

    :param replay_dir: The directory to replay (should be mahimahi-recorded)
    :param cert_path: The path to the SSL certificate for the HTTP/2 NGINX server
    :param key_path: The path to the SSL key for the HTTP/2 NGINX server
    :param policy: The path to the push/preload policy to use for the server
    """
    log = logger.with_namespace("replay_server")
    push_policy = policy.as_dict["push"] if policy else {}
    preload_policy = policy.as_dict["preload"] if policy else {}

    # Load the file store into memory
    if not os.path.isdir(replay_dir):
        raise NotADirectoryError(f"{replay_dir} is not a directory")
    filestore = FileStore(replay_dir)

    # Create host-ip mapping
    hosts = filestore.hosts
    interfaces = Interfaces(hosts)
    host_ip_map = interfaces.mapping

    # Save files and create nginx configuration
    config = Config()
    with tempfile.TemporaryDirectory() as file_dir:
        log.debug("storing temporary files in", file_dir=file_dir)

        for host, files in filestore.files_by_host.items():
            log.info("creating host", host=host, address=host_ip_map[host])
            uris_served = set()

            # Create a server block for this host
            server = config.http_block.add_server(
                server_name=host, server_addr=host_ip_map[host], cert_path=cert_path, key_path=key_path, root=file_dir
            )

            for file in files:
                # Handles the case where we may have duplicate URIs for a single host
                # or where URIs in nginx cannot be too long
                if file.uri in uris_served or len(file.uri) > 3600 or len(file.headers.get("location", "")) > 3600:
                    continue

                uris_served.add(file.uri)
                log.debug(
                    "serve",
                    file_name=file.file_name,
                    status=file.status,
                    method=file.method,
                    uri=file.uri,
                    host=file.host,
                )

                # Create entry for this resource
                if file.status < 300:
                    loc = server.add_location_block(
                        uri=file.uri, file_name=file.file_name, content_type=file.headers.get("content-type", None)
                    )
                elif "location" in file.headers:
                    loc = server.add_location_block(uri=file.uri, redirect_uri=file.headers["location"])
                else:
                    log.warn("skipping", file_name=file.file_name, method=file.method, uri=file.uri, host=file.host)
                    continue

                if extract_critical_requests:
                    # if this is an html file, then we want to insert our snippet here
                    # to extract critical requests.
                    log.debug("injecting critical request extractor")
                    if file.headers.get("content-type", "") == "text/html":
                        uncompressed_body = file.body
                        gzipped_file = False
                        if "gzip" in file.headers.get("content-encoding"):
                            gzipped_file = True
                            uncompressed_body = gzip.GzipFile(fileobj=BytesIO(uncompressed_body)).read()
                        uncompressed_body = prepend_javascript_snippet(uncompressed_body)
                        if gzipped_file:
                            out = BytesIO()
                            with gzip.GzipFile(fileobj=out, mode="wb") as f:
                                f.write(uncompressed_body.encode())
                            file.body = out.getvalue()
                        else:
                            file.body = uncompressed_body
                else:
                    log.debug("not injecting critical request extractor")

                # Save the file's body to file
                file_path = os.path.join(file_dir, file.file_name)
                with open(os.open(file_path, os.O_CREAT | os.O_WRONLY, 0o644), "wb") as f:
                    f.write(file.body)

                # Add headers
                for key, value in file.headers.items():
                    loc.add_header(key, value)

                # Look up push and preload policy
                full_source = f"https://{file.host}{file.uri}"
                push_res_list = push_policy.get(full_source, push_policy.get(full_source + "/", []))
                preload_res_list = preload_policy.get(full_source, preload_policy.get(full_source + "/", []))

                for res in push_res_list:
                    path = urlparse(res["url"]).path
                    log.debug("create push rule", source=file.uri, push=path)
                    loc.add_push(path)
                for res in preload_res_list:
                    log.debug("create preload rule", source=file.uri, preload=res["url"], type=res["type"])
                    loc.add_preload(res["url"], res["type"])

        # Save the nginx configuration
        conf_file = os.path.join(file_dir, "nginx.conf")
        log.debug("writing nginx config", conf_file=conf_file)
        with open(conf_file, "w") as f:
            f.write(str(config))

        # Create the interfaces, start the DNS server, and start the NGINX server
        with interfaces:
            with DNSServer(host_ip_map):
                # If wait lasts for more than 0.5 seconds, a TimeoutError will be raised, which is okay since it
                # means that nginx is running successfully. If it finishes sooner, it means it crashed and
                # we should raise an exception
                try:
                    proc = subprocess.Popen(
                        ["/usr/local/openresty/nginx/sbin/nginx", "-c", conf_file], stdout=sys.stderr, stderr=sys.stderr
                    )
                    proc.wait(0.5)
                    raise RuntimeError("nginx exited unsuccessfully")
                except subprocess.TimeoutExpired:
                    yield
                finally:
                    proc.terminate()
