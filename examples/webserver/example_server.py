import pathlib

from webserver import ThreadedWebServer, build_http_response, build_file_response, build_html_response, build_json_response


# --------
# Define various paths to be used for file handling
ROOT = pathlib.Path(__file__).parent.absolute() / 'www-root'
MEDIA_ROOT = ROOT / 'media'
TEMPLATE_ROOT = ROOT / 'templates'

server = ThreadedWebServer('localhost', 5000)

# --------
@server.add_path('GET:/')
def root():
    return build_file_response(TEMPLATE_ROOT / 'home.html')

# ----
@server.add_path('GET:/hello_world')
def hello_world():
    return build_html_response(
    """
    <% head %><title>Hello World</title><% /head %>
    <body><p>Hello world!</p></body>
    """
    )

# ----
@server.add_path('GET:/coffee')
def teapot():
    # Respect HTCPCP
    return build_html_response("<body><h1>418 I'm a teapot</h1></body>", response_code="418 I'm a teapot")

# ----
@server.add_path('GET:/favicon.ico')
def favicon():
    return build_file_response(MEDIA_ROOT / 'favicon.png')

# ----
@server.add_path('GET:/<filepath>')
def files(filepath):
    return build_file_response(ROOT / filepath)

# ----
@server.add_path('GET:/api/hello')
def json_get_endpoint():
    return build_json_response({'hello': 'world'})

# ----
@server.add_path('GET:/api/echo')
def json_get_echo_endpoint(url_params=None):
    url_params = {} if url_params is None else url_params
    msg = url_params.get('msg', '')
    opt = url_params.get('opt', '')

    if msg == '':
        return build_json_response({'error': "expected parameter 'msg'"}, '400 Bad Request')

    return build_json_response({'message': msg, 'opt': opt})

# --
@server.add_path('POST:/api/echo')
def json_post_echo_endpoint(form_data=None):
    return build_json_response({'received_data': form_data})

# --
@server.add_path('PUT:/api/echo')
def json_put_echo_endpoint(form_data=None):
    return build_json_response({'received_data': form_data})


# --------
if __name__ == '__main__':
    server.run_forever()
