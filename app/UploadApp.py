"""
Class of server application
"""
import datetime
import json
import logging
import os

from aiohttp import web, streamer
from aiohttp.web_app import Application

logger = logging.getLogger('app-log')

@streamer
async def file_sender(writer, file_path=None):
    """
    Read file chunk by chunk and send it through HTTP
    """
    with open(file_path, 'rb') as f:
        chunk = f.read(2 ** 16)
        while chunk:
            await writer.write(chunk)
            chunk = f.read(2 ** 16)


async def download_file(request) -> web.Response:
    """
    Get download of file
    Args:
        request: Request object
    Returns:
        web.Response object
    """
    try:
        file_name = request.match_info['file_name']
        headers = {
            "Content-disposition": "attachment; filename={file_name}".format(file_name = file_name)
        }
        file_path = os.path.join('store', file_name)

        logger.debug("filepath = %s", file_path)

        if not os.path.exists(file_path):
            return web.Response(
                body = 'File <{file_name}> does not exist'.format(file_name = file_name),
                status = 404
            )

        return web.Response(
            body = file_sender(file_path = file_path),
            headers = headers
        )
    except Exception as e:
        return web.Response(
            body = "File download exception {}".format(e),
            status = 404
        )


async def uploader(request) -> web.Response:
    """
    POST uploader of multipart from data
    Args:
        request: Request object
    Returns:
        web.Response
        body:  {
            "file_path": relative path to file,
            "full_link": full link to file,
            "size": size of file
        }
    """
    try:
        logger.debug("Get POST request for upload")
        if request.content_type == "multipart/form-data":
            reader = await request.multipart()
            while True:
                field = await reader.next()
                if field is None:
                    break
                if field.name == 'file':
                    filename = field.filename
                    size = 0
                    root_dir = os.path.abspath(os.curdir)
                    filename = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S_") + filename
                    with open(os.path.join(root_dir, "store", filename), 'wb') as f:
                        while True:
                            chunk = await field.read_chunk()  # 8192 bytes by default.
                            if not chunk:
                                break
                            size += len(chunk)
                            f.write(chunk)
                    link = "/store/{}".format(filename)
                    data = {
                        "file_path": link,
                        "full_link": request.scheme + "://" + request.host+link,
                        "size": size
                    }
                    data = json.dumps(data, indent = 4, ensure_ascii=False).encode('utf-8')
                    return web.Response(body = data,
                                        content_type="text/html",
                                        charset = "utf-8")
            # not correct form-data
            return web.Response(
                body = "field <file> not presented in form-data",
                status = 404
            )
        else:
            return web.Response(
                body = "Request doesn't has multipart/form-data {}".format(request.keys()),
                status = 404
            )

    except Exception as e:
        return web.Response(
            body = "POST Uploader exception {}".format(e),
            status = 404
        )


async def get_form(request) -> web.Response:
    """
    Get form to upload from browser
    Args:
        request: Request object
    Returns:
        web.Response object
    """
    html = "<head> <meta charset='utf-8'> </head>" \
           "<body>" \
           "<form action='upload' method='post' accept-charset='utf-8' enctype='multipart/form-data'>" \
           "<label for='file'>File</label>" \
           "<input id='file' name='file' type='file' value=''/>" \
           "<input type='submit' value='upload'/>" \
           "</form>" \
           "</body></html>"
    return web.Response(body = html, content_type="text/html")


async def echo_request(request) -> web.Response:
    """
    echo endpoint for testing
    Args:
        request: Request object
    Returns:
        web.Response object
    """
    name = request.match_info.get("name", 'Anonymous')
    text = "Hello {}".format(name)
    print('Request handled respond: {}'.format(text))
    return web.Response(text = text)


class UploadApp (Application):
    """Web Application Class"""
    def __init__(self, *args, **kwargs):
        super(UploadApp, self).__init__(*args, **kwargs)

        self.add_routes([web.get('/echo/{name}', echo_request)])  # test echo endpoint
        self.add_routes([web.get('/', get_form)])  # GET endpoint for HTML Form
        self.add_routes([web.post('/upload', uploader)])  # POST endpoint to upload
        self.add_routes([web.get('/store/{file_name}', download_file)])  # GET download endpoint
