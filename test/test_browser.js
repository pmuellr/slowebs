/*
#-----------------------------------------------------------------------------
# The MIT License
# 
# Copyright (c) 2009 Patrick Mueller
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-----------------------------------------------------------------------------
*/

//----------------------------------------------------------------------------
var output_div = document.getElementById("output");

//----------------------------------------------------------------------------
function html_escape(string) {
    return string.
        replace(/&/g, "&amp;").
        replace(/</g, "&lt;").
        replace(/>/g, "&gt;");
}

//----------------------------------------------------------------------------
function log(text) {
    output_div.innerHTML += text;
}

function log_error(text) {
    log("<li><span class='error'>" + text + "</span>");
}

function log_success(text) {
    log("<li><span class='success'>" + text + "</span>");
}

function log_note(text) {
    log("<li><span class='note'>" + text + "</span>");
}

//----------------------------------------------------------------------------
function http_get(uri, headers) {
    if (!headers) headers = [];
    
    var xhr = new XMLHttpRequest();
    
    xhr.open("GET", uri, false);
    for (var i=0; i<headers.length; ++i) {
        xhr.setRequestHeader(headers[i][0], headers[i][1]);
    }
    xhr.send(null);
    
    return xhr;
}

//----------------------------------------------------------------------------
function http_put(uri, headers, contents) {
    if (!headers) headers = [];
    
    var xhr = new XMLHttpRequest();
    
    xhr.open("PUT", uri, false);
    for (var i=0; i<headers.length; ++i) {
        xhr.setRequestHeader(headers[i][0], headers[i][1]);
    }
    xhr.send(contents);
    
    return xhr;
}

var passed = true;

//----------------------------------------------------------------------------
function run_test(func) {
    try {
        func();
        log_success("<tt>passed: </tt><b>" + func.name + "()</b>");
    }
    catch(e) {
        passed = false;
        
        var name    = e.name    || "???";
        var message = e.message || "???";
        
        log_error("<tt>failed: </tt><b>" + func.name + "()</b>: " + name + ": " + message);
    }
}

//----------------------------------------------------------------------------
function assert_equals(expected, actual) {
    if (expected == actual) return;
    
    throw {
        name: "AssertionEqualsFailure",
        message: "assert_equals(" + expected + ", " + actual + ")"
    };
}

//----------------------------------------------------------------------------
function assert_true(expression) {
    if (expression) return;

    throw {
        name: "AssertionTrueFailure",
        message: "assert_true(" + expression + ")"
    };
}

//----------------------------------------------------------------------------
log("<p>Starting Tests");
log("<ul>");

//----------------------------------------------------------------------------
run_test(function list_dirs() {
    var xhr = http_get("/");

    assert_equals(200, xhr.status);
    assert_equals("application/json", xhr.getResponseHeader("Content-Type"));
    
    var dir = JSON.parse(xhr.responseText).dir;
    assert_equals(3, dir.length);
    
    var xhr = http_get("/a-dir/");

    assert_equals(200, xhr.status);
    assert_equals("application/json", xhr.getResponseHeader("Content-Type"));
    
    var dir = JSON.parse(xhr.responseText).dir;
    assert_equals(0, dir.length);
});

//----------------------------------------------------------------------------
run_test(function list_redirect() {
    var xhr = http_get("/a-dir");

    assert_equals(200, xhr.status);
    assert_equals("application/json", xhr.getResponseHeader("Content-Type"));
    
    var dir = JSON.parse(xhr.responseText).dir;
    assert_equals(0, dir.length);
});

//----------------------------------------------------------------------------
run_test(function create_file() {
    var file_contents = "some interesting tidbits";
    var headers       = [ ["If-None-Match", "*"] ];
    var file_uri      = "/a-dir/file-1.txt";
    var xhr = http_put(file_uri, headers, file_contents);

    assert_equals(201, xhr.status);
    var etag = xhr.getResponseHeader("ETag");
    assert_true(etag);

    xhr = http_get(file_uri);
    assert_equals(200, xhr.status);
    var etag_get = xhr.getResponseHeader("ETag");
    assert_equals(etag, etag_get);
    assert_equals(file_contents, xhr.responseText);
});

//----------------------------------------------------------------------------
run_test(function update_file() {
    var file_uri = "/a-dir/file-1.txt";
    var xhr      = http_get(file_uri);
    assert_equals(200, xhr.status);
    
    var etag     = xhr.getResponseHeader("ETag");
    var contents = xhr.responseText;
    
    var new_contents  = contents + " - even more!";
    var headers       = [ ["If-Match", etag] ];
    var xhr = http_put(file_uri, headers, new_contents);
    assert_equals(200, xhr.status);

    var xhr = http_get(file_uri);
    assert_equals(200, xhr.status);
    assert_equals(new_contents, xhr.responseText);
});

//----------------------------------------------------------------------------
run_test(function get_cached() {
    var file_uri = "/a-dir/file-1.txt";
    var xhr      = http_get(file_uri);
    assert_equals(200, xhr.status);
    
    var etag = xhr.getResponseHeader("ETag");
    
    var headers = [ ["If-None-Match", etag] ];
    var xhr     = http_get(file_uri, headers);
    assert_equals(304, xhr.status);
});

//----------------------------------------------------------------------------
run_test(function write_final_result() {
    var xhr = http_put(
        "/test_browser.results.txt", 
        [
            ["If-None-Match", "*"],
        ],
        (passed ? "OK" : "some tests failed")
    );

    assert_equals(201, xhr.status);
});

//----------------------------------------------------------------------------
log("</ul>");
log("<p>Tests Completed: <b>" + (passed ? "Pass" : "Failure") + "</b>");
