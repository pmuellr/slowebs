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
    def test_simple(self):

        file1contents = "file 1 contents"
        utils.write_file("file.txt", file1contents)
        
        response = self.client.request("GET", "/file.txt")
        (status, reason, body, headers) = response

        content_length = utils.get_header("content-length", headers)
        etag           = utils.get_header("etag",           headers)

        self.assertEqual(200, status)
        self.assertEqual(file1contents, body)
        self.assertEqual(len(file1contents), int(content_length))
        self.assertTrue(etag != None)
        
    #---------------------------------------------------------------
    def test_simple_in_dir(self):

        utils.create_dir("a-dir")
        
        file1contents = "file 1 contents"
        utils.write_file("a-dir/file.txt", file1contents)

        response = self.client.request("GET", "/a-dir/file.txt")
        (status, reason, body, headers) = response

        content_length = utils.get_header("content-length", headers)
        etag           = utils.get_header("etag",           headers)
        
        etag_pattern = re.compile(r'^"[^"]+"$')

        self.assertEqual(200, status)
        self.assertEqual(file1contents, body)
        self.assertEqual(len(file1contents), int(content_length))
        self.assertTrue(etag != None)
        self.assertTrue(etag_pattern.match(etag) != None)

    #---------------------------------------------------------------
    def test_not_found(self):

        response = self.client.request("GET", "/file.txt")
        (status, reason, body, headers) = response
        self.assertEqual(404, status)

        response = self.client.request("GET", "/a-dir/file.txt")
        (status, reason, body, headers) = response
        self.assertEqual(404, status)

    #---------------------------------------------------------------
    def test_etag_changed(self):

        file1contents = "file 1 contents"
        utils.write_file("file.txt", file1contents)
        
        response = self.client.request("GET", "/file.txt")
        (status, reason, body, headers) = response

        etag1 = utils.get_header("etag", headers)

        file1contents = "file 1 contents - even more!"
        utils.write_file("file.txt", file1contents)

        response = self.client.request("GET", "/file.txt")
        (status, reason, body, headers) = response

        etag2 = utils.get_header("etag", headers)

        self.assertTrue(etag1 != etag2)
        
    #---------------------------------------------------------------
    def test_ifnonematch(self):

        file1contents = "file 1 contents"
        utils.write_file("file.txt", file1contents)

        response = self.client.request("GET", "/file.txt")
        (status, reason, body, headers) = response

        etag = utils.get_header("etag", headers)

        headers = {"If-None-Match": etag}
        response = self.client.request("GET", "/file.txt", headers)
        (status, reason, body, headers) = response
        
        self.assertEqual(status, 304)                

        file1contents = "file 1 contents - even more!"
        utils.write_file("file.txt", file1contents)

        headers = {"If-None-Match": etag}
        response = self.client.request("GET", "/file.txt", headers)
        (status, reason, body, headers) = response

        self.assertEqual(status, 200)
        self.assertEquals(file1contents, body)