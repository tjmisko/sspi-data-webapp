import requests
from bs4 import BeautifulSoup
import time
import json
import re
import pycountry

BASE_URL = "https://www.flagcolorcodes.com/flags/country"

def get_soup(url):
    print(f"[DEBUG] Requesting URL: {url}")
    r = requests.get(url)
    try:
        r.raise_for_status()
        print(f"[DEBUG] Received response: {r.status_code}")
    except requests.HTTPError as e:
        print(f"[ERROR] HTTP error for URL {url}: {e}")
        raise
    return BeautifulSoup(r.text, "html.parser")

def find_last_page(soup):
    print("[DEBUG] Locating pagination div...")
    pag = soup.find("div", class_="pagination")
    if not pag:
        print("[WARN] No pagination found, defaulting to 1 page.")
        return 1

    nums = []
    a_tags = pag.find_all("a", href=True)
    hrefs = [a.get("href") for a in a_tags]
    for href in hrefs:
        nums.append(int(href.split("/")[-1]) if href.split("/")[-1].isdigit() else 0)
    last = max(nums) if nums else 1
    print(f"[DEBUG] Found page numbers: {nums}, last = {last}")
    return last

def parse_figures(soup):
    print("[DEBUG] Parsing figures for colors and country names...")
    data = []
    figures = soup.find_all("figure")
    print(f"[DEBUG] Found {len(figures)} figures on this page.")
    for fig in figures:
        fig_title = fig.find("figcaption").h2.a.get_text(strip=True)
        name = fig_title[0:fig_title.find("Flag Colors")].strip()
        code = ""
        alpha_2 = ""
        official_name = ""
        common_name = ""
        m49 = ""
        flag = ""
        try:
            # remove anything in parentheses
            lookup_query = re.sub(r"\(.*?\)", "", name).strip()
            match = pycountry.countries.search_fuzzy(lookup_query)[0]
            name = match.name if hasattr(match, 'name') else lookup_query
            code = match.alpha_3 if hasattr(match, 'alpha_3') else ""
            alpha_2 = match.alpha_2 if hasattr(match, 'alpha_2') else ""
            official_name = match.official_name if hasattr(match, 'official_name') else ""
            common_name = match.common_name if hasattr(match, 'common_name') else ""
            m49 = match.numeric if hasattr(match, 'numeric') else ""
            flag = match.flag
        except LookupError:
            print(f"[WARN] Could not find pycountry object for {name}")
        colors = ["#" + span["data-clipboard-text"]
                  for span in fig.select(".colors .circle")
                  if span.has_attr("data-clipboard-text")]
        data.append({
            "Country": name,
            "CountryCode": code,
            "OfficialName": official_name,
            "CommonName": common_name,
            "M49": m49,
            "Alpha2": alpha_2,
            "Flag": flag,
            "FlagColors": colors
        })
        print(f"[INFO] Parsed {name}: {colors}")
    return data

def scrape_all():
    print("[INFO] Starting scrape...")
    first_soup = get_soup(BASE_URL)
    last_page = find_last_page(first_soup)
    print(f"[INFO] Total pages to scrape: {last_page}")
    all_countries = []

    for page in range(1, last_page + 1):
        url = f"{BASE_URL}/page/{page}" if page > 1 else BASE_URL
        print(f"[INFO] Scraping page {page}/{last_page}")
        soup = get_soup(url)
        page_data = parse_figures(soup)
        all_countries.extend(page_data)
        time.sleep(0.5)  # be polite

    print(f"[INFO] Scraping complete. Total entries: {len(all_countries)}")
    return all_countries

if __name__ == "__main__":
    results = scrape_all()
    with open('./local/country-flag-colors.json', 'w', encoding='utf-8') as f:
        json.dump(results, f)
