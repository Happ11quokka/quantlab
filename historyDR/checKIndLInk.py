import csv
import requests


def check_link(url):
    """
    URL에 GET 요청을 보낸 후,
    1) 정상 페이지(첫 번째 스크린샷 구조)인지 
    2) blank.html(두 번째 스크린샷)로 넘어가는지 판별하여 문자열을 반환합니다.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/111.0.0.0 Safari/537.36"
            ),
            "Referer": "https://kind.krx.co.kr"  # Referer 헤더 추가
        }
        # Session을 사용하여 쿠키 등을 유지
        with requests.Session() as s:
            s.headers.update(headers)
            # 초기 접속: 쿠키 등을 받아오기 위해 메인 페이지에 먼저 요청
            s.get("https://kind.krx.co.kr", timeout=5)
            response = s.get(url, timeout=5)

            final_url = response.url
            html_text = response.text

            if "blank.html" in final_url:
                return "틀린 링크 (blank.html)"

            keywords = ["docpathframe", "downloadform",
                        "SNS계정 START", "class=\"pop\"", "filedownloadframe"]
            if any(keyword in html_text for keyword in keywords):
                return "정상 링크"
            else:
                return "틀린 링크"

    except requests.exceptions.RequestException as e:
        return f"오류 발생: {e}"


def main():
    csv_file = "generated_links.csv"  # CSV 파일 경로
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            url = row[0].strip()
            if not url:
                continue
            result = check_link(url)
            print(f"{url} => {result}")


if __name__ == "__main__":
    main()
