import json
import mimetypes
import re
import socket
import socketserver
import threading
import time
import urllib.parse

from http.server import BaseHTTPRequestHandler
from io import BytesIO


# --------
def build_http_response(data, content_type='text/html', response_code='200 OK'):
    """
    Base HTTP response maker.
    ----
    data (str | bytes) : Data to be packed into an HTTP response
    content_type (str) : Mimetype of data
    response_code (str) : HTTP response code
    ----
    Returns (bytes) of the packaged HTTP response.
    """

    http_header = f'HTTP/1.1 {response_code}\r\nContent-Type: {content_type}\r\nContent-Length: {len(data)}\r\n\r\n'

    if content_type.startswith('text') and type(data) != bytes:
        return bytes(http_header + data, 'utf-8')
    else:
        return bytes(http_header, 'utf-8') + data

# ----
EXTRACT_HTML_HEAD_RE = re.compile('<% head %>(.+)<% /head %>', re.MULTILINE | re.DOTALL)
def build_html_response(data, response_code='200 OK'):
    """
    data (str) : HTML excluding <head> (see above)
    ----
    Returns (bytes) HTTP response of parsed template file. Use <% head %> ... <% /head %> to add to
    HTML head. Data is automatically wrapped with <html> and given proper meta tags.
    """

    extracted_head = EXTRACT_HTML_HEAD_RE.search(data)

    head = ''
    if extracted_head is not None:
        data = data.replace(extracted_head.group(0), '')
        head = extracted_head.group(1)

    meta_content = '<meta content="text/html;charset=utf-8" http-equiv="Content-Type"><meta content="utf-8" http-equiv="encoding">'

    return build_http_response(f'<html><head>{meta_content}{head}</head>{data}</html>', response_code=response_code)

# ----
def _recursive_json_load(data):
    # Move through dict recursively and load as much of the JSON as we can
    for key, val in data.items():
        if type(val) == str:
            try:
                data[key] = json.loads(data[key])
            except json.decoder.JSONDecodeError:
                pass

        else:
            _recursive_json_load(data[key])

def build_json_response(data, response_code='200 OK'):
    """
    data (str | dict) : JSON encodable data
    response_code (str) : HTTP response code
    ----
    Return (bytes) HTTP response of JSON-encoded data.
    """

    if type(data) == str:
        data = json.loads(data)

    elif type(data) == dict:
        _recursive_json_load(data)

    encoded_json = json.dumps(data)
    return bytes(f'HTTP/1.1 {response_code}\r\nContent-Type: application/json\r\nContent-Length: {len(encoded_json)}\r\n\r\n{encoded_json}', 'utf-8')

# ----
def build_file_response(path, content_type=None):
    """
    path (str) : Path to file relative to www-root folder next to your server script
    content_type (str) : Mimetype; if set to None mimetype will be automatically be determined
    ----
    Return (bytes) HTTP response containing file data. If content_type is set of determined
    to be text/html, the file will be parsed as a template. 404's if <path> is a directory.
    """

    try:
        path = urllib.parse.unquote(str(path)).replace('..', '')

        content_type = content_type if content_type is not None else mimetypes.guess_type(path)[0]
        if content_type is None:
            # 404 on directories
            return HTTP_404()

        mode = 'r' if content_type.startswith('text') else 'rb'
        with open(path, mode) as file:
            data = file.read()

        if content_type == 'text/html':
            return build_html_response(data)

        return build_http_response(data, content_type=content_type)

    except FileNotFoundError:
        return HTTP_404()

    except (OSError, PermissionError):
        return HTTP_403()

    except Exception as ex:
        print(f'Exception: {str(ex)}')
        return HTTP_500()

# --------
# HTTP errors for ease of use
def HTTP_400(msg='400 Bad Request'): return build_http_response(msg, response_code='400 Bad Request')
def HTTP_403(msg='403 Forbidden'): return build_http_response(msg, response_code='403 Forbidden')
def HTTP_404(msg='404 Not Found'): return build_http_response(msg, response_code='404 Not Found')
def HTTP_500(msg='500 Internal Server Error'): return build_http_response(msg, response_code='500 Internal Server Error')

# --------
class _HTTPRequest(BaseHTTPRequestHandler):
    # https://stackoverflow.com/questions/4685217/parse-raw-http-headers

    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.path = None
        self.parse_request()

# --------
# multipart/form-data data parsing
_MULTIPART_BOUNDARY_RE = re.compile('Content-Type: multipart/form-data; ?boundary=(.+)\\r\\n')
_MULTIPART_DATA_RE = re.compile('Content-Disposition: form-data; name="(.+)"\\r\\n\\r\\n(.+)\\r\\n--')

class _ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    path_handler = None  # Prepared instance of pyretree.RegexCollection(separator='/')

    def handle(self):
        data_bytes = self.request.recv(1024)

        if len(data_bytes) == 0:
            # Ignore empty requests
            return

        http_request = _HTTPRequest(data_bytes)
        extra_params = {}

        # Handle form data
        if http_request.command in ['POST', 'PUT']:
            data_str = str(data_bytes, encoding='utf-8')
            separator = '\r\n\r\n' if '\r\n\r\n' in data_str else '\n\n'
            request_parts = data_str.split(separator)
            form_data = separator.join(request_parts[1:]) if len(request_parts) > 1 else ''

            # multipart/form-data
            multipart_boundary = _MULTIPART_BOUNDARY_RE.search(request_parts[0])
            if multipart_boundary is not None:
                # Data separated by a specific boundary
                multipart_boundary = multipart_boundary.group(1)
                multiparts = form_data.split(multipart_boundary)

                multipart_data = {}
                for part in multiparts:
                    _result = _MULTIPART_DATA_RE.search(part)

                    if _result is not None:
                        key, val = _result.groups()
                        multipart_data[key] = val

                extra_params['form_data'] = multipart_data

            # x-www-form-urlencoded
            elif 'Content-Type: application/x-www-form-urlencoded' in request_parts[0]:
                form_pairs = form_data.split('&')
                x_www_data = {}

                # Data in format key=val&key2=val2
                for pair in form_pairs:
                    try:
                        split_pairs = pair.split('=')
                        key = split_pairs[0]
                        val = '='.join(split_pairs[1:])

                        x_www_data[key] = val

                    except IndexError:
                        # Ignore malformed form data
                        pass

                extra_params['form_data'] = x_www_data

            # raw/binary/graphql
            else:
                extra_params['form_data'] = form_data

        # Handle basic URL parameters
        if len(http_request.path.split('?')) > 1:
            url_params = {}
            params = '?'.join(http_request.path.split('?')[1:]).split('&')
            for param in params:
                parts = param.split('=')
                url_params[parts[0]] = '='.join(parts[1:])

            http_request.path = http_request.path.split('?')[0]
            extra_params['url_params'] = url_params

        while True:
            success = error_handled = False

            try:
                success, response = self.path_handler.match(f'{http_request.command}:{http_request.path}', extra_params=extra_params)
                break

            except TypeError as ex:
                # Handle unexcepted parameters / post data by ignoring them
                ex_str = str(ex)

                if ex_str.endswith("unexpected keyword argument 'url_params'"):
                    extra_params.pop('url_params')

                elif ex_str.endswith("unexpected keyword argument 'form_data'"):
                    extra_params.pop('form_data')

                else:
                    error_handled = True
                    response = HTTP_400()
                    break

            except Exception as ex:
                print(f'Exception: {str(ex)}')
                error_handled = True
                response = HTTP_500()
                break

        if not success and not error_handled:
           response = HTTP_404()

        self.request.sendall(response)


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


# ----
class ThreadedWebServer:

    def __init__(self, path_handler, host='localhost', port=5000):
        """
        Multithreaded webserver for demonstrative purposes. No safety guarantees whatsoever.
        ----
        path_handler (pyretree.RegexCollection(separator='/')) : See example_server.py
        host (str) : Host for the server
        port (int) : Port for the server
        """

        self.path_handler = path_handler
        self.host = host
        self.port = port

    # ----
    def run_forever(self):
        """
        Run the server until CTRL+C is pressed or the process exits.
        """

        request_handler = _ThreadedTCPRequestHandler
        request_handler.path_handler = self.path_handler

        with _ThreadedTCPServer((self.host, self.port), request_handler) as server:
            # Start a thread with the server. Will spawn threads for each request thereafter.
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)

            server_thread.start()
            print(f'Server is up at {self.host}:{self.port}. CTRL + C to close the server.')

            try:
                while True:
                    time.sleep(.5)
            except KeyboardInterrupt:
                print('Server shutting down...')
                pass

            server.shutdown()
