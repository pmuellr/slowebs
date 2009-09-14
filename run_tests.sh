#!/bin/sh

run-when-changed "test/test_all.py 8001 /etc/apache2/mime.types" *.py test/*.py test/*.html test/*.js
