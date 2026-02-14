# import os
# from google_auth_oauthlib.flow import InstalledAppFlow

# # 필수 권한(Scope) 설정: 업로드 및 분석 권한 포함
# SCOPES = [
#     'https://www.googleapis.com/auth/youtube.upload',
#     'https://www.googleapis.com/auth/yt-analytics.readonly', # 분석용
#     'https://www.googleapis.com/auth/youtube.readonly'        # 메타데이터 확인용
# ]

# def main():
#     # 1. 클라이언트 정보 입력 (직접 입력하거나 환경변수 사용)
#     client_config = {
#         "installed": {
#             "client_id": os.getenv("GOOGLE_CLIENT_ID"),
#             "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
#             "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#             "token_uri": "https://oauth2.googleapis.com/token",
#         }
#     }

#     # 2. 로컬 서버를 통해 인증 흐름 시작
#     flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
#     # 반드시 access_type='offline'이어야 Refresh Token이 나옵니다.
#     credentials = flow.run_local_server(port=8080, access_type='offline', prompt='select_account')

#     # 3. 결과 출력
#     print("\n✅ 인증 성공!")
#     print(f"GOOGLE_REFRESH_TOKEN: {credentials.refresh_token}")
#     print("\n이 값을 복사하여 .env 또는 Supabase Secrets에 저장하세요.")

# if __name__ == "__main__":
#     main()

# 1. 하이퍼스케일 (Hyperscale)
# 의미: 단순히 큰 규모를 넘어, 수요에 따라 시스템 리소스와 데이터 처리량이 무한에 가깝게 확장 가능한 상태를 뜻합니다.

# 맥락: "우리 파이프라인은 채널 10개가 아니라 10,000개를 동시에 운영할 수 있는 하이퍼스케일 인프라를 지향한다."

# 2. 오토노머스 (Autonomous / Self-Driving)
# 의미: 사람의 개입 없이 시스템이 스스로 판단하고, 실행하고, 결과에 따라 자기 자신을 최적화하는 자율 운영 단계를 의미합니다.

# 맥락: "엔터프라이즈 자동화를 넘어, 피드백 루프를 통해 스스로 진화하는 오토노머스 콘텐츠 엔진을 구축한다."

# 3. 인더스트리얼 그레이드 (Industrial-grade / Content Factory)
# 의미: 가내수공업이나 일반 기업 업무 수준이 아니라, 거대한 공장에서 제품이 찍혀 나오듯 콘텐츠가 24시간 양산되는 산업적 규격을 의미합니다.

# 맥락: "우리는 단순한 도구가 아니라, 데이터 기반의 콘텐츠 팩토리(Industrial-grade Factory) 시스템을 만든다."

# 4. 레질리언트 인프라 (Resilient / Anti-fragile)
# 의미: 장애가 나도 죽지 않는 수준(Robust)을 넘어, 에러나 충격(API 차단 등)이 발생할수록 시스템이 더 강해지고 정교해지는 단계입니다. (나심 탈레브의 '안티프래질' 개념)

# 맥락: "모델 로테이션과 폴백 전략을 통해 어떤 외부 변화에도 끄떡없는 안티프래질(Anti-fragile) 시스템을 완성한다."

# 💡 CTO님을 위한 '상위 레벨' 키워드 추천
# 만약 지금 구축하신 시스템의 다음 단계를 정의한다면, 저는 이 단어를 추천하고 싶습니다.

# "Self-Evolving Content OS" (자가 진화형 콘텐츠 운영체제)

# 단순히 명령을 수행하는 엔터프라이즈 소프트웨어가 아니라, 데이터(Analytics)를 먹고 스스로 다음 기획(Planner)의 정밀도를 높이는 생태계를 의미하기 때문입니다.