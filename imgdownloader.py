#!/data/data/com.termux/files/usr/bin/python
import argparse
import io
import os
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional imports for backends with graceful fallback handling
try:
    import requests
except ImportError:
    requests = None

try:
    import httpx
except ImportError:
    httpx = None

try:
    import pycurl
except ImportError:
    pycurl = None

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def validDir(userDir):
    """
    Argparse validator to ensure specified output directory exists or can be created.
    """
    if userDir and os.path.exists(userDir):
        return userDir
    elif not userDir:
        return userDir
    return userDir  # Will be created automatically via os.makedirs later


def validSize(size):
    """
    Argparse validator for custom image dimensions (e.g. '1920*1080').
    """
    valid = re.search(r"^[0-9]+\*[0-9]+$", size)
    if valid:
        dimensions = re.findall(r"[0-9]+", size)
        return dimensions
    raise argparse.ArgumentTypeError("Custom size must be in 'WIDTH*HEIGHT' format (e.g. 1920*1080).")


def getParams(sysArgs):
    """
    Configures and parses CLI options.
    """
    parser = argparse.ArgumentParser(description="Get arguments for searching and downloading Google images")

    # Required and general arguments
    parser.add_argument("-q", "--query", help="Query to search for", type=str, required=True, nargs="+")
    parser.add_argument("-l", "--limit", help="Max images to download (default: 3)", type=int, default=3)
    parser.add_argument("-o", "--outputDir", help="Full directory to store images in", type=validDir, required=False)
    parser.add_argument("-c", "--chromedriver", help="Full path to the chromedriver binary", type=str, required=False)

    # NEW FUNCTIONALITY: Download Backend Choice
    parser.add_argument(
        "-b",
        "--backend",
        help="HTTP backend library to use for downloading images (requests [default], pycurl, httpx)",
        type=str,
        choices=["requests", "pycurl", "httpx"],
        default="requests",
    )

    # NEW FUNCTIONALITY: Multi-threading support
    parser.add_argument(
        "-t",
        "--threads",
        help="Number of parallel download threads (default: 4)",
        type=int,
        default=4,
    )

    # Query refinement arguments
    parser.add_argument("-epq", "--exactQuery", help="Words that must be included", type=str, default="")
    parser.add_argument("-oq", "--optionalQuery", help="Words that are optional", type=str, default="")
    parser.add_argument("-eq", "--exceptQuery", help="Words that must not be included", type=str, default="")

    # Size selection
    sizeGroup = parser.add_mutually_exclusive_group(required=False)
    sizeGroup.add_argument("-cs", "--customSize", help="Find image of specific size (e.g., 1920*1080)", type=validSize)
    sizeGroup.add_argument(
        "-sz",
        "--size",
        help="Find images of pre-defined size category",
        type=str,
        choices=[
            "s",
            "m",
            "l",
            "i",
            ">2MP",
            ">4MP",
            ">6MP",
            ">8MP",
            ">10MP",
            ">12MP",
            ">15MP",
            ">20MP",
            ">40MP",
            ">70MP",
            ">400*300",
            ">640*480",
            ">800*600",
            ">1024*768",
        ],
    )

    # Aspect ratio & colors
    parser.add_argument(
        "-ar",
        "--aspectRatio",
        help="Find images of specific aspect ratio",
        type=str,
        choices=["s", "t", "w", "p"],
    )

    colourGroup = parser.add_mutually_exclusive_group(required=False)
    colourGroup.add_argument(
        "-co",
        "--colour",
        help="Find images containing specific colour",
        type=str,
        choices=[
            "red",
            "orange",
            "yellow",
            "green",
            "teal",
            "blue",
            "purple",
            "pink",
            "white",
            "gray",
            "black",
            "brown",
        ],
    )
    colourGroup.add_argument(
        "-ct",
        "--colourType",
        help="Find images of specific color type",
        type=str,
        choices=["full-colour", "black-and-white", "transparent"],
    )

    # File and image type filters
    parser.add_argument(
        "-it",
        "--imageType",
        help="Type of image",
        type=str,
        choices=["face", "photo", "clipart", "lineart", "animated"],
    )
    parser.add_argument(
        "-ft",
        "--fileType",
        help="Type of file extension",
        type=str,
        choices=["jpg", "gif", "png", "bmp", "svg", "webp", "ico", "raw"],
    )
    parser.add_argument("-s", "--site", help="Specific site or domain to search", type=str, default="")

    # SafeSearch flag (FIXED bug: action="store_true" instead of type=bool)
    parser.add_argument(
        "-ss",
        "--SafeSearch",
        help="Enable SafeSearch filter",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-ur",
        "--usageRights",
        help="Filter by usage rights",
        type=str,
        choices=["CC", "Commercial", "Other"],
    )

    args = parser.parse_args(sysArgs)
    params = vars(args)

    # Join list of query words into single string
    params["query"] = " ".join(params["query"]).strip()
    return params


def compileParams(params):
    """
    Compiles input options into formatted Google Search URL parameters.
    """
    imgQuery = params["query"]
    compiled = {}
    for key, value in params.items():
        compiled[key] = getParamValue(key, value, imgQuery)
    return compiled


def getParamValue(k, v, imgQuery):
    """
    Maps option keys to URL query strings.
    """
    if v:
        if k == "size":
            sizeSwitcher = {
                "s": "s",
                "m": "m",
                "l": "l",
                "i": "i",
                ">2MP": "2mp",
                ">4MP": "4mp",
                ">6MP": "6mp",
                ">8MP": "8mp",
                ">10MP": "10mp",
                ">12MP": "12mp",
                ">15MP": "15mp",
                ">20MP": "20mp",
                ">40MP": "40mp",
                ">70MP": "70mp",
                ">400*300": "qsvga",
                ">640*480": "vga",
                ">800*600": "svga",
                ">1024*768": "xvga",
            }
            return sizeSwitcher.get(v, "")
        elif k == "customSize":
            return f" imagesize:{v[0]}x{v[1]}"
        elif k == "aspectRatio":
            ratioSwitcher = {"s": "iar:s", "t": "iar:t", "w": "iar:w", "p": "iar:p"}
            return ratioSwitcher.get(v, "")
        elif k == "colourType":
            colourSwitcher = {"full-colour": "color", "black-and-white": "gray", "transparent": "trans"}
            return colourSwitcher.get(v, "")
        elif k == "SafeSearch":
            return "active" if v else "images"
        elif k == "usageRights":
            typeSwitcher = {"CC": "sur%3Acl", "Commercial": "sur%3Aol", "Other": "sur%3Aol"}
            return typeSwitcher.get(v, "")
        else:
            return v
    else:
        if k == "limit":
            return 3
        elif k == "outputDir":
            # Default directory created in current working directory based on query
            safe_folder = re.sub(r"[^\w\s-]", "_", imgQuery).strip()
            return os.path.join(os.getcwd(), safe_folder)
        elif k == "SafeSearch":
            return "images"
        else:
            return ""


def getSearchUrl(params):
    """
    Builds Google Images Search URL.
    """
    searchUrl = (
        f"https://www.google.com/search?as_st=y&tbm=isch"
        f"&as_q={urllib.parse.quote(params['query'] or '')}{params.get('customSize', '')}"
        f"&as_epq={urllib.parse.quote(params.get('exactQuery', ''))}"
        f"&as_oq={urllib.parse.quote(params.get('optionalQuery', ''))}"
        f"&as_eq={urllib.parse.quote(params.get('exceptQuery', ''))}"
        f"&imgsz={params.get('size', '')}"
        f"&imgc={params.get('colourType', '')}"
        f"&imgcolor={params.get('colour', '')}"
        f"&imgtype={params.get('imageType', '')}"
        f"&as_sitesearch={params.get('site', '')}"
        f"&safe={params.get('SafeSearch', 'images')}"
        f"&as_filetype={params.get('fileType', '')}"
        f"&tbs={params.get('aspectRatio', '')} {params.get('usageRights', '')}"
    )
    return searchUrl


def getImageUrls(params, url):
    """
    Launches headless Chrome using Selenium to extract image target URLs.
    """
    resultsIndex = 0
    imageUrls = []
    maxImages = params["limit"]

    # Modern headless Chrome configuration
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--headless=new")
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument("log-level=3")
    chromeOptions.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        if params.get("chromedriver"):
            service = Service(executable_path=params["chromedriver"])
            driver = webdriver.Chrome(service=service, options=chromeOptions)
        else:
            driver = webdriver.Chrome(options=chromeOptions)
    except Exception as e:
        print(f"Could not initialize Chrome driver: {e}")
        sys.exit(3)

    driver.set_window_size(1024, 768)
    driver.get(url)

    def scroll(drv):
        drv.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        while len(imageUrls) < maxImages:
            scroll(driver)

            # Updated modern Selenium By syntax
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
            resultsNo = len(thumbnails)

            if resultsIndex >= resultsNo:
                try:
                    loadButton = driver.find_element(By.CSS_SELECTOR, ".mye4qd")
                    if loadButton.is_displayed():
                        driver.execute_script("arguments[0].click();", loadButton)
                except Exception:
                    print("No more images found on Google.")
                    break

            for thumbnail in thumbnails[resultsIndex:resultsNo]:
                try:
                    thumbnail.click()
                    images = driver.find_elements(By.CSS_SELECTOR, "img.n3VNCb, img.iR330, img.r48fl")
                    for image in images:
                        imgSource = image.get_attribute("src")
                        if imgSource and imgSource.startswith("http") and imgSource not in imageUrls:
                            imageUrls.append(imgSource)
                            print(f"Collected URL ({len(imageUrls)}/{maxImages}): {imgSource[:60]}...")
                            if len(imageUrls) >= maxImages:
                                break
                    if len(imageUrls) >= maxImages:
                        break
                except Exception:
                    continue

            resultsIndex = resultsNo

    finally:
        driver.quit()

    print(f"Done getting URLs. Total retrieved: {len(imageUrls)}")
    return imageUrls


# ===========================================================================
# BACKEND DOWNLOAD IMPLEMENTATIONS (requests, httpx, pycurl)
# ===========================================================================


def download_with_requests(url, timeout=10, headers=None):
    """Download implementation using the 'requests' package."""
    if requests is None:
        raise ImportError("The 'requests' library is not installed (`pip install requests`).")
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    return resp.content, content_type


def download_with_httpx(url, timeout=10, headers=None):
    """Download implementation using the 'httpx' package."""
    if httpx is None:
        raise ImportError("The 'httpx' library is not installed (`pip install httpx`).")
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        return resp.content, content_type


def download_with_pycurl(url, timeout=10, headers=None):
    """Download implementation using the 'pycurl' libcurl bindings."""
    if pycurl is None:
        raise ImportError("The 'pycurl' library is not installed (`pip install pycurl`).")

    buffer = io.BytesIO()
    header_buffer = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.HEADERFUNCTION, header_buffer.write)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.TIMEOUT, timeout)

    user_agent = headers.get("User-Agent", "Mozilla/5.0") if headers else "Mozilla/5.0"
    c.setopt(c.USERAGENT, user_agent)

    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()

    if status_code != 200:
        raise Exception(f"HTTP Status Code {status_code}")

    # Extract Content-Type header from response
    header_text = header_buffer.getvalue().decode("iso-8859-1", errors="ignore")
    content_type = ""
    for line in header_text.splitlines():
        if line.lower().startswith("content-type:"):
            content_type = line.split(":", 1)[1].strip()

    return buffer.getvalue(), content_type


def get_extension_from_content_type(content_type, default=".jpg"):
    """
    Helper to detect file extension from response Content-Type header.
    """
    if "image/png" in content_type:
        return ".png"
    elif "image/gif" in content_type:
        return ".gif"
    elif "image/webp" in content_type:
        return ".webp"
    elif "image/bmp" in content_type:
        return ".bmp"
    elif "image/svg+xml" in content_type:
        return ".svg"
    elif "image/x-icon" in content_type or "image/vnd.microsoft.icon" in content_type:
        return ".ico"
    elif "image/jpeg" in content_type:
        return ".jpg"
    return default


def single_download_worker(index, url, backend, output_dir, headers):
    """
    Thread pool worker function to execute downloading an image.
    """
    backend = backend.lower()
    try:
        if backend == "requests":
            file_content, content_type = download_with_requests(url, headers=headers)
        elif backend == "httpx":
            file_content, content_type = download_with_httpx(url, headers=headers)
        elif backend == "pycurl":
            file_content, content_type = download_with_pycurl(url, headers=headers)
        else:
            raise ValueError(f"Unknown backend requested: {backend}")

        ext = get_extension_from_content_type(content_type)
        filename = f"image_{index:03d}{ext}"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(file_content)

        print(f"[+] [{backend.upper()}] Downloaded: {filename}")
        return True

    except Exception as err:
        print(f"[-] [{backend.upper()}] Failed image {index} ({url[:40]}...): {err}")
        return False


def downloadImages(params, imageUrls):
    """
    Coordinates downloading images into outputDir using selected backend & multi-threading.
    """
    backend = params.get("backend", "requests")
    picDir = params["outputDir"]
    thread_count = params.get("threads", 4)

    os.makedirs(picDir, exist_ok=True)
    print(f"\nDownloading {len(imageUrls)} images using backend '{backend}' into '{picDir}'...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Execute parallel download jobs using ThreadPoolExecutor
    success_count = 0
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [
            executor.submit(single_download_worker, idx + 1, url, backend, picDir, headers)
            for idx, url in enumerate(imageUrls)
        ]

        for future in as_completed(futures):
            if future.result():
                success_count += 1

    print(f"\nFinished: {success_count}/{len(imageUrls)} images successfully saved.")


def main(args):
    """
    Main script workflow.
    """
    params = getParams(args)
    params = compileParams(params)
    url = getSearchUrl(params)
    imageUrls = getImageUrls(params, url)

    if imageUrls:
        downloadImages(params, imageUrls)
    else:
        print("No image URLs found to download.")


if __name__ == "__main__":
    main(sys.argv[1:])
