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
import sys
import time
import shutil
import httplib
import subprocess

#-----------------------------------------------------------------------------
# get shared values
#-----------------------------------------------------------------------------
def get_port():
    return int(os.environ["TEST.PORT"])

def get_root():
    return os.environ["TEST.ROOT"]

def get_mimetypes():
    return os.environ["TEST.MIMETYPES"]

#-----------------------------------------------------------------------------
# model a launchable server
#-----------------------------------------------------------------------------
class Server:
    
    #-------------------------------------------------------------------------
    # initialize
    #-------------------------------------------------------------------------
    def __init__(self):
        self.port      = str(get_port())
        self.root      = get_root()
        self.mimetypes = get_mimetypes()
    
    #-------------------------------------------------------------------------
    # start a server
    #-------------------------------------------------------------------------
    def start(self):
#        print "Server.start():"
        args = ("python", "../slowebs.py", self.port, self.root, self.mimetypes)
        self.process = subprocess.Popen(args, 
            executable="python", 
            stdin=subprocess.PIPE,
            stdout=sys.stdout,
            stderr=sys.stderr,
            )
        time.sleep(1)
        
    #-------------------------------------------------------------------------
    # shutdown a server
    #-------------------------------------------------------------------------
    def stop(self):
#        print "Server.stop():"
        try:
            self.process.stdin.write("\n")
        except:
            pass
        
        status = self.process.wait()
        delete_dir(self.root)
    
#-----------------------------------------------------------------------------
# a reusable client for the server
#-----------------------------------------------------------------------------
class Client:

    #-------------------------------------------------------------------------
    # initialize
    #-------------------------------------------------------------------------
    def __init__(self):
        self.port = get_port()
        
    #-------------------------------------------------------------------------
    # issue a request, returns (status, reason, body, headers)
    #-------------------------------------------------------------------------
    def request(self, method, url, headers={}, body=""):
#        print "Client.request():"
        connection = httplib.HTTPConnection("localhost", self.port)
        connection.request(method, url, body, headers)
        response = connection.getresponse()
        
        result = (
            response.status,
            response.reason,
            response.read(),
            response.getheaders(),
            )

        connection.close()
        
        return result

#-----------------------------------------------------------------------------
# get server url base
#-----------------------------------------------------------------------------
def get_server_url_base():
    if get_port() == "80":
        return "http://localhost/"
    else:
        return "http://localhost:%s/" % get_port()

#-----------------------------------------------------------------------------
# get a file name from the root
#-----------------------------------------------------------------------------
def get_file_name(file_name):
    return os.path.join(get_root(), file_name)

#-----------------------------------------------------------------------------
# create a directory
#-----------------------------------------------------------------------------
def create_dir(dir_name):
    dir_name = get_file_name(dir_name)
    
    if os.path.isdir(dir_name): return
    if os.path.exists(dir_name): raise RuntimeError, "cannot create directory '%s', already exists as non-directory" % dir_name
    
    os.makedirs(dir_name)
        
#-----------------------------------------------------------------------------
# create a directory
#-----------------------------------------------------------------------------
def delete_dir(dir_name):
    dir_name = get_file_name(dir_name)

    if not os.path.exists(dir_name): return

    shutil.rmtree(dir_name)

#-----------------------------------------------------------------------------
# write a file
#-----------------------------------------------------------------------------
def write_file(file_name, contents):
    file_name = get_file_name(file_name)
    ofile = file(file_name, "w")
    ofile.write(contents)
    ofile.close()

#-----------------------------------------------------------------------------
# read a file
#-----------------------------------------------------------------------------
def read_file(file_name):
    file_name = get_file_name(file_name)
    if not os.path.exists(file_name): return None
    
    ifile = file(file_name, "r")
    contents = ifile.read()
    ifile.close()
    
    return contents

#-----------------------------------------------------------------------------
# get a header value
#-----------------------------------------------------------------------------
def get_header(key, headers):

    for (tkey, val) in headers:
        if tkey == key: return val

    return None
    
#-----------------------------------------------------------------------------
# dump a response
#-----------------------------------------------------------------------------
def dump_response(response):
    (status, reason, body, headers) = response
    
    print "response:"
    print "   status: %s" % status
    print "   reason: %s" % reason
    print "   headers(%d):" % len(headers)
    for (key, val) in headers:
       print "      %s: %s" % (key, val)
    print "   body:"
    print "   -----"
    print body
    print "   -----"
    print 
