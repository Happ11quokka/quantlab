import pandas as pd

# 엑셀 파일 읽기 (파일 이름이 실제로 엑셀 파일 형식이면 확장자가 csv여도 괜찮습니다)
df = pd.read_excel('korean_data.csv', engine='openpyxl')
print("전체 컬럼:", df.columns.tolist())

# 필요한 열만 선택 (컬럼명이 정확한지 확인하세요)
selected_columns = ['제목', '일자', '본문', 'URL', '언론사', '통합 분류1']
# 만약 컬럼명이 다르다면 실제 컬럼명으로 수정해야 합니다.
df_selected = df[selected_columns]

# 필수 열에 결측값이 있는 행 제거 (옵션)
df_selected = df_selected.dropna(subset=selected_columns)

# 전처리된 데이터를 CSV 파일로 저장 (한글 깨짐 방지)
output_filename = 'korean_data_selected.csv'
df_selected.to_csv(output_filename, index=False, encoding='utf-8-sig')
print(f"전처리 완료: '{output_filename}' 파일로 저장되었습니다.")
