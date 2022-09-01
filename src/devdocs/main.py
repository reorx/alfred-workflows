
import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
from urllib_util import http_request
from urllib.error import HTTPError

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
}

doc_name_map = {
    'web': 'dom',
}

doc = os.environ['doc'].strip()
if doc in doc_name_map:
    doc = doc_name_map[doc]
doc_id = doc

doc_version = os.environ.get(f'{doc}_version')
if doc_version:
    doc_id = f'{doc}~{doc_version}'

def get_filter_json():
    url = f'https://devdocs.io/docs/{doc_id}/index.json'
    try:
        _, body = http_request('GET', url, headers=default_headers)
    except HTTPError as e:
        raise Exception(f'{url} -> {e}: {e.read().decode()}')
    data = json.loads(body)

    # https://www.alfredapp.com/help/workflows/inputs/script-filter/json/
    @dataclass
    class Item:
        uid: str
        type: str
        title: str
        subtitle: str
        arg: str
        autocomplete: str

    # {"entries":[{"name":"abc","path":"library/abc","type":"Runtime"}]}
    items = []
    for i in data['entries']:
        name = i['name']
        path = i['path']
        typ = i['type']
        items.append(Item(path, 'default', name, typ, name, name).__dict__)

    return json.dumps({'items': items})


def is_file_outdated(path_str, fresh_seconds) -> bool:
    modifed_before_seconds = int(time.time()) - Path(path_str).stat().st_mtime
    if modifed_before_seconds > fresh_seconds:
        return True
    return False


def get_workflow_data(key, func, max_age=60 * 60 * 24 * 7):
    # https://www.alfredapp.com/help/workflows/script-environment-variables/
    data_dir = Path(os.environ['alfred_workflow_data'])
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
    data_path = data_dir.joinpath(f'{key}.data')
    if data_path.exists() and not is_file_outdated(data_path, max_age):
        with open(data_path, 'r') as f:
            return f.read()
    data = func()
    with open(data_path, 'w') as f:
        f.write(data)
    return data


print(get_workflow_data(doc, get_filter_json))
