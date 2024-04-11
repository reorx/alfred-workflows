#!/usr/bin/env python3

import sys
import os
import re
import json
import urllib.request
from urllib.error import HTTPError, URLError

# Get environment variables for GitHub API token and user
GITHUB_API_TOKEN = os.environ.get('GITHUB_API_TOKEN')
GITHUB_USER = os.environ.get('GITHUB_USER')

# Ensure we have the necessary environment variables
if not GITHUB_API_TOKEN or not GITHUB_USER:
    output = {
        'items': [{
            'uid': 'error',
            'title': 'Error',
            'subtitle': 'Please set GITHUB_API_TOKEN and GITHUB_USER in the workflow configuration',
        }]
    }
    print(json.dumps(output))
    sys.exit()


def debug(msg):
    print(msg, file=sys.stderr, flush=True)


# Function to parse the link header
def parse_link_header(link_header):
    """
    https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28

    sample:
    <https://api.github.com/repositories/1300192/issues?page=2>; rel="prev", <https://api.github.com/repositories/1300192/issues?page=4>; rel="next", <https://api.github.com/repositories/1300192/issues?page=515>; rel="last", <https://api.github.com/repositories/1300192/issues?page=1>; rel="first"
    """
    # Regular expression to find URLs and their corresponding rel values
    link_pattern = re.compile(r'<(.+?)>; rel="(.+?)"')
    # Find all matches in the header
    links = link_pattern.findall(link_header)
    # Convert the tuples into a dictionary
    link_dict = {rel: url for url, rel in links}
    return link_dict


def get_url(page=1):
    # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repositories-for-a-user
    return f"https://api.github.com/users/{GITHUB_USER}/repos?sort=pushed&per_page=100&page={page}"


def get_cache(key):
    # https://www.alfredapp.com/help/workflows/script-environment-variables/
    cache_dir = os.environ.get('alfred_workflow_cache', '/tmp')
    cache_path = f'{cache_dir}/{key}'

    if not os.path.exists(cache_path):
        return None
    debug(f'cache hit: {key}')

    with open(f'{cache_dir}/{key}', 'r') as f:
        return json.loads(f.read())


def set_cache(key, value):
    cache_dir = os.environ.get('alfred_workflow_cache', '/tmp')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    with open(f'{cache_dir}/{key}', 'w') as f:
        f.write(json.dumps(value))


def get_repos(url, key, no_cache=False):
    if not no_cache:
        cached = get_cache(key)
        if cached is not None:
            return cached['repos'], cached['links']

    # Prepare the request headers with the token for authentication
    headers = {
        'Authorization': f'Bearer {GITHUB_API_TOKEN}',
        'User-Agent': 'Python urllib request'
    }

    # Create a request object with the URL and headers
    request = urllib.request.Request(url, headers=headers)

    try:
        # Perform the request
        with urllib.request.urlopen(request) as response:
            # Check if the response status code is 200 (OK)
            if response.status != 200:
                raise Exception(f"GitHub API responded with status code: {response.status}")

            # get 'link' from response headers
            link_header = response.getheader('Link') or response.getheader('link')
            links = parse_link_header(link_header)

            # Read the response body and decode it to string
            response_body = response.read().decode('utf-8')
            # Parse the response body as JSON
            repos_data = json.loads(response_body)

            # set cache
            set_cache(key, {'repos': repos_data, 'links': links})
            return repos_data, links


    except HTTPError as e:
        # Handle HTTP errors
        raise Exception(f"HTTPError: {e.code} - {e.reason}")
    except URLError as e:
        # Handle URL errors
        raise Exception(f"URLError: {e.reason}")
    except Exception as e:
        # Handle any other exceptions
        raise


def main():
    # Process the response data into the specified format
    items = []

    url = get_url()
    page = 1

    while True:
        key = f'{GITHUB_USER}-{page}.json'
        repos, links = get_repos(url, key, no_cache=page == 1)
        next_url = links.get("next")
        debug(f'repos count: {len(repos)}, next url: {next_url}')

        for repo in repos:
            items.append({
                "uid": repo["full_name"],
                "title": repo["name"],
                "subtitle": repo["description"],
                "arg": f'https://github.dev/{repo["full_name"]}',
            })

        if next_url is None or next_url == url:
            break
        # update url to next page
        url = next_url
        page += 1

    # Create the final structure
    data = {
        "items": items
    }

    # Print the data as JSON
    print(json.dumps(data))

main()
