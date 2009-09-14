slowebs - Simple LOcal WEB Server
=================================

Patrick Mueller  
[pmuellr@yahoo.com](mailto:pmuellr@yahoo.com)

Summary
-------

<b>`slowebs`</b> is a simple HTTP server designed to be used on your
development computer, to serve files up for a web browser running on your
development computer. Besides of course handling reading files via HTTP GET,
it handles file writing via HTTP PUT and directory listing via HTTP GET.

<b>`slowebs`</b> can be run at an arbitrary tcp/ip port, but is hardcoded to
be bound to `localhost`, to keep security simple. Only you can access it.
Presumably.

Rationale
---------

I've been wanting to write some browser-based development tools, but to make
them useful, I need to be able to write files, and list directories. Which is
what <b>`slowebs`</b> does. At first I thought - "it should do everything",
and by everything, I was thinking every file-related management task besides
read/write/list, including `cp`, `move`, `mkdir`, `rmdir`, and of course, most
importantly, SCM commands.

But that's a lot of work. And it's not clear how pleasing of an HTTP interface
I could make for some of that stuff. And people already have their favorite
tools to do all that sort of file management stuff. So I didn't do it.

Invocation
----------
    
    usage:
        slowebs <port> <root> <mimetypes>
    where:
        <port>      is the tcp/ip port number to run the http server
        <root>      is the directory to serve as the root for the http server
        <mimetypes> is the apache2 compatible mime.types file
    
All three parameters must be specified.  
    
The `port` parameter is obviously the port the server will be run on, so you
can then access the server via `http://localhost:port`.

The `root` parameter is the directory which will serve as the base directory
for the web server. The directory structure is served up as the hierarchical 
URLs that you would expect.
    
For the `mimetypes` parameter, you'll need a file in the same format as the
Apache httpd `mime.types` file. If you're on a Mac, you can probably find a
mimetypes file in `/etc/apache2/mime.types`. Otherwise, you can download one
here:
<a href="http://svn.apache.org/repos/asf/httpd/httpd/trunk/docs/conf/">http://svn.apache.org/repos/asf/httpd/httpd/trunk/docs/conf/</a>.

As the server runs, it will generate log entries to `stdout`. You can stop the
server by entering a newline (press Enter or Return).

Technical Details
-----------------
    
### What It Doesn't Do

This server only handles reading files via HTTP GET, creating and updating
files via HTTP PUT, and generating directory listings via HTTP GET. It doesn't
do anything else. No creating directories, deleting files, etc.

Other notable non-features:
    
* No security - see the security section below.
    
* Subset of cache validation functionality.  Only ETag-based cache
validation is supported, and only a subset of the possibilities there.
The subsets supported are listed below in the request documentation.

* No auto-mapping directory requests to files like `index.html`.
Directory requests always return a directory listing, or a redirect if
you left off the trailing `"/"` from the URL.

### ETag headers

ETag headers are returned in both HTTP GET and PUT responses, except for GETs
that resolve to directory listings. The ETag header values can be used in
subsequent `If-Match` and `If-None-Match` request headers.

ETag values are strings consisting of the file's date, time and size.
If a file is changed, but the size and time don't change, then the ETag also
(invalidly) won't change.  It's presumed that this won't be a big problem for
a single-user server.

### Cache-Control

The HTTP response header 

        Cache-Control: no-cache

is used with every GET request to try to ensure you are never dealing with
stale files, at least from the browser's standpoint. This means the browser
doesn't cache file the files itself, but you can, if you're using
`XMLHttpRequest`.

Requests Handled
----------------

### Reading Files

Reading files is handled with an HTTP GET request.

The `Content-Type` of the file is determined by the `mime.types` file passed
in.

For cache validation, a `If-None-Match` header may be
used with an ETag value returned by a previous response for the same
resource.  If present, and the ETag passed matches the ETag value for
the file, then a 304 (Not Modified) HTTP status code is returned.  If present,
and the ETag doesn't match the ETag value for the resource, the 
resource is returned as requested.

### Writing Files

Writing files is handled with an HTTP PUT request.

One and only one cache validator *MUST* be used for every PUT request.

When creating a new file, use a cache validator header

        If-None-Match: *
    
When updating an existing file, you should send the ETag of the version of the
file you are expecting is stored on the server with the following header

        If-Match: [ETag value here]

A create request will successfully return a 201 (Created) HTTP status code. An
update request will successfully return a 200 (OK) HTTP status code. A request
which doesn't pass the cache validation test will return a 412 (Precondition
Failed) HTTP status code.

### Listing Directories

Directory listings are obtained with an HTTP GET request to a resource which
resolves to a directory. Canonically, the URL for the GET request must end
with a `"/"` character. However, if the resource requested is a directory, but
doesn't include the a trailing `"/"` in the URL, the request will be
redirected to the proper URL with a 307 (Temporary Redirect) HTTP status code.

Listings are available in HTML and JSON format.  To obtain a JSON formatted
listing, use an `Accept` header with one of `application/json` or `text/json`
as the header value.  To obtain an HTML formatted listing, use
use an `Accept` header with `text/html` as the value.  Other values, including
using no `Accept` will cause JSON to be returned.

For JSON listings, the JSON returned will represent an object with a `"dir"`
key whose value is an array of objects.  Each object represents a file, and
has the following properties:

* `name` - the name of the file
* `is_dir` - true if the file is a directory, false if not
* `date_ms_utc` - the date in seconds since unix epoch
* `date_print_local` - date in local time zone in a printable format
* `date_rfc3339` - date in RFC 3339 format, with a Z suffix (UTC-based)
* `size` - size of the file in bytes

Security
--------

There is little traditional web-based security happening with this server. For
instance, there is no authentication that takes place, such as BasicAuth. This
is mitigated by the fact that the server is bound to your localhost ip
address, and so can only be connected to by a client on the same machine as
the server.

Still, there are concerns. If you are running a multi-user machine, for
instance then this program is not for you, probably.

One of the most insidious hacks opened up here is cross origin requests from a
browser running on the same machine. For instance, if you run <b>`slowebs`</b>
and then use a web browser on the same machine, you may end up browsing a page
on a different machine which includes references back to your machine. For
instance, a page from another machine could include an HTML &lt;img&gt;
element which points into the <b>`slowebs`</b> server. Or a JavaScript file, a
CSS file, a media file, etc, etc.

Of course, there's nothing specific about <b>`slowebs`</b> causing a problem
here; if you run a local apache server, or even a CUPS print server manager
thingee, you are open for the same sorts of attacks.

To help mitigate this potential hole, <b>`slowebs`</b> will check `Referer`
and `Origin` headers on requests to help ensure the top-level request came
from the <b>`slowebs`</b> server.

Is there anything else can we do here?  Let the author now.

History
-------

* 2009/09/13 - version 0.1 - Initial version
