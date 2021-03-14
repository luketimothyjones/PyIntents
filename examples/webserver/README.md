Multithreaded webserver that supports GET, POST, and PUT. Includes parsing for URL parameters and form data. No external dependencies (aside from pyretree). This is just a fun example project; while I have tried to make it safe there are likely exploitable flaws. Should not be used in production.

----
<br>

Use `<% head %> ... <% /head %>` to add to HTML head in a template file (see [home.html](https://github.com/luketimothyjones/pyretree/tree/main/examples/webserver/www-root/templates/home.html)) or call to `build_html_response()`.

See [example_server.py](https://github.com/luketimothyjones/pyretree/tree/main/examples/webserver/example_server.py) for an example implementation.

----
<br>

A server is created by creating an instance of `webserver.ThreadedWebServer(host='localhost', port=5000)`.  
Once you have added all of your paths, call `server.run_forever()` to run the server.

----
<br>

Decorate functions with `@server.add_path('GET:/my-page')` to hook them to that path.  

Paths are in the format `HTTP_VERB:path`. For example, `GET:/my-page`, `PUT:/my-page`, `POST:/my-page`.  

Use `<some_var>` and `<some_var=foo>` to extract values from the path. For example, `GET:/blog/posts/<post_id>`. These will be passed as positional arguments to the annoatated function.  

Functions expecting to receive URL parameters should have a `url_params` argument with a default value of None. 

Functions expecting to receive data should have a `form_data` argument with a default value of None.  

----
<br>

There are four functions provided to create responses (return values from path handler functions)

--  
`build_html_response(data, response_code='200 OK')`  

`data (str)` : HTML excluding <head> (see below)

Returns (bytes) HTTP response of parsed template file. Use <% head %> ... <% /head %> to add to
HTML head. Data is automatically wrapped with <html> and given proper meta tags.

--  
`build_json_response(data, response_code='200 OK')`  

`data (str | dict)` : JSON encodable data  
`response_code (str)` : HTTP response code  

Return (bytes) HTTP response of JSON-encoded data.  

--  
`build_file_response(path, content_type=None)`  

File handling with automatic content type detection.

`path (str)` : Path to file relative to www-root folder next to your server script  
`content_type (str)` : Mimetype; if set to None mimetype will be automatically be determined  

Return (bytes) HTTP response containing file data. If content_type is set of determined  
to be text/html, the file will be parsed as a template. 404's if <path> is a directory.

--  
`build_http_response(data, content_type='text/html', response_code='200 OK')`

Base HTTP response maker.

`data (str | bytes)` : Data to be packed into an HTTP response  
`content_type (str)` : Mimetype of data  
`response_code (str)` : HTTP response code  

Returns (bytes) of the packaged HTTP response.

--  
There are also several basic responses for ease of use:  
`HTTP_200(msg='200 OK')`  
`HTTP_201(msg='201 Created')`  
`HTTP_204(msg='204 No Content')`  
`HTTP_400(msg='400 Bad Request')`  
`HTTP_403(msg='403 Forbidden')`  
`HTTP_404(msg='404 Not Found')`  
`HTTP_500(msg='500 Internal Server Error')`  
