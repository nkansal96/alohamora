if (!StackTrace) {
    var StackTrace = function () {

    }
    
    StackTrace.prototype.get = function () {
        // console.log("using mock stack trace")
        try {
            throw new Error()
        } catch (err) {
            var fileNames = err.stack.split('\n').map(function(l) {
                // var regExp = /^at (?:.* \()?(.*):\d+:\d+[\n\)]?$/
                var regExp = /((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w-_]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)/
                var matches = regExp.exec(l.trim())
                if (matches != null && matches.length > 1) {
                    return matches[1]
                } else {
                    return null
                }
            }).filter(function(x) {
                return x != null;
            })
            var returnObject = fileNames.map(function(ele) {
                return {fileName: ele};
            })
            return Promise.resolve(returnObject)
        }
    }

    window.StackTrace = new StackTrace()
}

function htmlToElement(html) {
    // console.log("in html to element")
    try {
        var template = document.createElement('template');
        if (typeof html.trim != "undefined") {
            html = html.trim(); // Never return a text node of whitespace as the result
        }
        template.innerHTML = html;
        return template.content.firstChild;
    } catch(error) {
        return html
    }
    
}


/* XHR intercept */


var urlRequestors = [];

var stackInterceptCallback = function (stackframes, url) {
    // if we have a stack, and the url we are currently looking at is not for a stacktrace related request
    try {
        if(stackframes.length > 0 && url != 'https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js') {
            // if the request was not initiated by stacktrace
            if ('https://cdnjs.cloudflare.com/ajax/libs/stacktrace.js/2.0.1/stacktrace.min.js' != stackframes[stackframes.length - 1].fileName) {
                urlRequestors.push({
                    'url': url,
                    'initiator': stackframes.map(function(s){return s.fileName;} ) //[[stackframes.length - 1].fileName, stackframes[stackframes.length - 2].fileName],
                })
            }
        }        
    } catch (error) {
        console.log("error caught ", error)
    }

};

var stackInterceptErrBack = function(err) { console.log(err.message); };

var openOrig = window.XMLHttpRequest.prototype.open;
function openReplacement(method, url, async, user, password) {
    this._url = url;
    StackTrace.get()
    .then(function(stackframes) {
        stackInterceptCallback(stackframes, url);
    }).catch(function(err) {
        stackInterceptErrBack(err);
    }) 
    return openOrig.apply(this, arguments);
}

window.XMLHttpRequest.prototype.open = openReplacement;

const _fetch = window.fetch;
window.fetch = function() {
    var url = arguments[0]
    StackTrace.get()
    .then(function(stackframes) {
        stackInterceptCallback(stackframes, url);
    }).catch(function(err) {
        stackInterceptErrBack(err);
    })
    return _fetch.apply(this, arguments)
}

/**document.write intercept */
document.old_write = document.write;

document.write = function (str) {
    var element = htmlToElement(str)
    if(typeof element.href != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, element.href);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    if(typeof element.src != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, element.src);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    document.old_write(str);
};

/**document.writeln intercept */
document.old_writeln = document.writeln;

document.writeln = function (str) {
    var element = htmlToElement(str)
    if(typeof element.href != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, element.href);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    if(typeof element.src != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, element.src);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    document.old_writeln(str);
};

/** *.innerHTML intercept */
(function() {
    
    //Store the original "hidden" getter and setter functions from Element.prototype
    //using Object.getOwnPropertyDescriptor
    var originalSet = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML').set;
    
    Object.defineProperty(Element.prototype, 'innerHTML', {
        set: function (value) {
            // change it (ok)
            var new_value = my_function(value);
            
            //Call the original setter
            return originalSet.call(this, new_value);
        }
    });
    
    function my_function(value) {
        var element = value
        var url = getURLfromString(element)
        if (url != null) {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, url);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        }
        return value
    }
    
})();


/** Element.prototype.appendChild intercept */
old_appendChild = Element.prototype.appendChild;

Element.prototype.appendChild = function () {
    var e = arguments[0]
    if(typeof e.href != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.href);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    if(typeof e.src != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.src);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    old_appendChild.apply(this, arguments);
};

/** Element.prototype.append intercept */
old_append = Element.prototype.append;

Element.prototype.append = function () {
    var element = arguments[0] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_append.apply(this, arguments);
};


/** Element.prototype.prepend intercept */
old_prepend = Element.prototype.prepend;

Element.prototype.prepend = function () {
    var element = arguments[0] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_prepend.apply(this, arguments);
};

/** Element.prototype.before intercept */
old_before = Element.prototype.before;

Element.prototype.before = function () {
    var element = arguments[0] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_before.apply(this, arguments);
};

/** Element.prototype.after intercept */
old_after = Element.prototype.after;

Element.prototype.after = function () {
    var element = arguments[0] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_after.apply(this, arguments);
};


/** Element.prototype.insertBefore intercept */
old_insertBefore = Element.prototype.insertBefore;

Element.prototype.insertBefore = function () {
    var e = arguments[0]
    if(typeof e.href != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.href);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    if(typeof e.src != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.src);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        })
    } 
    old_insertBefore.apply(this, arguments);    
};

/** Element.prototype.after intercept */
// covered by innerHTML

/** Element.prototype.replaceWith intercept */
old_replaceWith = Element.prototype.replaceWith;

Element.prototype.replaceWith = function () {
    var e = arguments[0]
    if(typeof e.href != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.href);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    if(typeof e.src != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.src);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    old_replaceWith.apply(this, arguments);
};

/** Element.prototype.insertAdjacentHTML intercept */
old_insertAdjacentHTML = Element.prototype.insertAdjacentHTML;

Element.prototype.insertAdjacentHTML = function () {
    var element = arguments[1] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[1];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_insertAdjacentHTML.apply(this, arguments);
};

/** Element.prototype.insertAdjacentText intercept */
old_insertAdjacentText = Element.prototype.insertAdjacentText;

Element.prototype.insertAdjacentText = function () {
    var element = arguments[1] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[1];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_insertAdjacentText.apply(this, arguments);
};

/** Element.prototype.insertAdjacentElement intercept */
old_insertAdjacentElement = Element.prototype.insertAdjacentElement;

Element.prototype.insertAdjacentElement = function () {
    var element = arguments[1] + ""
    var url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[1];
        var e = htmlToElement(element)
        if(typeof e.href != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.href);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else if(typeof e.src != 'undefined') {
            StackTrace.get()
            .then(function(stackframes) {
                stackInterceptCallback(stackframes, e.src);
            }).catch(function(err) {
                stackInterceptErrBack(err);
            }) 
        } else {            
            var e = element
            if(typeof e.href != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.href);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
            if(typeof e.src != 'undefined') {
                StackTrace.get()
                .then(function(stackframes) {
                    stackInterceptCallback(stackframes, e.src);
                }).catch(function(err) {
                    stackInterceptErrBack(err);
                }) 
            }
        }
    }
    old_insertAdjacentElement.apply(this, arguments);
};

/** Element.prototype.replaceChild intercept */
old_replaceChild = Element.prototype.replaceChild;

Element.prototype.replaceChild = function () {
    var e = arguments[0]
    if(typeof e.href != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.href);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    if(typeof e.src != 'undefined') {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, e.src);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    }
    old_replaceChild.apply(this, arguments);
};

/** Helpers */

function getURLfromString(element) {
    var url = null;
    try {
        if (element.indexOf("<") >= 0 && element.indexOf(">") >= 0) { // has < and >, so could be an html tag
            // don't want to use the htmlToElement function as that will recurse
            element = element.replace("= ", "=").replace("= ", "=")
            element = element.replace(/["']/g, "")
            var start = element.indexOf("src=")
            if (start >= 0) {
                var end = element.indexOf(" ", start)
                if (end < 0) {
                    end = element.indexOf(">", start)
                }
                var s = element.substring(start, end)
                s = s.replace(" ", "")
                s= s.replace("src=", "")
                url = s.trim()
            } else {
                start = element.indexOf("href=")
                if(start >= 0) {
                    var end = element.indexOf(" ", start)
                    if (end < 0) {
                        end = element.indexOf(">", start)
                    }
                    var s = element.substring(start, end)
                    s = s.replace(" ", "")
                    s = s.replace("href=", "")
                    url = s.trim()
                }
            }
        } 
    } catch (error) {
        return url
    }
    
    return url;
}