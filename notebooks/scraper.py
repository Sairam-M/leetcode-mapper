import argparse
import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_gfg(url):
    """Scrape a GeeksforGeeks problem page and return a sanitized result."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return {
                "url": url,
                "status": "failed",
                "reason": f"HTTP {response.status_code}",
                "text": None,
            }

        soup = BeautifulSoup(response.text, "html.parser")

        selectors = [
            "div.MainArticleContent_articleMainContentCss__b_1_R",
            "div.article--viewer_content",
            "div.content",
        ]

        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 200:
                    return {"url": url, "status": "success", "text": text[:850]}

        return {"url": url, "status": "failed", "reason": "no matching selector", "text": None}

    except Exception as exc:
        return {"url": url, "status": "error", "reason": str(exc), "text": None}


def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def scrape_classified_links(input_path, delay=1.0, limit=None):
    classified_links = load_json_file(input_path)
    scraped_results = []

    for group_index, group in enumerate(classified_links):
        print(f"Processing group {group_index + 1}/{len(classified_links)}")
        result_group = dict(group)
        scraped_gfg_links = []

        for link_obj in group.get("classified_links", []):
            if link_obj.get("type") == "gfg_problem":
                url = link_obj.get("url")
                if not url:
                    continue
                result = scrape_gfg(url)
                print(f"  {url} -> {result['status']}")
                scraped_gfg_links.append(result)
                time.sleep(delay)

                if limit is not None and len(scraped_gfg_links) >= limit:
                    print("Reached per-group limit.")
                    break

        result_group["scraped_gfg_links"] = scraped_gfg_links
        scraped_results.append(result_group)

    return scraped_results


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape GeeksforGeeks problem pages from classified links JSON.")
    parser.add_argument("input", help="Input classified links JSON file")
    parser.add_argument("output", help="Output JSON file for scraped results")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between requests")
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of GFG links to scrape per group")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    scraped_data = scrape_classified_links(input_path, delay=args.delay, limit=args.limit)
    save_json_file(output_path, scraped_data)
    print(f"Saved scraped results to: {output_path}")


if __name__ == "__main__":
    main()
