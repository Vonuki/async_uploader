import json
import os

import pytest
from aiohttp import web, FormData

from app.UploadApp import UploadApp

TEST_FILE_BODY = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
TEST_FILE_CONTENT_TYPE = 'plain/text'
TEST_FILE_NAME = 'example.txt'


async def test_echo(aiohttp_server, aiohttp_client):
    app = UploadApp()
    server = await aiohttp_server(app)
    client = await aiohttp_client(server)
    response = await client.get('/echo/John')
    assert response.status == 200
    body = await response.text()
    assert "John" in body


# fixture to creat client
@pytest.fixture
def uploader_client(loop, aiohttp_client):
    app = UploadApp()
    return loop.run_until_complete(aiohttp_client(app))


async def test_get_form(uploader_client):
    """
    Test get request respond with form
    """
    resp = await uploader_client.get('/')
    body = await resp.text()
    assert "action='upload'" in body


async def test_upload(uploader_client):
    """
    Test to upload file
    """
    # upload file
    data = FormData()
    data.add_field(
        'file',
        TEST_FILE_BODY,
        filename = TEST_FILE_NAME,
        content_type = TEST_FILE_CONTENT_TYPE
    )
    response = await uploader_client.post('/upload', data = data)
    assert response.status == 200

    # handle response
    response_json_bytes = await response.read()
    json_obj = json.loads(response_json_bytes.decode())
    file_link = json_obj.get("file_path")
    assert file_link

    # download file and compare
    file_response = await uploader_client.get(file_link)
    assert file_response.status == 200, 'After upload download failed'
    file_body = await file_response.content.read()
    assert file_body == TEST_FILE_BODY


async def test_error(uploader_client):
    """
    Test get request respond with form
    """
    data = FormData()
    data.add_field(
        'other_file',
        TEST_FILE_BODY,
        filename = TEST_FILE_NAME,
        content_type = TEST_FILE_CONTENT_TYPE
    )
    response = await uploader_client.post('/upload', data = data)
    assert response.status == 404


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup once we are finished."""
    request.addfinalizer(files_clear)


def files_clear():
    """ function removes uploaded test files """
    path = './store'
    files = os.listdir(path)
    for file_name in files:
        if "gitignore" not in file_name:
            os.remove(path + "/" + file_name)
