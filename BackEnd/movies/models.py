from django.db import models
import requests
import math

# TMDB API의 Bearer Token. TMDB 계정에서 발급받아 여기에 입력하세요.
API_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4NzNhODFhNzFiYTljYmMwNDU5ZDM4NjliMzU4OGZlZCIsIm5iZiI6MTczMTM2OTA0My4xNDc1NTcsInN1YiI6IjY3MjA2NmVhNzY5MTA3ZDc3YjQ4NmU0NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.o49CK7mZuXJUEdbnR729NzS2s4LbIyUVGAPky7B0Z8I'

# TMDB Configuration API의 URL. 이미지 설정 정보를 가져옵니다.
CONFIG_URL = 'https://api.themoviedb.org/3/configuration'


def fetch_image_config():
    """
    TMDB의 /configuration API를 호출하여 이미지 URL과 지원되는 크기 목록을 가져옵니다.
    
    Returns:
        tuple: (base_url, profile_sizes, poster_sizes)
            - base_url: 이미지의 기본 URL
            - profile_sizes: 프로필 이미지에서 지원되는 크기 목록
            - poster_sizes: 포스터 이미지에서 지원되는 크기 목록
    """
    try:
        response = requests.get(CONFIG_URL, headers={'Authorization': API_TOKEN})
        if response.status_code == 200:
            config = response.json()
            return config['images']['base_url'], config['images']['profile_sizes'], config['images']['poster_sizes']
        else:
            print(f"Failed to fetch configuration: {response.status_code}")
            return "https://image.tmdb.org/t/p/", ["w185"], ["w500"]
    except Exception as e:
        print(f"Error fetching configuration: {e}")
        return "https://image.tmdb.org/t/p/", ["w185"], ["w500"]


# 장르 데이터를 저장하는 모델
class Genre(models.Model):
    tmdb_id = models.IntegerField(unique=True)  # TMDB 고유 ID
    name = models.CharField(max_length=100)  # 장르 이름

    def __str__(self):
        return self.name

# 영화 데이터를 저장하는 모델
class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)  # TMDB 고유 ID
    title = models.CharField(max_length=255)  # 영화 제목
    overview = models.TextField(null=True, blank=True)  # 영화 설명
    release_date = models.DateField(null=True, blank=True)  # 영화 개봉일
    popularity = models.FloatField(null=True, blank=True)  # 영화의 TMDB 인기 점수
    poster_path = models.CharField(max_length=255, null=True, blank=True)  # 포스터 이미지 경로
    trailer_link = models.URLField(max_length=500, null=True, blank=True)  # 유튜브 트레일러 링크
    genres = models.ManyToManyField('Genre', related_name="movies")  # 영화와 장르의 다대다 관계
    normalized_popularity = models.FloatField(null=True, blank=True)  # 새 필드

    def calculate_normalized_popularity(self):
        """
        popularity 값을 0-10 사이로 정규화
        """
        if self.popularity is None:
            return 0
        BASE = 1000
        LOG_BASE = math.log(BASE + 1)
        normalized = (math.log(self.popularity + 1) / LOG_BASE) * 7
        return min(round(normalized, 1), 10)

    def save(self, *args, **kwargs):
        # 저장 전에 정규화 값을 계산
        self.normalized_popularity = self.calculate_normalized_popularity()
        super().save(*args, **kwargs)
    

    def __str__(self):
        return self.title  # 문자열 표현: 영화 제목

    
# 배우 데이터를 저장하는 모델
class Actor(models.Model):
    tmdb_id = models.IntegerField(unique=True)  # TMDB 고유 ID
    name = models.CharField(max_length=255)  # 배우 이름
    gender = models.CharField(
        max_length=30,
        choices=[
            ("Unknown", "Unknown"),  # 성별 미지정
            ("Female", "Female"),   # 여성
            ("Male", "Male")        # 남성
        ],
        default="Unknown"
    )  # 성별
    profile_path = models.CharField(max_length=255, null=True, blank=True)  # 프로필 이미지 경로
    movies = models.ManyToManyField("Movie", related_name='actor_movies')  # 배우와 영화의 다대다 관계
    birthdate = models.DateField(null=True, blank=True)  # 배우의 생년월일 (추가)
    biography = models.TextField(null=True, blank=True)  # 배우의 약력 (추가)
    birthplace = models.CharField(max_length=255, null=True, blank=True)  # 배우의 출생지 (추가)

    DEFAULT_PROFILE_IMAGE = "https://via.placeholder.com/200x300?text=No+Image"



    def __str__(self):
        return self.name


# 감독 데이터를 저장하는 모델
class Director(models.Model):
    tmdb_id = models.IntegerField(unique=True)  # TMDB 고유 ID
    name = models.CharField(max_length=255)  # 감독 이름
    gender = models.CharField(
        max_length=30,
        choices=[
            ("Unknown", "Unknown"),  # 성별 미지정
            ("Female", "Female"),   # 여성
            ("Male", "Male")        # 남성
        ],
        default="Unknown"
    )  # 성별
    profile_path = models.CharField(max_length=255, null=True, blank=True)  # 프로필 이미지 경로
    movies = models.ManyToManyField("Movie", related_name='director_movies')  # 감독과 영화의 다대다 관계
    birthdate = models.DateField(null=True, blank=True)  # 감독의 생년월일 (추가)
    biography = models.TextField(null=True, blank=True)  # 감독의 약력 (추가)
    birthplace = models.CharField(max_length=255, null=True, blank=True)  # 감독의 출생지 (추가)

    DEFAULT_PROFILE_IMAGE = "https://via.placeholder.com/200x300?text=No+Image"


    def __str__(self):
        return self.name


# 영화 관련 뉴스 데이터를 저장하는 모델
from django.utils.timezone import now

class News(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='news', help_text="영화 관련 뉴스")
    title = models.CharField(max_length=255, help_text="뉴스 제목")
    content = models.TextField(help_text="뉴스 내용")
    url = models.URLField(max_length=500, help_text="뉴스 링크")
    created_at = models.DateTimeField(default=now, help_text="저장 시간")  

    def __str__(self):
        return f"{self.movie.title} - {self.title}"


# 영화 캐릭터 중개모델
class ActorCharacter(models.Model):
    actor = models.ForeignKey('Actor', on_delete=models.CASCADE, related_name='movie_roles')
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE, related_name='actor_roles')
    character_name = models.CharField(max_length=255, null=True, blank=True)  # 극 중 캐릭터 이름

    def __str__(self):
        return f"{self.actor.name} as {self.character_name} in {self.movie.title}"
