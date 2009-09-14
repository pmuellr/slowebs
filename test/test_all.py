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
import sys
import tempfile
import unittest

import utils

#-------------------------------------------------------------------
# change to directory this file lives in
#-------------------------------------------------------------------
gotoDir = os.path.dirname(sys.argv[0])
if gotoDir != "": os.chdir(gotoDir)

#-------------------------------------------------------------------
# parse args
#-------------------------------------------------------------------
if len(sys.argv) < 3:
    print "Expecting parameters [port] [mimetypes]"
    sys.exit()
    
port      = sys.argv[1]
mimetypes = sys.argv[2]

try: 
    port = int(port)
except:
    print "port argument was not numeric: %s" % port
    sys.exit()
    
if (port <= 0) or (port >= 65536):
    print "port argument should be between 1 and 65545"
    sys.exit()

if not os.path.exists(mimetypes):
    print "mimetypes file does not exist: %s" % mimetypes
    sys.exit()

os.environ["TEST.PORT"]      = str(port)
os.environ["TEST.ROOT"]      = tempfile.mkdtemp()
os.environ["TEST.MIMETYPES"] = mimetypes

#-------------------------------------------------------------------
# initialize variables
#-------------------------------------------------------------------
suite  = unittest.TestSuite()
result = unittest.TestResult()
runner = unittest.TextTestRunner(verbosity=2)
    
#-------------------------------------------------------------------
# run tests in the listed modules
#-------------------------------------------------------------------

moduleNames = """
    test_list
    test_redirect
    test_read
    test_write
    test_cross_origin
    test_browser
""".split()

modules = [__import__(moduleName) for moduleName in moduleNames]

for module in modules: 
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))

server = utils.Server()
server.start()

try:
    runner.run(suite)
finally:
    server.stop()
    utils.delete_dir("")
    