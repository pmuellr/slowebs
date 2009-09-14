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
import unittest

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
    def test_dir(self):
        utils.create_dir("dir1")

        response = self.client.request("GET", "/dir1")
        (status, reason, body, headers) = response

        location = utils.get_header("location", headers)

        self.assertEqual(307, status)
        self.assertEqual("http://localhost:%s/dir1/" % utils.get_port(), location)
        
    #---------------------------------------------------------------
    def test_dir_in_dir(self):
        utils.create_dir("dir1")

        response = self.client.request("GET", "/dir1")
        (status, reason, body, headers) = response

        location = utils.get_header("location", headers)

        self.assertEqual(307, status)
        self.assertEqual("http://localhost:%s/dir1/" % utils.get_port(), location)

        utils.create_dir("dir1/dir2")

        response = self.client.request("GET", "/dir1/dir2")
        (status, reason, body, headers) = response

        location = utils.get_header("location", headers)

        self.assertEqual(307, status)
        self.assertEqual("http://localhost:%s/dir1/dir2/" % utils.get_port(), location)
