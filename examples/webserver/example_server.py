import pathlib
import sys

from webserver import ThreadedWebServer, build_http_response, build_file_response, build_html_response, build_json_response

try:
    from pyretree import pyretree
except ImportError:
    # Gross way to import from the repository structure
    sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent.absolute()))
    from pyretree import pyretree


# --------
# Define various paths to be used for file handling
ROOT = pathlib.Path(__file__).parent.absolute() / 'www-root'
MEDIA_ROOT = ROOT / 'media'
TEMPLATE_ROOT = ROOT / 'templates'

path_handler = pyretree.RegexCollection(separator='/')

# --------
@path_handler.add('GET:/')
def root():
    return build_file_response(TEMPLATE_ROOT / 'home.html')

# ----
@path_handler.add('GET:/hello_world')
def hello_world():
    return build_html_response(
    """
    <% head %><title>Hello World</title><% /head %>
    <body><p>Hello world!</p></body>
    """
    )

# ----
@path_handler.add('GET:/coffee')
def teapot():
    # Respect HTCPCP
    return build_html_response("<body><h1>418 I'm a teapot</h1></body>", response_code="418 I'm a teapot")

# ----
@path_handler.add('GET:/favicon.ico')
def favicon():
    return build_file_response(MEDIA_ROOT / 'favicon.png')

# ----
@path_handler.add('GET:/<filepath>')
def files(filepath):
    return build_file_response(ROOT / filepath)

# ----
@path_handler.add('GET:/api/hello')
def json_get_endpoint():
    return build_json_response({'hello': 'world'})

# ----
@path_handler.add('GET:/api/echo')
def json_get_echo_endpoint(url_params=None):
    url_params = {} if url_params is None else url_params
    msg = url_params.get('msg', '')
    opt = url_params.get('opt', '')

    if msg == '':
        return build_json_response({'error': "expected parameter 'msg'"}, '400 Bad Request')

    return build_json_response({'message': msg, 'opt': opt})

# --
@path_handler.add('POST:/api/echo')
def json_post_echo_endpoint(form_data=None):
    return build_json_response({'received_data': form_data})

# --
@path_handler.add('PUT:/api/echo')
def json_put_echo_endpoint(form_data=None):
    return build_json_response({'received_data': form_data})

# ----
path_handler.prepare()


# --------
if __name__ == '__main__':
    server = ThreadedWebServer(path_handler, 'localhost', 5000)
    server.run_forever()
