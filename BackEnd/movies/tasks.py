import requests
import re
import html
from django.conf import settings
from .models import News, Movie



def fetch_and_save_movie_news(movie_title):
    MAX_ADDITIONAL_REQUESTS = 5  # 최대 추가 요청 횟수
    additional_request_count = 0
    """
    영화 제목으로 뉴스를 검색하고 최소 3개의 뉴스를 저장.
    """
    NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"
    HEADERS = {
        "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
    }
    params = {"query": f"{movie_title} 영화", "display": 3, "sort": "sim"}

    # 1. API 호출
    response = requests.get(NAVER_API_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"네이버 API 호출 실패: {response.status_code}")
        return

    # 2. Movie 모델에서 영화 객체 확인
    try:
        movie = Movie.objects.get(title=movie_title)
    except Movie.DoesNotExist:
        print(f"영화 '{movie_title}'가 데이터베이스에 없습니다.")
        return

    data = response.json()
    articles = []  # 중복 제거를 위한 리스트

    # 3. 뉴스 데이터 필터링
    for item in data.get("items", []):
        # HTML 태그와 특수 문자를 정리
        clean_title = re.sub(r"<[^>]*>", "", item["title"]).strip()
        clean_description = re.sub(r"<[^>]*>", "", item["description"]).strip()
        clean_title = html.unescape(clean_title)
        clean_description = html.unescape(clean_description)
        url = item["link"]

        # 중복 확인 (articles와 DB 모두 확인)
        if any(article["title"] == clean_title and article["url"] == url for article in articles):
            print(f"중복된 뉴스 제외 (articles 내부): {clean_title}")
            continue
        if News.objects.filter(title=clean_title, url=url).exists():
            print(f"중복된 뉴스 제외 (DB): {clean_title}")
            continue

        # 영화 제목 포함 여부 확인
        if movie_title in clean_title or movie_title in clean_description:
            articles.append({
                "title": clean_title,
                "content": clean_description,
                "url": url,
            })
        else:
            print(f"제외된 뉴스: {clean_title}")

    # 부족한 경우 추가 요청
    while len(articles) < 3 and additional_request_count < MAX_ADDITIONAL_REQUESTS:
        print(f"{movie_title} 관련 뉴스 부족, 추가 검색 시도... (시도 {additional_request_count + 1}/{MAX_ADDITIONAL_REQUESTS})")
        additional_params = {"query": f"{movie_title} 개봉", "display": 50}
        additional_response = requests.get(NAVER_API_URL, headers=HEADERS, params=additional_params)
        
        if additional_response.status_code == 200:
            additional_data = additional_response.json()
            for item in additional_data.get("items", []):
                clean_title = re.sub(r"<[^>]*>", "", item["title"]).strip()
                clean_description = re.sub(r"<[^>]*>", "", item["description"]).strip()
                clean_title = html.unescape(clean_title)
                clean_description = html.unescape(clean_description)
                url = item["link"]

                # 중복 확인
                if any(article["title"] == clean_title and article["url"] == url for article in articles):
                    continue
                if News.objects.filter(title=clean_title, url=url).exists():
                    continue

                if movie_title in clean_title:
                    articles.append({
                        "title": clean_title,
                        "content": clean_description,
                        "url": url,
                    })
                if len(articles) >= 3:
                    break
        else:
            print(f"추가 검색 실패: {additional_response.status_code}")
            break

        additional_request_count += 1

    # 5. 뉴스 저장
    for article in articles[:3]:
        News.objects.create(
            movie=movie,
            title=article["title"],
            content=article["content"],
            url=article["url"]
        )
        print(f"저장 완료: {article['title']}")
