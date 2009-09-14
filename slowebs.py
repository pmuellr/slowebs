#!/usr/bin/env python

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

import os
import re
import sys
import cgi
import time
import urllib
import select
import optparse
import textwrap
import wsgiref.simple_server
import wsgiref.util

#-----------------------------------------------------------------------------
# program constants
#-----------------------------------------------------------------------------
program_name   = os.path.splitext(os.path.basename(sys.argv[0]))[0]
program_vers   = "0.1"

#------------------------------------------------------- ----------------------
# print a message
#-----------------------------------------------------------------------------
use_debug = not True

def debug(message):
    if use_debug: log(message)

#------------------------------------------------------- ----------------------
# print a message
#-----------------------------------------------------------------------------
def log(message):
    print "%s: %s" % (program_name, message)

#-----------------------------------------------------------------------------
# print a message then exit
#-----------------------------------------------------------------------------
def error(message):
    log(message)
    sys.exit()

#-----------------------------------------------------------------------------
# print some help
#-----------------------------------------------------------------------------
def help():
    print "%s %s" % (program_name, program_vers)
    print
    print "usage:"
    print "   %s <port> <root> <mimetypes>" % program_name
    print "where:"
    print "   <port>      is the tcp/ip port number to run the http server"
    print "   <root>      is the directory to serve as the root for the http server"
    print "   <mimetypes> is the apache2 compatible mime.types file"
    print
    print "%s is a Simple LOcal WEB Server, that will make a directory on" % program_name
    print "your file system available via http://localhost:<port>/"

    sys.exit()

#-----------------------------------------------------------------------------
# escape characters for a literal string
#-----------------------------------------------------------------------------
def string_escape(string):
    return string.replace('"', r'\"')

#-----------------------------------------------------------------------------
# parse an apache mime.types file
#-----------------------------------------------------------------------------
def parse_mimetypes(fileName):
    if not os.path.exists(fileName): 
        error("mimetypes file %s not found; try /etc/apache2/mime.types" % fileName)
    
    file = open(fileName)
    lines = file.readlines()
    file.close()
    
    result = {}
    for line in lines:
        line = line.strip()
        if line == "": continue
        if line.startswith("#"): continue
        
        words = line.split()
        mimetype = words[0]
        exts     = words[1:]
        for ext in exts:
            result[ext] = mimetype
        
    return result

#-----------------------------------------------------------------------------
# make sure the path is legal
#-----------------------------------------------------------------------------
def path_check(path):
    debug("path_check(%s)" % path)
    
    if path == "": return True
    if path == "/": return True
    
    parts = path.split("/")
    
    for part in parts:
        if part == ".": return False
        if part == "..": return False
            
    return True

#-----------------------------------------------------------------------------
# dump environment
#-----------------------------------------------------------------------------
def dump_environ(environ):
    keys = environ.keys()
    keys.sort()
    
    max_key_len = 0
    for key in keys:
        if len(key) > max_key_len: 
            max_key_len = len(key)
        
    for key in keys:
        print "%s: %s" % (key.ljust(max_key_len), environ[key])

#-----------------------------------------------------------------------------
# wsgi responder for some HTTP status
#-----------------------------------------------------------------------------
def handler_status(environ, start_response, status, reason, extra_headers=None):
    debug("handler_status(%d, %s)" % (status, reason))
    
    status = '%d %s' % (status, reason.upper())
    headers = [('Content-type','text/plain')]
    headers.append(("Cache-Control", "no-cache"))
    if extra_headers:
        for header in extra_headers:
            headers.append(header)
        
    start_response(status, headers)
    
    return [reason]

#-----------------------------------------------------------------------------
# wsgi responder for 200
#-----------------------------------------------------------------------------
def handler_ok(environ, start_response, etag):
    headers = []
    headers.append(('ETag', etag))
    return handler_status(environ, start_response, 200, "OK")

#-----------------------------------------------------------------------------
# wsgi responder for 201
#-----------------------------------------------------------------------------
def handler_created(environ, start_response, etag):
    headers = []
    headers.append(('ETag', etag))
    return handler_status(environ, start_response, 201, "Created", headers)

#-----------------------------------------------------------------------------
# wsgi responder for 304
#-----------------------------------------------------------------------------
def handler_not_modified(environ, start_response, etag):
    headers = []
    headers.append(('ETag', etag))
    return handler_status(environ, start_response, 304, "Not modified", headers)

#-----------------------------------------------------------------------------
# wsgi responder for 307
#-----------------------------------------------------------------------------
def handler_temporary_redirect(environ, start_response, location):
    headers = []
    headers.append(("Location", location))
    return handler_status(environ, start_response, 307, "Temporary Redirect", headers)

#-----------------------------------------------------------------------------
# wsgi responder for 404
#-----------------------------------------------------------------------------
def handler_not_found(environ, start_response):
    return handler_status(environ, start_response, 404, "Not found")

#-----------------------------------------------------------------------------
# wsgi responder for 400
#-----------------------------------------------------------------------------
def handler_bad_request(environ, start_response):
    return handler_status(environ, start_response, 400, "Bad request")

#-----------------------------------------------------------------------------
# wsgi responder for 403
#-----------------------------------------------------------------------------
def handler_forbidden(environ, start_response):
    return handler_status(environ, start_response, 403, "Forbidden")

#-----------------------------------------------------------------------------
# wsgi responder for 412
#-----------------------------------------------------------------------------
def handler_precondition_failed(environ, start_response):
    return handler_status(environ, start_response, 412, "Precondition failed")

#-----------------------------------------------------------------------------
# wsgi responder for 501
#-----------------------------------------------------------------------------
def handler_not_implemented(environ, start_response):
    return handler_status(environ, start_response, 501, "Not implemented")

#-----------------------------------------------------------------------------
# find the preferred content type from an accept header
#-----------------------------------------------------------------------------
def get_preferred_content_type(available_types, accept_header):
    header_types = [cgi.parse_header(header_type) for header_type in accept_header.split(",")]
    
    for (header_type, parms) in header_types:
        if header_type in available_types: return header_type
        
        header_parts = header_type.split("/")

        for available_type in available_types:
            available_parts = available_type.split("/")
            
            if (header_parts[0] == "*") and (available_parts[1] == header_parts[1]):
                return available_type
        
            if (header_parts[1] == "*") and (available_parts[0] == header_parts[0]):
                return available_type

            if (header_parts[0] == "*") and (header_parts[1] == "*"):
                return available_type
    return None

#-----------------------------------------------------------------------------
# calculate the ETag
#-----------------------------------------------------------------------------
def get_etag(name):
    if not os.path.exists(name): return None
    
    date = os.path.getmtime(name)
    size = os.path.getsize(name)
    return "%d-%d" % (date, size)

#-----------------------------------------------------------------------------
# determine if the specified referer is our server
#-----------------------------------------------------------------------------
def referer_is_self(referer):
    if global_port == 80:
        test = "http://localhost/"
        if referer.find(test) == 0:
            return True

        test = "http://localhost"
        if referer.find(test) == 0:
            return True

    test = "http://localhost:%d/" % global_port
    if referer.find(test) == 0:
        return True

    test = "http://localhost:%d" % global_port
    if referer.find(test) == 0:
        return True

    return False

#-----------------------------------------------------------------------------
# class describing file info
#-----------------------------------------------------------------------------
class File_Info:

    def __init__(self, dir, name):
        self.dir           = dir
        self.name          = name
        self.full_name     = os.path.join(dir,name)
        self.qname          = urllib.quote(name)
        self.exists         = os.path.exists(self.full_name)

        debug("File_Info(%s): %s" % (name, self.full_name))

        if not self.exists: return

        self.is_dir           = os.path.isdir(self.full_name)
        self.size             = os.path.getsize(self.full_name)
        self.size_print       = re.sub(r'(\d{3})(?=\d)', r'\1,', str(self.size)[::-1])[::-1]
        self.date_ms_utc      = os.path.getmtime(self.full_name)
        self.date_print_local = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(self.date_ms_utc))
        self.date_rfc3339     = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.date_ms_utc))

        # self.psize calculation from: http://code.activestate.com/recipes/498181/

#-----------------------------------------------------------------------------
# wsgi responder for redirect adding a / at the end of the URL
#-----------------------------------------------------------------------------
def handler_redirect_with_slash(environ, start_response, match):
    debug("handler_redirect_with_slash()")
    
    protocol = environ["wsgi.url_scheme"]
    host     = environ["REMOTE_HOST"]
    port     = environ["SERVER_PORT"]
    path     = environ["PATH_INFO"]
    verb     = environ["REQUEST_METHOD"]
    
    path = urllib.quote(path)
    
    if   protocol == "http"  and port == "80":  port = ""
    elif protocol == "https" and port == "443": port = ""
    else:                                       port = ":%s" % port
    
    url = "%s://%s%s%s/" % (protocol, host, port, path)
    
    return handler_temporary_redirect(environ, start_response, url)

#-----------------------------------------------------------------------------
# get a directory listing
#-----------------------------------------------------------------------------
def handler_file_list(environ, start_response, match):
    debug("handler_file_list()")
    
    dir_name = match.group(1)
    dir_name = os.path.join(global_root, dir_name)

    if not os.path.isdir(dir_name):
        return handler_not_found(environ, start_response)
    
    available_types = ["application/json", "text/json", "text/html"]
    accept_header = environ.get("HTTP_ACCEPT", "*/*")
    content_type = get_preferred_content_type(available_types, accept_header)

    useJSON = True
    if content_type == "text/html": useJSON = False
    
    files = os.listdir(dir_name)
    files.sort()

    # build array of files, each on is [name, isDir, mDate, size]
    file_infos = []
    for file in files:
        if not path_check(file): continue
        
        file_infos.append(File_Info(dir_name, file))
        
    content = ""
    if useJSON:
        content = '{"dir": [\n'
        for (index, file_info) in enumerate(file_infos):
            is_dir = "false"
            if file_info.is_dir: is_dir = "true"
            content += "   { "
            content +=   '"name": "%s"' % string_escape(file_info.qname)
            content += ', "is_dir": %s'  % is_dir
            content += ', "date_ms_utc": "%d"' % file_info.date_ms_utc
            content += ', "date_print_local": "%s"' % file_info.date_print_local
            content += ', "date_rfc3339": "%s"' % file_info.date_rfc3339
            content += ', "size": %d' % file_info.size
            content += "   } "
            if index + 1 < len(file_infos): content += ","
            content += "\n"
        content += "]}\n"
        
    else:
        header = textwrap.dedent('''\
            <html>
            <head>
            <title>%s: %s</title>
            <style>
            .col-date { 
                padding-left: 3em;
            }
            .col-size { 
                padding-left: 3em;
                text-align:   right;
            }
            tr:nth-child(odd) {
                background: #DDD
            }            
            </style>
            </head>
            <body>
            <h1>%s: %s</h1>
            <table cellpadding=5 cellspacing=0>
            ''' % (program_name, dir_name, program_name, dir_name))

        trailer = textwrap.dedent('''\
            </table>
            </body>
            </html>
            ''')

        content = header
        for file_info in file_infos:
            if file_info.is_dir:
                name = "<a href='%s/'>%s/</a>"
            else:
                name = "<a href='%s'>%s</a>"
                
            name = name % (file_info.qname, file_info.name)
                
            content += "<tr><td>%s<td class='col-date'>%s<td class='col-size'>%s bytes" % (
                name, file_info.date_print_local, file_info.size_print
            )

        content += trailer
    
    status = '200 OK'
    headers = [('Content-type',content_type)]
    headers.append(("Cache-Control", "no-cache"))
    start_response(status, headers)

    if environ["REQUEST_METHOD"] == "HEAD": return [""]

    return [content]

#-----------------------------------------------------------------------------
# read a file
#-----------------------------------------------------------------------------
def handler_file_get(environ, start_response, match):
    debug("handler_file_get()")
    
    file_name = match.group(1)
    file_name = os.path.join(global_root, file_name)
    
    if not os.path.exists(file_name):
        return handler_not_found(environ, start_response)
    
    if os.path.isdir(file_name):
        return handler_redirect_with_slash(environ, start_response, match)
        
    # values may be '"foo-bar-baz"' or '*'
    if_none_match = environ.get("HTTP_IF_NONE_MATCH")
    
    file_etag = '"%s"' % get_etag(file_name)

    if if_none_match and (if_none_match == file_etag):
        return handler_not_modified(environ, start_response, file_etag)
    
    ext = os.path.splitext(file_name)[1]
    if ext == "":
        content_type = "application/octet-stream"
    else:
        ext = ext[1:].lower()
        content_type = global_mimetypes.get(ext, "application/octet-stream")
        
    # // Mon, 17 Aug 2009 07:06:44 GMT
    last_modified = os.path.getmtime(file_name)
    last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(last_modified))
    
    status = '200 OK'
    headers = []
    headers.append(('Last-Modified',last_modified))
    headers.append(('Content-type',content_type))
    headers.append(("Cache-Control", "no-cache"))
    headers.append(("ETag", file_etag))
    start_response(status, headers)
    
    file = open(file_name)
    
    if environ["REQUEST_METHOD"] == "HEAD": return [""]
    
    return list(wsgiref.util.FileWrapper(file))

#-----------------------------------------------------------------------------
# write a file
#-----------------------------------------------------------------------------
def handler_file_put(environ, start_response, match):
    debug("handler_file_put()")

    content_length = environ.get("CONTENT_LENGTH", None)
    if not content_length: 
        return handler_bad_request(environ, start_response)
        
    try:
        content_length = int(content_length)
    except:
        return handler_bad_request(environ, start_response)
    
    # values may be '"foo-bar-baz"' or '*'
    if_match      = environ.get("HTTP_IF_MATCH", None)
    if_none_match = environ.get("HTTP_IF_NONE_MATCH", None)
    
#    print "handler_file_put():"
#    print "   if_match:      %s" % if_match
#    print "   if_none_match: %s" % if_none_match

    if not if_match and not if_none_match:
        return handler_precondition_failed(environ, start_response)

    if if_match and if_none_match:
        return handler_precondition_failed(environ, start_response)

    file_name = match.group(1)
    file_name = os.path.join(global_root, file_name)

    dir_name = os.path.dirname(file_name)
    if not os.path.exists(dir_name) or not os.path.isdir(dir_name):
        return handler_not_found(environ, start_response)
        
    file_etag = get_etag(file_name)
    if file_etag: file_etag = '"%s"' % file_etag

    if not os.path.exists(file_name):
        creating = True
        if if_none_match == "*":
            pass
        else:
            return handler_precondition_failed(environ, start_response)

    elif os.path.exists(file_name):
        creating = False
        if if_match == file_etag:
            pass
        else:
            return handler_precondition_failed(environ, start_response)
    
    i_file = environ.get("wsgi.input", None)
    if not i_file:
        return handler_bad_request(environ, start_response)
        
    try:
        o_file = file(file_name, "w")
    except:
        return handler_forbidden(environ, start_response)
        
    content = i_file.read(content_length)
    o_file.write(content)
        
    i_file.close()
    o_file.close()

    file_etag = '"%s"' % get_etag(file_name)
        
    if creating:
        return handler_created(environ, start_response, file_etag)
    else:
        return handler_ok(environ, start_response, file_etag)

#-----------------------------------------------------------------------------
# main wsgi entry point - dispatch request based on route
#-----------------------------------------------------------------------------
def app_main(environ, start_response):
    if not True: dump_environ(environ)
    
    path   = environ["PATH_INFO"]
    method = environ["REQUEST_METHOD"]
    
    origin  = environ.get("HTTP_ORIGIN", None)
    referer = environ.get("HTTP_REFERER", None)
    
    if origin:
        if not referer_is_self(origin):
            return handler_forbidden(environ, start_response)

    if referer:
        if not referer_is_self(referer):
            return handler_forbidden(environ, start_response)

    path = urllib.unquote(path)
    if not path_check(path): 
        return handler_not_found(environ, start_response)
        
    for (route_method, route_pattern, route_function) in global_routes:
        if (route_method != "*") and (route_method != method): continue

        match = route_pattern.match(path)
        if match:
            return route_function(environ, start_response, match)

    return handler_not_implemented(environ, start_response)

#-----------------------------------------------------------------------------
# routes for this application
#-----------------------------------------------------------------------------
global_routes = [
    [ "HEAD",    r'^/?(.*)/$',        handler_file_list ],
    [ "GET",     r'^/?(.*)/$',        handler_file_list ],
    [ "HEAD",    r'^/?(.*)$',         handler_file_get ],
    [ "GET",     r'^/?(.*)$',         handler_file_get ],
    [ "PUT",     r'^/?(.*)$',         handler_file_put ],
]

global_routes = [
    (method, re.compile(pattern), function) for 
        (method, pattern, function) in global_routes
]

#-----------------------------------------------------------------------------
# main program
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# parse options
#-----------------------------------------------------------------------------
opt_parser = optparse.OptionParser()
(options, args) = opt_parser.parse_args()

if (len(args) < 3):
    help()
    
global_port      = args[0]
global_root      = args[1]
global_mimetypes = args[2]

try: 
    global_port = int(global_port)
except:
    error("port argument was not numeric: %s" % global_port)
    
if (global_port <= 0) or (global_port >= 65536):
    error("port argument should be between 1 and 65545")

if not os.path.exists(global_root):
    error("root directory does not exist: %s" % global_root)

if not os.path.isdir(global_root):
    error("root directory is actually a file: %s" % global_root)
    
global_root = os.path.abspath(global_root)

global_mimetypes = parse_mimetypes(global_mimetypes)

#-----------------------------------------------------------------------------
# create the server, print some help
#-----------------------------------------------------------------------------
global_httpd = wsgiref.simple_server.make_server('localhost', global_port, app_main)

print "Serving HTTP for root %s as http://localhost:%d/" % (global_root, global_port)
print "Press Enter to stop the server."
print

#-----------------------------------------------------------------------------
# process server requests in a loop, waiting also for stdin input
# note: I don't think this works on windows
#-----------------------------------------------------------------------------
h_stdin = sys.stdin.fileno()
h_httpd = global_httpd.fileno()
while True:
    test_handles = [h_stdin, h_httpd]
    
    (ready_read, ready_write, ready_error) = select.select(test_handles, [], test_handles)
    
    if ready_error:
        print
        if h_stdin in ready_error: print "Error reading stdin."
        if h_httpd in ready_error: print "Error reading socket."
        sys.exit()
        
    if h_stdin in ready_read:
        os.close(h_httpd)
        print "Shutting down."
        sys.stdin.readline()
        sys.exit()

    if h_httpd in ready_read:
        global_httpd.handle_request()
