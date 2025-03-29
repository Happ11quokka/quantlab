from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import requests
from datetime import datetime, timedelta
import json
import os


def get_full_text(article_url: str) -> str:
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(article_url)

    # 페이지 전체가 로딩될 때까지 대기 (필요시 WebDriverWait 사용 가능)
    time.sleep(2)

    # 페이지의 <body> 전체 텍스트 추출
    full_text = driver.find_element(By.TAG_NAME, "body").text
    driver.quit()
    return full_text


def get_article_content(article_url: str) -> str:
    """
    Selenium을 사용해 전체 페이지 텍스트를 추출하는 방식으로 본문을 가져온다.
    """
    try:
        content = get_full_text(article_url)
    except Exception as e:
        print(f"❌ Error retrieving full text for {article_url}: {e}")
        content = ""
    return content


def crawl_nate_news(start_date="20250101", end_date="20250102"):
    """
    날짜 범위를 지정하면, 해당 날짜의 기사 목록 페이지에서
    기사 URL을 수집하고 get_article_content()를 통해 본문을 가져와 결과를 반환한다.
    """
    base_url = "https://news.nate.com/MediaList?cp=jo&cate=eco&mid=n1101&type=c&date="
    current_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")

    all_articles = []

    while current_date <= end_date:
        date_str = current_date.strftime("%Y%m%d")
        print(f"📰 크롤링 중: {date_str}")
        url = base_url + date_str

        # 기사 목록 페이지 요청
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.content, "html.parser")

        # 기사 목록에서 a.lt1 태그(기사 링크) 추출
        links = soup.select("a.lt1")
        for link in links:
            title = link.get_text(strip=True)
            article_url = link.get("href")
            if article_url:
                if not article_url.startswith("http"):
                    article_url = "https:" + article_url

                print(f"  ➤ 기사 수집 중: \"{title}\" | URL: {article_url}")
                content = get_article_content(article_url)
                if not content:
                    print(f"   ❌ 본문을 찾지 못했습니다: {article_url}")

                all_articles.append({
                    "date": date_str,
                    "title": title,
                    "url": article_url,
                    "content": content
                })

                time.sleep(0.5)  # 과도한 요청 방지

        current_date += timedelta(days=1)

    return all_articles


def save_to_json(data, filename="nate_news.json"):
    os.makedirs("results", exist_ok=True)
    filepath = os.path.join("results", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ JSON 저장 완료: {filepath}")


if __name__ == "__main__":
    articles = crawl_nate_news()
    save_to_json(articles)
