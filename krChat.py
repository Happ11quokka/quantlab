import os
import json
import re
import openai
from datetime import datetime
from collections import defaultdict
from pykrx import stock  # pip install pykrx

# OPENAI API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

# 구버전 방식의 client 인스턴스 생성 (openai==0.28)
client = openai.Client(api_key=OPENAI_API_KEY)

# 파일 경로 (필요에 따라 수정)
input_file = "/Users/imdonghyeon/quantlab/results/first.json"
output_file = "/Users/imdonghyeon/quantlab/results/chattmp2.json"

# JSON 데이터 불러오기
with open(input_file, "r", encoding="utf-8") as f:
    news_data = json.load(f)

# 다양한 날짜 포맷을 지원하는 파서 함수 (정렬용)


def parse_date(s):
    s = s.strip()
    if " " in s and ":" in s:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unsupported datetime format with time: {s}")
    else:
        try:
            dt = datetime.strptime(s, "%Y%m%d")
        except ValueError:
            try:
                dt = datetime.strptime(s, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Unsupported date format without time: {s}")
        dt = dt.replace(hour=9, minute=0)  # 기본 시간 09:00 (정렬용으로만 사용)
        return dt


# 원본 "date" 필드를 변경하지 않고, 정렬을 위해 파싱한 값으로만 정렬합니다.
news_data.sort(key=lambda x: parse_date(x["date"]))


def analyze(title, company="Stock Market"):
    prompt = f"""
이전의 모든 지시사항은 잊으세요. 당신은 주식 추천 경험이 있는 금융 전문가입니다.
헤드라인이 긍정적이면 "YES", 부정적이면 "NO", 모호하면 "UNKNOWN"을 첫 줄에 작성하고,
두 번째 줄에 짧은 설명을 덧붙여주세요.
뉴스 헤드라인: {title}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",  # 필요시 모델명을 변경하세요.
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
    except Exception as e:
        print(f"Error in analyze() API call: {e}")
        return 0

    full_response = resp.choices[0].message.content.strip()
    label = full_response.split("\n")[0].strip().upper()
    print(f"[DEBUG] 헤드라인: {title}\n응답: {full_response}\n해석된 라벨: {label}\n")
    return {"YES": 1, "NO": -1, "UNKNOWN": 0}.get(label, 0)


def company_and_category(content):
    prompt = f"""
뉴스 내용을 분석해 주요 기업 리스트와 금융 카테고리를 추출하세요.
출력 형식:
Companies: [기업1, 기업2]
Category: [카테고리]
내용: {content}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",  # 필요시 모델명을 변경하세요.
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
    except Exception as e:
        print(f"Error in company_and_category() API call: {e}")
        return "Unknown", "Unknown"

    full_response = resp.choices[0].message.content.strip()
    lines = full_response.split("\n")
    comp = next((l.replace("Companies:", "").strip()
                for l in lines if l.startswith("Companies:")), "Unknown")
    cat = next((l.replace("Category:", "").strip()
               for l in lines if l.startswith("Category:")), "Unknown")
    print(
        f"[DEBUG] 콘텐츠 분석 응답:\n{full_response}\n추출된 기업: {comp}, 카테고리: {cat}\n")
    return comp, cat


def cleaningData(row):
    if isinstance(row, str):
        return row.replace("Key Companies Mentioned:", "").replace("*", "").strip()
    return "Unknown"


def clean_category_data(row):
    if isinstance(row, str):
        return row.strip()
    return "Unknown"


print("🔍 감성 및 기업/카테고리 분석 시작...")

for idx, item in enumerate(news_data):
    item["Sentiment"] = analyze(item["title"])
    comp, cat = company_and_category(item["content"])
    item["Company"] = cleaningData(comp)
    item["Category"] = clean_category_data(cat)
    print(f"[INFO] {idx+1}번째 뉴스 처리 완료.")

# 날짜 변환 없이, 입력 데이터를 그대로 사용하여 출력 파일에 저장합니다.
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print(f"✅ 분석 완료! 결과가 {output_file}에 저장되었습니다.")
