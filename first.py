import json
import re
from datetime import datetime

input_file = "/Users/imdonghyeon/quantlab/results/nate_news.json"
with open(input_file, "r", encoding="utf-8") as f:
    articles = json.load(f)

for article in articles:
    content = article.get("content", "")
    match = re.search(r"기사전송\s*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})", content)
    if match:
        article["date"] = match.group(1)
    else:
        article["date"] = article.get("date", "")

# 날짜 문자열을 datetime 객체로 변환해 오름차순 정렬
articles.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"))

output_file = "/Users/imdonghyeon/quantlab/results/first.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"✅ Updated date field saved to {output_file}")
