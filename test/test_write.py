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
    def test_precondition_failed(self):

        file1contents = "file 1 contents"
        
        headers = {}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        self.assertEqual(412, status)
        
        headers = {"If-None-Match": "*", "If-Match": "*"}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        self.assertEqual(412, status)
        
        headers = {"If-Match": "*"}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        self.assertEqual(412, status)
        
        utils.write_file("file.txt", file1contents)
        
        headers = {"If-None-Match": "*"}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        self.assertEqual(412, status)

    #---------------------------------------------------------------
    def test_dir_not_found(self):

        file1contents = "file 1 contents"

        headers = {"If-None-Match": "*"}
        response = self.client.request("PUT", "/dir1/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        self.assertEqual(404, status)

    #---------------------------------------------------------------
    def test_create(self):
        
        file1contents = "file 1 contents"

        headers = {"If-None-Match": "*"}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        etag = utils.get_header("etag", headers)

        self.assertEqual(201, status)
        self.assertTrue(etag != None)
        
        response = self.client.request("GET", "/file.txt")
        (status, reason, body, headers) = response

        etag_get = utils.get_header("etag", headers)
        
        self.assertEqual(etag_get, etag)

    #---------------------------------------------------------------
    def test_update(self):

        file1contents = "file 1 contents"

        headers = {"If-None-Match": "*"}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        etag1 = utils.get_header("etag", headers)

        self.assertEqual(201, status)
        self.assertTrue(etag1 != None)
        
        file1contents = "file 1 contents - even more!"

        headers = {"If-Match": etag1}
        response = self.client.request("PUT", "/file.txt", headers, file1contents)
        (status, reason, body, headers) = response

        etag2 = utils.get_header("etag", headers)

        self.assertEqual(200, status)
        self.assertTrue(etag1 != etag2)
        
