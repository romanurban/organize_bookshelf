import requests
from bs4 import BeautifulSoup
import time
import json
import re


def extract_book_details(book_url):
    print(f"Extracting details from: {book_url}")
    response = requests.get(book_url)
    if response.status_code != 200:
        print(
            f"Failed to fetch details from {book_url}, status code: {response.status_code}"
        )
        return None
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the title and author from the breadcrumb
    title = None
    author = None
    breadcrumb_container = soup.find("div", class_=re.compile(r"BreadCrumbs_container"))
    if breadcrumb_container:
        breadcrumb_list = breadcrumb_container.find(
            "ul", class_=re.compile(r"BreadCrumbs_list")
        )
        if breadcrumb_list:
            breadcrumb_items = breadcrumb_list.find_all("li")
            if len(breadcrumb_items) >= 2:
                author = breadcrumb_items[1].get_text(strip=True)
            if len(breadcrumb_items) >= 1:
                title = breadcrumb_items[-1].get_text(strip=True)

    print(f"Extracted Title: {title}, Author: {author}")

    if not title:
        print("No title found, skipping this book.")
        return None

    if not author:
        author = "Unknown"

    book_info = {"Title": title, "Author": author, "URL": book_url}

    # Extract additional book information from the "Details" section
    details_parent = soup.find("details", class_=re.compile(r"Accordion_details"))
    if details_parent:
        ul_element = details_parent.find("ul", {"role": "list"})
        if ul_element:
            for child in ul_element.children:
                if isinstance(child, str):
                    continue
                if child.name == "li":
                    text_content = child.get_text(separator=" ", strip=True)
                    if ":" in text_content:
                        label, value = text_content.split(":", 1)
                        book_info[label.strip()] = value.strip()
                elif child.name == "a":
                    previous_sibling = (
                        child.previous_sibling.strip() if child.previous_sibling else ""
                    )
                    if previous_sibling and previous_sibling.endswith(":"):
                        label = previous_sibling[:-1].strip()
                        value = child.get_text(strip=True)
                        book_info[label] = value

    return book_info


def extract_books_from_list(page_url):
    print(f"Fetching books from page: {page_url}")
    books = []
    response = requests.get(page_url)
    if response.status_code != 200:
        print(f"Failed to fetch page {page_url}, status code: {response.status_code}")
        return books

    with open("page_source.html", "w", encoding="utf-8") as file:
        file.write(response.text)

    soup = BeautifulSoup(response.content, "html.parser")

    book_links = soup.find_all("a", class_=re.compile(r"BookCard_link"))
    base_url = "https://www.penguin.co.uk"

    if not book_links:
        print(f"No books found on page: {page_url}")

    for link in book_links:
        book_url = base_url + link["href"]

        title = link.find("span", class_=re.compile(r"BookCard_title"))
        author = link.find("span", class_=re.compile(r"BookCard_authors"))

        if title:
            title = title.get_text(strip=True)
        else:
            title = "Unknown"

        if author:
            author = author.get_text(strip=True)
        else:
            author = "Unknown"

        book_details = {"Title": title, "Author": author, "URL": book_url}

        books.append(book_details)
        time.sleep(1)

    return books


def main():
    page_url = "https://www.penguin.co.uk/penguin-classics/classics-list?classicsType=Fiction&page=1"
    max_pages = 100
    current_page = 1

    while current_page <= max_pages:
        print(f"Scraping page {current_page}...")
        books_on_page = extract_books_from_list(page_url)

        if not books_on_page:
            print(f"No more books found on page {current_page}. Ending pagination.")
            break

        for book in books_on_page:
            book_details = extract_book_details(book["URL"])
            if book_details:
                print(book_details)
                print("-" * 40)

                with open("books.json", mode="a", encoding="utf-8") as json_file:
                    json.dump(book_details, json_file, ensure_ascii=False)
                    json_file.write("\n")

        current_page += 1
        page_url = f"https://www.penguin.co.uk/penguin-classics/classics-list?classicsType=Fiction&page={current_page}"

    print("Scraping completed.")


if __name__ == "__main__":
    main()