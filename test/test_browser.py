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
import unittest
import webbrowser

import utils

false = False
true  = True

#-------------------------------------------------------------------
class Test(unittest.TestCase):

    #---------------------------------------------------------------
    def setUp(self):
        print
        self.client = utils.Client()
        utils.delete_dir("")
        utils.create_dir("")
        
    def tearDown(self):
        utils.delete_dir("")

    #---------------------------------------------------------------
    def test_browser(self):
        src_dir = os.path.dirname(__file__)
        dst_dir = utils.get_root()
        
        shutil.copyfile("%s/test_browser.html" % src_dir, "%s/test_browser.html" % dst_dir)
        shutil.copyfile("%s/test_browser.js"   % src_dir, "%s/test_browser.js"   % dst_dir)

        utils.create_dir("a-dir")
        
        webbrowser.open("http://localhost:%d/test_browser.html" % utils.get_port())
        
        print "waiting for response from browser test: "
        wait = 5
        while wait > 0:
            contents = utils.read_file("test_browser.results.txt")
            if contents: break
            
            print "%d" % wait
            time.sleep(1)
            wait -= 1

        self.assertTrue(contents != None)
        self.assertEquals("OK", contents)
