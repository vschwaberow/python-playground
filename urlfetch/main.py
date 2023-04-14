# Description: This script reads a file containing URLs and fetches the content of each URL using multiple threads.
# SPDX-License-Identifier: MIT
# Author: Volker Schwaberow <volker@schwaberow.de>

import os
import sys
import requests
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import queue
from threading import Lock

total_urls_in_queue = 0
processed_urls = 0
failed_urls = 0
stats_lock = Lock()


def read_urls_from_file(file_path):
    global total_urls_in_queue
    url_queue = queue.Queue()
    with open(file_path, "r") as file:
        for line in file:
            url = line.strip()
            if url.startswith("http") or url.startswith("https"):
                url_queue.put(url)
                total_urls_in_queue += 1
            else:
                if url.startswith("www."):
                    url = url[4:]
                url_queue.put("http://" + url)
                url_queue.put("https://" + url)
                total_urls_in_queue += 2
    return url_queue

def print_help():
    print("Usage: python main.py [file with urls]")
    print("Example: python main.py ./urls.txt")

def get_url_content(url, executor):
    try:
        response = requests.get(url)
        response.raise_for_status()
        update_and_print_statistics(success=True)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching the URL: {e}")
        update_and_print_statistics(success=False)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        update_and_print_statistics(success=False)
        return None

def update_and_print_statistics(success):
    global processed_urls, failed_urls
    with stats_lock:
        clear_previous_lines(7)
        if success:
            processed_urls += 1
        else:
            failed_urls += 1
        print(f"Total URLs in queue: {total_urls_in_queue}")
        print(f"Processed URLs: {processed_urls}")
        print(f"Failed URLs: {failed_urls}")
        print("\n")

def clear_previous_lines(num_lines):
    try:
        for _ in range(num_lines):
            sys.stdout.write("\x1b[1A")
            sys.stdout.write("\x1b[2K")
    except Exception as e:
        print(f"Error while clearing previous lines: {e}")
        return None

def process_urls(url_queue):
    with ThreadPoolExecutor() as executor:
        future_results = [executor.submit(
            get_url_content, url_queue.get(), executor) for _ in range(url_queue.qsize())]

        for future in concurrent.futures.as_completed(future_results):
            try:
                content = future.result()
            except Exception as e:
                print(f"Failed to process {future.url}: {e}")

def main():
    if len(sys.argv) != 2:
        print_help()
    else:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            url_queue = read_urls_from_file(file_path)
            process_urls(url_queue)
        else:
            print("File does not exist")

if __name__ == "__main__":
    main()
