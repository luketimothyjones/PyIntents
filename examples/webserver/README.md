Multithreaded webserver that supports GET, POST, and PUT. Includes parsing for URL parameters and form data. No external dependencies (aside from pyretree). This is just a fun example project; while I have tried to make it safe there are likely exploitable flaws. Should not be used in production.

Use `<% head %> ... <% /head %>` to add to HTML head in a template file (see [home.html](https://github.com/luketimothyjones/pyretree/tree/main/examples/webserver/www-root/templates/home.html)) or call to `build_html_response()`.

See [example_server.py](https://github.com/luketimothyjones/pyretree/tree/main/examples/webserver/example_server.py) for an example implementation.

Paths are in the format `HTTP_VERB:<path>`. For example, `GET:/my-page`, `PUT:/my-page`, `POST:/my-page`.

Functions expecting to receive URL parameters should have a `url_params` argument with a default value of None.
Functions expecting to receive data should have a `form_data` argument with a default value of None.
