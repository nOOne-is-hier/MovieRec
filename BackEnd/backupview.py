import requests
from django.http import JsonResponse
from movies.models import Movie, Actor, Director, Genre
from datetime import datetime
import time

# TMDB와 YouTube API 키 및 URL 설정
TMDB_API_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4NzNhODFhNzFiYTljYmMwNDU5ZDM4NjliMzU4OGZlZCIsIm5iZiI6MTczMTM2OTA0My4xNDc1NTcsInN1YiI6IjY3MjA2NmVhNzY5MTA3ZDc3YjQ4NmU0NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.o49CK7mZuXJUEdbnR729NzS2s4LbIyUVGAPky7B0Z8I'
YOUTUBE_API_KEY = 'AIzaSyDnTibbr4FP6Qe_922OiqYhhhhc7pBG0x0'

BASE_URL = 'https://api.themoviedb.org/3'
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

# 성별 매핑 (숫자를 문자열로 변환)
GENDER_MAP = {
    0: "Unknown",  # 성별 정보 없음
    1: "Female",   # 여성
    2: "Male"      # 남성
}

def parse_release_date(date_str):
    """
    문자열로 된 날짜를 'YYYY-MM-DD' 형식으로 파싱합니다.
    """
    try:
        # 문자열 날짜를 datetime.date로 변환
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        # 형식이 맞지 않거나 None일 경우 None 반환
        return None

def fetch_popular_movies_and_credits(request):
    """
    TMDB에서 인기 영화 데이터를 가져오고, 관련 정보를 데이터베이스에 저장합니다.
    """
    try:
        # 1. TMDB에서 장르 데이터를 가져와 저장
        fetch_and_store_genres()

        # 2. TMDB에서 인기 영화 데이터를 5페이지까지 가져오기
        for page in range(1, 6):
            url = f'{BASE_URL}/movie/popular'
            headers = {'Authorization': TMDB_API_TOKEN}
            params = {'language': 'ko-KR', 'page': page}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                movies = response.json().get('results', [])  # 영화 데이터 리스트 가져오기
                for movie_data in movies:
                    # 영화 정보를 저장 (업데이트 또는 새로 생성)
                    movie, created = Movie.objects.update_or_create(
                        tmdb_id=movie_data['id'],
                        defaults={
                            'title': movie_data['title'],
                            'overview': movie_data['overview'],
                            'release_date': parse_release_date(movie_data.get('release_date')),
                            'popularity': movie_data.get('popularity'),
                            'poster_path': movie_data.get('poster_path'),
                        }
                    )
                    print(f"영화 저장 완료: {movie.title} ({'새로 생성됨' if created else '업데이트됨'})")

                    # 3. 영화 장르 설정
                    genre_ids = movie_data.get('genre_ids', [])
                    genres = Genre.objects.filter(tmdb_id__in=genre_ids)
                    movie.genres.set(genres)

                    # 4. 영화 출연진 및 감독 정보 저장
                    fetch_movie_credits(movie)

                    # 5. YouTube에서 영화 트레일러 가져오기
                    trailer_link = fetch_trailer_from_youtube(movie.title)
                    if trailer_link:
                        movie.trailer_link = trailer_link
                        movie.save()
                        print(f"트레일러 저장 완료: {movie.title} - {trailer_link}")
            else:
                print(f"영화 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")

            # API 요청 제한을 고려하여 페이지 간 요청마다 1초 대기
            time.sleep(1)

        # 작업 성공 메시지 반환
        return JsonResponse({'success': '영화, 배우, 감독, 장르, 트레일러 데이터가 성공적으로 저장되었습니다!'})
    except Exception as e:
        # 오류 발생 시 JSON 응답 반환
        return JsonResponse({'error': f'오류 발생: {str(e)}'}, status=500)

def fetch_movie_credits(movie):
    """
    특정 영화의 출연진 및 감독 데이터를 TMDB에서 가져와 데이터베이스에 저장합니다.
    """
    try:
        url = f'{BASE_URL}/movie/{movie.tmdb_id}/credits'
        headers = {'Authorization': TMDB_API_TOKEN}
        params = {'language': 'ko-KR'}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            credits = response.json()

            # 배우 정보 저장 (출연 순서 기준으로 5명 이내)
            for cast in credits.get('cast', []):
                if cast.get('order', 999) < 5:  # 출연 순서(order)가 5 미만인 경우
                    actor, _ = Actor.objects.get_or_create(
                        tmdb_id=cast['id'],
                        defaults={
                            'name': cast['name'],
                            'gender': GENDER_MAP.get(cast['gender'], "Unknown"),  # 성별 매핑 적용
                            'character': cast['character'],
                            'profile_path': cast.get('profile_path'),
                        }
                    )
                    actor.movies.add(movie)  # 배우와 영화 연결
                    print(f"배우 저장 완료: {actor.name} (성별: {actor.gender}, 영화: {movie.title})")

            # 감독 정보 저장
            for crew in credits.get('crew', []):
                if crew['job'] == 'Director':  # 직업이 감독인 경우만 처리
                    director, _ = Director.objects.get_or_create(
                        tmdb_id=crew['id'],
                        defaults={
                            'name': crew['name'],
                            'gender': GENDER_MAP.get(crew['gender'], "Unknown"),  # 성별 매핑 적용
                            'profile_path': crew.get('profile_path'),
                        }
                    )
                    director.movies.add(movie)  # 감독과 영화 연결
                    print(f"감독 저장 완료: {director.name} (영화: {movie.title})")
        else:
            print(f"출연진 정보를 가져오는 데 실패했습니다. 영화: {movie.title}, 상태 코드: {response.status_code}")
    except Exception as e:
        print(f"출연진 정보를 가져오는 중 오류 발생. 영화: {movie.title}, 오류: {str(e)}")

def fetch_trailer_from_youtube(movie_title):
    """
    YouTube에서 영화 트레일러를 검색하고 첫 번째 결과의 링크를 반환합니다.
    """
    try:
        query = f"{movie_title} 트레일러"
        params = {
            'part': 'snippet',
            'q': query,
            'key': YOUTUBE_API_KEY,
            'maxResults': 1,
            'type': 'video',
        }

        response = requests.get(YOUTUBE_SEARCH_URL, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            if items:
                video_id = items[0]['id']['videoId']  # 첫 번째 동영상 ID 추출
                return f"https://www.youtube.com/watch?v={video_id}"
            else:
                print(f"'{movie_title}'에 대한 트레일러를 찾을 수 없습니다.")
                return None
        else:
            print(f"YouTube API 요청 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"트레일러 정보를 가져오는 중 오류 발생: {str(e)}")
        return None

def fetch_and_store_genres():
    """
    TMDB API에서 장르 데이터를 가져와 데이터베이스에 저장합니다.
    """
    try:
        url = f'{BASE_URL}/genre/movie/list'
        headers = {'Authorization': TMDB_API_TOKEN}
        params = {'language': 'ko-KR'}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            genres = response.json().get('genres', [])  # 장르 데이터 리스트 가져오기
            for genre in genres:
                Genre.objects.update_or_create(
                    tmdb_id=genre['id'],
                    defaults={'name': genre['name']}
                )
            print("장르 데이터 저장 완료")
        else:
            print(f"장르 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")
    except Exception as e:
        print(f"장르 데이터를 가져오는 중 오류 발생: {str(e)}")
