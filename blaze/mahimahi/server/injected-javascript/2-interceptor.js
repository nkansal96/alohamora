function htmlToElement(html) {
    console.log("in html to element")
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


let urlRequestors = [];

let stackInterceptCallback = function (stackframes, url) {
    console.log("in stack intercept callback")
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

let stackInterceptErrBack = function(err) { console.log(err.message); };

let openOrig = window.XMLHttpRequest.prototype.open;
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
    let url = arguments[0]
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
    let element = htmlToElement(str)
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
    let element = htmlToElement(str)
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
        let element = value
        let url = getURLfromString(element)
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
    let e = arguments[0]
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
    let element = arguments[0] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        let e = htmlToElement(element)
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
            let e = element
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
    let element = arguments[0] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        let e = htmlToElement(element)
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
            let e = element
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
    let element = arguments[0] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        let e = htmlToElement(element)
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
            let e = element
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
    let element = arguments[0] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[0];
        let e = htmlToElement(element)
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
            let e = element
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
    let e = arguments[0]
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
    let e = arguments[0]
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
    let element = arguments[1] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[1];
        let e = htmlToElement(element)
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
            let e = element
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
    let element = arguments[1] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[1];
        let e = htmlToElement(element)
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
            let e = element
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
    let element = arguments[1] + ""
    let url = getURLfromString(element)
    if (url != null) {
        StackTrace.get()
        .then(function(stackframes) {
            stackInterceptCallback(stackframes, url);
        }).catch(function(err) {
            stackInterceptErrBack(err);
        }) 
    } else {
        element = arguments[1];
        let e = htmlToElement(element)
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
            let e = element
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
    let e = arguments[0]
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
    let url = null;
    try {
        if (element.indexOf("<") >= 0 && element.indexOf(">") >= 0) { // has < and >, so could be an html tag
            // don't want to use the htmlToElement function as that will recurse
            element = element.replace("= ", "=").replace("= ", "=")
            element = element.replace(/["']/g, "")
            let start = element.indexOf("src=")
            if (start >= 0) {
                let end = element.indexOf(" ", start)
                if (end < 0) {
                    end = element.indexOf(">", start)
                }
                let s = element.substring(start, end)
                s = s.replace(" ", "")
                s= s.replace("src=", "")
                url = s.trim()
            } else {
                start = element.indexOf("href=")
                if(start >= 0) {
                    let end = element.indexOf(" ", start)
                    if (end < 0) {
                        end = element.indexOf(">", start)
                    }
                    let s = element.substring(start, end)
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