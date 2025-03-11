import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import time

# Yahoo Finance 뉴스 페이지 URL
BASE_URL = "https://finance.yahoo.com/topic/latest-news/"

# HTTP 요청 헤더 (크롤링 차단 방지)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def get_news_links():
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"페이지 요청 오류: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # 뉴스 기사 링크 크롤링 (다양한 구조 반영)
    articles = soup.select("a.subtle-link.fin-size-small.titles.noUnderline")
    articles += soup.select("a.tw-w-full.titles-link.noUnderline")

    news_data = []

    for article in articles:
        if "href" in article.attrs:
            url = urljoin(BASE_URL, article["href"])
            title_tag = article.find("h3", class_="clamp yf-82qtw3")
            title = title_tag.text.strip() if title_tag else "제목 없음"
            news_data.append({"Title": title, "URL": url})

    if not news_data:
        print("기사 링크를 찾을 수 없습니다. HTML 구조를 확인하세요.")

    return news_data[:30]  # 상위 30개 기사만 저장


def scrape_article(article):
    url = article["URL"]

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"기사 요청 오류: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 기사 제목 크롤링 (다양한 구조 반영)
    title_tag = soup.find("div", class_="cover-title yf-1rjrr1")  # 첫 번째 구조
    if not title_tag:
        title_tag = soup.find("h3", class_="clamp yf-82qtw3")  # 두 번째 구조
    title = title_tag.text.strip() if title_tag else article["Title"]

    paragraphs = soup.find_all("p")
    content = "\n".join([p.text.strip()
                        for p in paragraphs]) if paragraphs else "본문 없음"

    article["Title"] = title  # 제목 업데이트
    article["Content"] = content  # 본문 추가
    return article


if __name__ == "__main__":
    news_data = get_news_links()
    articles_data = []

    if not news_data:
        print(" 기사 링크를 찾을 수 없습니다.")
    else:
        print(f"감지된 기사 {len(news_data)}개 크롤링 시작...")

        for article in news_data:
            scraped_article = scrape_article(article)
            if scraped_article:
                articles_data.append(scraped_article)
            time.sleep(1)  # 크롤링 속도 조절 (서버 차단 방지)

    df = pd.DataFrame(articles_data)
    csv_filename = "news_data.csv"
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

    print(f"\n✅ 데이터가 CSV 파일로 저장되었습니다: {csv_filename}")
