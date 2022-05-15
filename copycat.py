"""Module for cloning a website given a list of URLs"""
import requests
from urllib.parse import urlparse
import os


def prep_path(path, docroot):
    """Builds the local directory path string and full file path string"""

    path = docroot + path
    if path.endswith("/"):
        path += "index.html"

    tree = path.split("/")
    tree_dirs = tree[:-1]
    tree_file = tree[-1]

    dot_parts = tree_file.split(".")
    if len(dot_parts) == 1:
        tree_dirs.append(tree_file)
        tree_file = "index.html"

    dir_path = "/".join(tree_dirs)
    full_path = f"{dir_path}/{tree_file}"

    return dir_path, full_path


def save_page(response, docroot):
    """Saves the page to the local file system"""

    url = response.url
    data = response.content
    code = response.status_code

    path = urlparse(url).path
    dir_path, full_path = prep_path(path, docroot)

    os.makedirs(dir_path, exist_ok=True)
    with open(full_path, "wb") as file:
        file.write(response.content)

    return "+", code, full_path


def redirect(response):
    """Builds response payload for any kind of redirection"""

    url = response.url
    code = response.status_code
    location = response.headers.get("Location")

    source = urlparse(url).path
    target = urlparse(location).path

    message = f"{source} -> {target}"
    return "*", code, message


def scrape(url, docroot):
    """Scrapes the remote URL and handles response"""

    payload = None

    try:
        response = requests.get(url, allow_redirects=False, timeout=10)
    except requests.exceptions.ReadTimeout:
        payload = "!", "N/A", url
    else:
        code = response.status_code
        if code == 200:
            payload = save_page(response, docroot)
        elif code in (301, 302):
            payload = redirect(response)
        else:
            payload = "-", code, url

    return payload


def copycat(args):
    """Loads URLs and performs the website cloning process"""

    with open(args.urls) as file:
        urls = set(file.read().strip().split("\n"))

    docroot = args.docroot.rstrip("/")

    with open(args.outfile, "w") as file:
        for url in urls:
            status, code, message = scrape(url, docroot)
            result = f"[{status}] ({code}) {message}"
            file.write(result + "\n")
            print(result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "urls",
        help="specify a file name containing a list of URLs"
    )
    parser.add_argument(
        "-o", "--outfile",
        required=False,
        default="copycat.out",
        help="specify output file name to store results"
    )
    parser.add_argument(
        "-d", "--docroot",
        required=False,
        default="www",
        help="specify directory name for the cloned files to be stored in"
    )
    args = parser.parse_args()
    copycat(args)
