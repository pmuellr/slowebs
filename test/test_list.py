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
    def test_empty_list(self):
        response = self.client.request("GET", "/")
        (status, reason, body, headers) = response
        
        self.assertEqual(200, status)
        
        body = eval(body)
        
        self.assertTrue(isinstance(body,dict))
        self.assertEqual(0, len(body["dir"]))

    #---------------------------------------------------------------
    def test_one_file(self):
        
        file1contents = "file 1 contents"
        utils.write_file("file1.txt", file1contents)
        
        response = self.client.request("GET", "/")
#        utils.dump_response(response)
        (status, reason, body, headers) = response
        
        self.assertEqual(200, status)
        
        body = eval(body)
        body = body["dir"]
        
        self.assertTrue(isinstance(body,list))
        self.assertEqual(1, len(body))

        self.assertEqual("file1.txt",        body[0]["name"])
        self.assertEqual(False,              body[0]["is_dir"])
        self.assertEqual(len(file1contents), body[0]["size"])
            
    #---------------------------------------------------------------
    def test_two_files(self):
        
        file1contents = "file 1 contents"
        file2contents = "file 2 contents contents"
        utils.write_file("file1.txt", file1contents)
        utils.write_file("file2.txt", file2contents)

        response = self.client.request("GET", "/")

        (status, reason, body, headers) = response

        self.assertEqual(200, status)

        body = eval(body)
        body = body["dir"]

        self.assertTrue(isinstance(body,list))
        self.assertEqual(2, len(body))

        self.assertEqual("file1.txt",        body[0]["name"])
        self.assertEqual(False,              body[0]["is_dir"])
        self.assertEqual(len(file1contents), body[0]["size"])

        self.assertEqual("file2.txt",        body[1]["name"])
        self.assertEqual(False,              body[1]["is_dir"])
        self.assertEqual(len(file2contents), body[1]["size"])

    #---------------------------------------------------------------
    def test_one_dir(self):
        
        utils.create_dir("dir1")

        response = self.client.request("GET", "/")

        (status, reason, body, headers) = response

        self.assertEqual(200, status)

        body = eval(body)
        self.assertTrue(isinstance(body,dict))
        
        body = body["dir"]
        self.assertEqual(1, len(body))

        self.assertEqual("dir1",         body[0]["name"])
        self.assertEqual(True,           body[0]["is_dir"])

        response = self.client.request("GET", "/dir1/")

        (status, reason, body, headers) = response

        self.assertEqual(200, status)

        body = eval(body)
        body = body["dir"]

        self.assertTrue(isinstance(body,list))
        self.assertEqual(0, len(body))
        
    #---------------------------------------------------------------
    def test_html(self):

        file1contents = "file 1 contents"
        utils.create_dir("dir1")
        utils.write_file("dir1/file1.txt", file1contents)

        response = self.client.request("GET", "/dir1/", {"Accept": "text/html"})
        (status, reason, body, headers) = response
        
        content_type = utils.get_header("content-type", headers)
        
        self.assertEqual(200, status)
        self.assertEqual("text/html", content_type)
        
    #---------------------------------------------------------------
    def test_one_file_in_dir(self):
        
        file1contents = "file 1 contents"
        utils.create_dir("dir1")
        utils.write_file("dir1/file1.txt", file1contents)

        response = self.client.request("GET", "/dir1/")
        (status, reason, body, headers) = response

        self.assertEqual(200, status)

        body = eval(body)
        body = body["dir"]

        self.assertTrue(isinstance(body,list))
        self.assertEqual(1, len(body))

        self.assertEqual("file1.txt",    body[0]["name"])
        self.assertEqual(False,          body[0]["is_dir"])

    #---------------------------------------------------------------
    def test_not_found(self):

        response = self.client.request("GET", "/dir1/")
        (status, reason, body, headers) = response

        self.assertEqual(404, status)

        response = self.client.request("GET", "/dir1/dir2/")
        (status, reason, body, headers) = response

        self.assertEqual(404, status)
