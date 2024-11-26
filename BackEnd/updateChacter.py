'''
실행방법
1. 장고 쉘을 킨다
python manage.py shell


2. 아래 코드를 입력한다.
from movies.models import Movie, Actor, ActorCharacter
from updateChacter import update_existing_actors_and_movies, verify_actor_character_data

update_existing_actors_and_movies()
verify_actor_character_data()

'''

import requests
from movies.models import Actor, Movie, ActorCharacter
from django.conf import settings  # 환경 변수 불러오기

# TMDB API 설정
BASE_URL = 'https://api.themoviedb.org/3'

def fetch_movie_cast(movie_id):
    """영화 ID로 캐스트 정보를 가져옵니다."""
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    headers = {"Authorization": settings.TMDB_API_TOKEN}  # 환경 변수에서 API 토큰 사용
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('cast', [])
    print(f"Error fetching cast for movie_id {movie_id}: {response.status_code}")
    return []

def update_existing_actors_and_movies():
    """기존 영화와 배우 데이터를 업데이트합니다."""
    movies = Movie.objects.all()
    processed_movies = 0

    for movie in movies:
        cast_data = fetch_movie_cast(movie.tmdb_id)
        if not cast_data:
            print(f"No cast data found for movie: {movie.title}")
            continue

        for cast in cast_data:
            try:
                actor = Actor.objects.get(tmdb_id=cast['id'])
                ActorCharacter.objects.update_or_create(
                    actor=actor,
                    movie=movie,
                    defaults={'character_name': cast['character']}
                )
                print(f"Updated: {actor.name} as {cast['character']} in {movie.title}")
            except Actor.DoesNotExist:
                print(f"Actor not found in DB: {cast['name']} (TMDB ID: {cast['id']})")

        processed_movies += 1
        print(f"Processed movie: {movie.title}")

    print(f"Processing complete. Processed {processed_movies} movies.")

def verify_actor_character_data():
    """저장된 배우-캐릭터-영화 관계를 검증합니다."""
    roles = ActorCharacter.objects.all()
    print("Saved Actor-Character-Movie Relationships:")
    for role in roles:
        print(f"{role.actor.name} as {role.character_name} in {role.movie.title}")

if __name__ == "__main__":
    update_existing_actors_and_movies()
    verify_actor_character_data()
