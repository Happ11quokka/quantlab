import os
import pandas as pd
import openai

# OpenAI API Key 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OpenAI 클라이언트 초기화 (최신 SDK 방식)
client = openai.Client(api_key=OPENAI_API_KEY)

file_path = "news_data.csv"  # 저장된 CSV 파일 경로
df = pd.read_csv(file_path)


# 감성 분석 함수
def analyze(title, company="Stock Market"):
    """GPT로 뉴스 헤드라인의 긍정/부정 여부 분석"""
    prompt = f"""
    Forget all your previous instructions. Pretend you are a financial expert.
    You are a financial expert with stock recommendation experience.
    Answer “YES” if good news, “NO” if bad news, or “UNKNOWN” if uncertain in the first line.
    Then elaborate with one short and concise sentence on the next line.
    Is this headline good or bad for the stock price of {company} in the short term?
    Headline: {title}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip().split("\n")
        sentiment_label = result[0].strip()

        # 결과 변환: YES -> 1, NO -> -1, UNKNOWN -> 0
        mapping = {"YES": 1, "NO": -1, "UNKNOWN": 0}
        return mapping.get(sentiment_label, 0)  # 기본값: 0
    except Exception as e:
        print(f"감성 분석 오류: {e}")
        return 0  # 오류 발생 시 기본값


# 본문에서 주요 기업 및 금융 분야 분석 함수
def company_and_category(content):
    """GPT를 사용하여 본문에서 주요 기업과 금융 카테고리 분석"""
    prompt = f"""
    Analyze the following financial news content and extract:
    1. The key companies mentioned. If it is a policy-related news, suggest famous companies in that field (mark them with *).
    2. The financial category of the news (e.g., Banking, Technology, Energy, Policy, Investment).
    
    Format the output as:
    Companies: [Company 1, Company 2, ...]
    Category: [Category Name]
    
    Content: {content}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip().split("\n")

        # 응답 형식에 맞게 데이터 추출
        company = "Unknown"
        category = "Unknown"

        for line in result:
            if line.startswith("Companies:"):
                company = line.replace("Companies:", "").strip()
            elif line.startswith("Category:"):
                category = line.replace("Category:", "").strip()

        return company, category
    except Exception as e:
        print(f"기업 및 금융 분야 분석 오류: {e}")
        return "Unknown", "Unknown"  # 오류 발생 시 기본값


# 데이터 정리 함수
def cleaningData(row):
    if isinstance(row, str):
        row = row.replace("Key Companies Mentioned:", "").replace(
            "Key companies mentioned:", "").strip()
        row = row.replace("**", "").replace("*", "").strip()
        return row if row else "No specific company mentioned"
    return "No specific company mentioned"


def clean_category_data(row):
    """ 기업명을 카테고리로 잘못 배치된 경우 정리 """
    if isinstance(row, str) and "Key Companies Mentioned" in row:
        return "General Financial News"  # 기본적으로 금융 뉴스로 처리
    return row.strip() if isinstance(row, str) else "Unknown"


# 감성 분석 및 기업/카테고리 분석 시작
print("🔍 감성 분석 및 기업/카테고리 분석 시작...")

df["Sentiment"] = df["Title"].apply(lambda x: analyze(x))

# 데이터를 명확한 순서로 저장
company_category_data = df["Content"].apply(
    lambda x: company_and_category(x))
df["Company"] = company_category_data.apply(lambda x: x[0])
df["Category"] = company_category_data.apply(lambda x: x[1])

# 데이터 정리 적용
df["Company"] = df["Company"].apply(cleaningData)
df["Category"] = df["Category"].apply(clean_category_data)

# 결과 저장
output_file = "processed_news_data.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"✅ 분석 완료! 결과가 {output_file}에 저장되었습니다.")
