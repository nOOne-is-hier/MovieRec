
'''
실행방법
1. 장고 쉘을 킨다
python manage.py shell


2. 아래 코드를 입력한다.
from movies.models import Movie, Actor, Director
from movies.models import fetch_image_config

def update_to_full_urls():
    base_url, profile_sizes, poster_sizes = fetch_image_config()
    poster_size = poster_sizes[1] if len(poster_sizes) > 1 else poster_sizes[0]
    profile_size = profile_sizes[1] if len(profile_sizes) > 1 else profile_sizes[0]

    movies_updated = 0
    for movie in Movie.objects.all():
        if movie.poster_path and not movie.poster_path.startswith("http"):
            movie.poster_path = f"{base_url}{poster_size}{movie.poster_path}"
            movie.save()
            movies_updated += 1

    actors_updated = 0
    for actor in Actor.objects.all():
        if actor.profile_path and not actor.profile_path.startswith("http"):
            actor.profile_path = f"{base_url}{profile_size}{actor.profile_path}"
            actor.save()
            actors_updated += 1

    directors_updated = 0
    for director in Director.objects.all():
        if director.profile_path and not director.profile_path.startswith("http"):
            director.profile_path = f"{base_url}{profile_size}{director.profile_path}"
            director.save()
            directors_updated += 1

    print(f"Movies updated: {movies_updated}")
    print(f"Actors updated: {actors_updated}")
    print(f"Directors updated: {directors_updated}")

update_to_full_urls()


'''


