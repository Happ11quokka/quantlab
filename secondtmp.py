import json
import re
from collections import defaultdict

# 입력 파일
input_file = "/Users/imdonghyeon/quantlab/results/second.json"
output_file = "/Users/imdonghyeon/quantlab/results/second_summary.json"

# 기업 이름 분리 함수


def split_companies(raw):
    if raw.startswith("["):
        raw = raw[1:-1]  # 대괄호 제거
    return [comp.strip().strip('"').strip() for comp in raw.split(",") if comp.strip()]

# 카테고리 분리 함수


def split_categories(raw):
    if raw.startswith("["):
        raw = raw[1:-1]  # 대괄호 제거
    return [cat.strip() for cat in raw.split(",") if cat.strip()]


# JSON 로드
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 결과 저장 딕셔너리
summary = {}

for period in ["장전", "장중", "장후"]:
    company_stats = defaultdict(lambda: {
        "Count": 0,
        "Sentiment_Sum": 0,
        "Categories": set()
    })

    for entry in data.get(period, []):
        raw_companies = split_companies(entry["Company"])
        raw_categories = split_categories(entry["Categories"][0])
        sentiment = entry.get("Average_Sentiment", 0)

        for comp in raw_companies:
            stat = company_stats[comp]
            stat["Count"] += 1
            stat["Sentiment_Sum"] += sentiment
            stat["Categories"].update(raw_categories)

    # 정리해서 리스트로 변환
    result_list = []
    for comp, stat in company_stats.items():
        avg_sentiment = stat["Sentiment_Sum"] / \
            stat["Count"] if stat["Count"] > 0 else 0
        result_list.append({
            "Company": comp,
            "Count": stat["Count"],
            "Average_Sentiment": round(avg_sentiment, 4),
            "Categories": sorted(stat["Categories"])
        })

    summary[period] = sorted(
        result_list, key=lambda x: x["Count"], reverse=True)

# 저장
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"✅ 시간대별 기업 분석 저장 완료: {output_file}")
