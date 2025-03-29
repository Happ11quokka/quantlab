import json
import os
import openai
import pandas as pd
import time
from datetime import datetime
from collections import defaultdict

# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
client = openai.Client(api_key=OPENAI_API_KEY)


def normalize_company(company):
    prompt = f"""
다음 기업명을 표준화된 하나의 이름으로 반환해 주세요.
동일한 기업이 여러 방식으로 표현될 경우, 하나의 표준 이름으로 통일합니다.
예시: "제주항공", "jeju air", "무안 제주" → "제주항공"
기업명: "{company}"
표준화된 기업명:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        normalized = response.choices[0].message.content.strip().splitlines()[
            0].strip().strip('"')
        return normalized
    except Exception as e:
        print(f"Error normalizing company '{company}': {e}")
        return company


# -------------------------------------------
# 1. 데이터 로드 및 날짜 포맷 통일, 시간대 분류
# -------------------------------------------
input_file = "/Users/imdonghyeon/quantlab/results/chattmp2.json"
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# 날짜 포맷을 통일하는 함수


def reformat_date(date_str):
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            continue
    # 만약 "YYYYMMDD" 형식이라면, 기본 시간 09:00을 추가합니다.
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        dt = dt.replace(hour=9, minute=0)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        print(f"[WARNING] 날짜 재포맷 실패: {date_str}, 에러: {e}")
        return date_str


# date 컬럼을 통일된 형식으로 변환 (원본 날짜 정보를 보존)
df["date"] = df["date"].apply(reformat_date)

# 시간대 분류 함수 (입력 날짜는 "YYYY-MM-DD HH:MM" 형식)


def classify_time_period(time_str):
    try:
        t = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        hour_min = t.hour * 60 + t.minute
        if hour_min < 540:           # 09:00 이전
            return "장전"
        elif 540 <= hour_min <= 930:   # 09:00 ~ 15:30
            return "장중"
        else:                        # 15:30 이후
            return "장후"
    except Exception as e:
        print(f"시간 파싱 실패: {time_str}, 에러: {e}")
        return "기타"


df["Time_Period"] = df["date"].apply(classify_time_period)

# -------------------------------------------
# 2. 시간대별 기업 표준화 (normalize_company)
# -------------------------------------------
company_mapping = {}
unique_companies = df['Company'].unique()

print("기업명 표준화 진행 중...")
for comp in unique_companies:
    normalized = normalize_company(comp)
    company_mapping[comp] = normalized
    print(f"'{comp}' -> '{normalized}'")
    time.sleep(1)

df['Normalized_Company'] = df['Company'].map(company_mapping)

# -------------------------------------------
# 3. 시간대별 집계 (날짜 정보 포함)
# -------------------------------------------
results_by_period = {}

for period in ["장전", "장중", "장후"]:
    subset = df[df["Time_Period"] == period]
    aggregated = {}

    for _, row in subset.iterrows():
        comp = row["Normalized_Company"]
        sentiment = row.get("Sentiment", 0)
        category = str(row.get("Category", "")).strip()
        date_val = row.get("date", "")

        if comp not in aggregated:
            aggregated[comp] = {
                "Company": comp,
                "Count": 0,
                "Sentiment_Sum": 0,
                "Categories": set(),
                "Dates": []  # 날짜 정보를 저장
            }

        aggregated[comp]["Count"] += 1
        aggregated[comp]["Sentiment_Sum"] += sentiment
        if category:
            aggregated[comp]["Categories"].add(category)
        if date_val:
            aggregated[comp]["Dates"].append(date_val)

    final_results = []
    for comp, stats in aggregated.items():
        count = stats["Count"]
        sentiment_sum = stats["Sentiment_Sum"]
        avg_sentiment = sentiment_sum / count if count > 0 else 0
        final_results.append({
            "Company": comp,
            "Count": count,
            "Average_Sentiment": avg_sentiment,
            "Categories": list(stats["Categories"]),
            "Dates": sorted(list(set(stats["Dates"])))  # 중복 제거 후 정렬
        })

    results_by_period[period] = final_results

# -------------------------------------------
# 4. 결과 저장
# -------------------------------------------
output_file = "/Users/imdonghyeon/quantlab/results/second.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results_by_period, f, ensure_ascii=False, indent=2)

print(f"시간대별 결과 저장 완료: {output_file}")
