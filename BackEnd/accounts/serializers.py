# accounts/serializers.py

from rest_framework import serializers
from movies.models import Actor, Movie, Genre, News, Director
from community.models import Review, Post, Comment
from accounts.models import CustomUser, Notification
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncMonth
from drf_spectacular.utils import extend_schema_field
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
import logging

logger = logging.getLogger('custom')

CustomUser = get_user_model()

from django.db.models import Max
from django.core.cache import cache

import base64
from django.core.files.base import ContentFile

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Base64 데이터인지 확인
        if isinstance(data, str) and data.startswith('data:image'):
            # 헤더 분리
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]  # 확장자 추출
            # Base64 데이터를 파일로 변환
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)








# 회원가입 시리얼라이저
# 1. Custom Register Serializer
class CustomRegisterSerializer(RegisterSerializer):
    phone_number = serializers.CharField(
        max_length=15, required=False, allow_blank=True, help_text="전화번호"
    )
    date_of_birth = serializers.DateField(
        required=False, help_text="생년월일 (YYYY-MM-DD 형식)"
    )
    bio = serializers.CharField(
        required=False, allow_blank=True, help_text="자기소개"
    )
    
    
    def custom_signup(self, request, user):
        """
        회원가입 시 사용자 추가 정보 저장
        """
        print("Custom signup called")  # 호출 확인 로그
        print("Validated data:", self.validated_data)  # 요청 데이터 출력
        user.phone_number = self.validated_data.get('phone_number', '')
        user.date_of_birth = self.validated_data.get('date_of_birth',None)
        user.bio = self.validated_data.get('bio', '')
        user.save(update_fields=['phone_number', 'date_of_birth', 'bio'])

# 사용자 프로필 수정 시리얼라이저
class CustomUserDetailsSerializer(UserDetailsSerializer):
    bio = serializers.CharField(source="CustomUser.bio", allow_blank=True, required=False)
    favorite_genres = serializers.ListField(
        source="CustomUser.favorite_genres", child=serializers.CharField(), required=False
    )
    profile_image = serializers.ImageField(required=False)

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('bio', 'favorite_genres', 'profile_image')




# 재사용 많이
class GenreSerializer(serializers.ModelSerializer):
    """
    장르 데이터를 직렬화하기 위한 시리얼라이저.
    """
    class Meta:
        model = Genre
        fields = ['id', 'name']  # 필요한 필드만 정의

# 재사용 많이
class MovieCardSerializer(serializers.ModelSerializer):
    """
    영화 목록 페이지에서 카드 형식으로 영화를 직렬화하기 위한 시리얼라이저.
    popularity 값을 10점 기준으로 정규화하여 반환.
    """
    genres = GenreSerializer(many=True, read_only=True)  # 영화의 장르들

    class Meta:
        ref_name = "AccountsMovieCardSerializer"  # 고유한 이름 설정

        model = Movie
        fields = ['id', 'title', 'poster_path', 'release_date', 'popularity', 'normalized_popularity', 'genres']


class ActorSerializer(serializers.ModelSerializer):
    """
    배우 데이터를 직렬화합니다.
    """
    class Meta:
        model = Actor
        fields = ['name', 'character', 'profile_path']

class DirectorSerializer(serializers.ModelSerializer):
    """
    감독 데이터를 직렬화합니다.
    """
    class Meta:
        model = Director
        fields = ['name', 'profile_path']

class NewsSerializer(serializers.ModelSerializer):
    """
    영화 관련 기사를 직렬화합니다.
    """
    class Meta:
        model = News
        fields = ['title', 'content', 'url']

class ReviewSerializer(serializers.ModelSerializer):
    """
    리뷰 데이터를 직렬화합니다.
    """
    user = serializers.StringRelatedField()  # 작성자 이름 반환

    class Meta:
        model = Review
        fields = ['user', 'rating', 'comment', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    """
    게시글 데이터를 직렬화합니다.
    """
    author = serializers.StringRelatedField()  # 작성자 이름 반환

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'created_at', 'author']

class RelatedMovieSerializer(serializers.ModelSerializer):
    """
    관련 영화 데이터를 직렬화합니다.
    """
    class Meta:
        model = Movie
        fields = ['id', 'title', 'poster_path', 'genres', 'normalized_popularity']




# 1. 회원가입 페이지에 장르 목록 제공 
# -> 폐기 예정. 그냥 회원가입 성공 후, 프론트에서 프로필 수정 페이지로 보내버리자.
class RegistorGenresSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


# ---------------------------------유저 프로필----------------------------------------------
# 통합
from rest_framework import serializers

'''
AHS 수정
'''
class UserProfileSerializer(serializers.ModelSerializer):
    """
    CustomUser Profile 통합 시리얼라이저
    """

    # 좋아한 영화 시리얼라이저 (내부 정의)
    class MovieCardSerializer(serializers.ModelSerializer):
        genres = serializers.StringRelatedField(many=True)  # 장르 이름 표시

        class Meta:
            model = Movie
            fields = ['id', 'title', 'poster_path', 'release_date','normalized_popularity', 'genres']

    # 좋아한 배우/감독 시리얼라이저 (내부 정의)
    class ActorCardSerializer(serializers.ModelSerializer):
        movies = serializers.StringRelatedField(many=True)  # 출연 영화 이름 표시

        class Meta:
            model = Actor
            fields = ['id', 'name', 'profile_path', 'movies']

    class DirectorCardSerializer(serializers.ModelSerializer):
        movies = serializers.StringRelatedField(many=True)  # 연출 영화 이름 표시

        class Meta:
            model = Director
            fields = ['id', 'name', 'profile_path', 'movies']

    # 최근 리뷰/댓글/게시글 시리얼라이저 (내부 정의)
    class RecentReviewSerializer(serializers.ModelSerializer):
        movie_title = serializers.SerializerMethodField()

        class Meta:
            model = Review
            fields = ['id', 'movie_title', 'content', 'rating', 'created_at', 'updated_at']

        def get_movie_title(self, obj):
            # movie가 None일 경우 "영화 선택 안함" 반환
            return obj.movie.title if obj.movie else "영화 선택 안함"

    class RecentCommentSerializer(serializers.ModelSerializer):
        object_id = serializers.SerializerMethodField()  # 댓글 대상 객체 ID

        class Meta:
            model = Comment
            fields = [
                'id', 'object_id', 'content',
                'like_count', 'dislike_count', 'created_at',
            ]

        def get_object_id(self, obj):
            """
            댓글이 작성된 객체의 ID를 반환.
            """
            if obj.review:
                return obj.review.id
            elif obj.post:
                return obj.post.id
            elif obj.actor:
                return obj.actor.id
            elif obj.director:
                return obj.director.id
            elif obj.movie:
                return obj.movie.id
            elif obj.parent:
                return obj.parent.id
            return None

    class RecentPostSerializer(serializers.ModelSerializer):
        class Meta:
            model = Post
            fields = [
                'id', 'title', 'content', 'created_at', 'updated_at'
            ]

    # 팔로워/팔로잉 시리얼라이저 (내부 정의)
    class SimpleUserCardSerializer(serializers.ModelSerializer):
        class Meta:
            model = CustomUser
            fields = ['id', 'username', 'profile_image', 'bio']

    # 통합 필드
    liked_movies = MovieCardSerializer(many=True, read_only=True)
    favorite_actors = ActorCardSerializer(many=True, read_only=True)
    favorite_directors = DirectorCardSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    recent_comments = serializers.SerializerMethodField()
    recent_posts = serializers.SerializerMethodField()
    followers = SimpleUserCardSerializer(many=True, read_only=True)
    following = SimpleUserCardSerializer(many=True, read_only=True)
    mutual_followers = serializers.SerializerMethodField()

    # 사용자 공통 필드
    is_following = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    favorite_genres = serializers.StringRelatedField(many=True)  # 선호 장르 이름
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'profile_image', 'username', 'bio', 'favorite_genres', 'is_following', 'level',
            'liked_movies', 'favorite_actors', 'favorite_directors',
            'recent_reviews', 'recent_comments', 'recent_posts',
            'followers', 'followers_count', 'following', 'following_count', 'mutual_followers'
        ]

    def get_is_following(self, obj):
        """
        현재 로그인한 사용자가 이 유저를 팔로우하고 있는지 여부
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_level(self, obj):
        """
        사용자 레벨 계산 (좋아한 영화 수 + 본 영화 수)
        """
        liked_movies_count = obj.liked_movies.count()
        watched_movies_count = obj.watched_movies.count()
        return liked_movies_count + watched_movies_count

    def get_followers_count(self, obj):
        """
        팔로워 수 반환
        """
        return obj.followers.count()

    def get_following_count(self, obj):
        """
        팔로잉 수 반환
        """
        return obj.following.count()

    def get_mutual_followers(self, obj):
        """
        맞팔로우 사용자 목록 반환
        """
        mutual_follow_users = obj.followers.filter(id__in=obj.following.values_list('id', flat=True))
        serializer = self.SimpleUserCardSerializer(mutual_follow_users, many=True)
        return serializer.data
    
    def get_recent_reviews(self, obj):
        reviews = self.context.get('recent_reviews', [])
        serializer = self.RecentReviewSerializer(reviews, many=True)
        return serializer.data

    def get_recent_comments(self, obj):
        comments = self.context.get('recent_comments', [])
        serializer = self.RecentCommentSerializer(comments, many=True)
        return serializer.data

    def get_recent_posts(self, obj):
        posts = self.context.get('recent_posts', [])
        serializer = self.RecentPostSerializer(posts, many=True)
        return serializer.data













# 유저 프로필 탭 1- 좋아요한 영화 
class UserLikedMoviesSerializer(serializers.ModelSerializer):
    """
    CustomUser Profile - 좋아하는 영화 탭 시리얼라이저
    """
    # MovieCard 시리얼라이저 (내부 정의)
    class MovieCardSerializer(serializers.ModelSerializer):
        genres = serializers.StringRelatedField(many=True)  # 장르 이름 표시

        class Meta:
            model = Movie
            fields = ['id', 'title', 'poster_path', 'normalized_popularity', 'genres']

    liked_movies = MovieCardSerializer(many=True, read_only=True)

    # 사용자 공통 필드
    is_following = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    favorite_genres = serializers.StringRelatedField(many=True)  # 선호 장르 이름을 역참조로 가져옴
    # 팔로잉/팔로워 수 추가
    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = [
            'id', 'profile_image','username', 'bio', 'favorite_genres',
            'is_following', 'level', 'liked_movies','followers_count','following_count',
        ]

    def get_is_following(self, obj):
        """
        현재 로그인한 사용자가 이 사용자를 팔로우 중인지 확인
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_level(self, obj):
        """
        사용자 레벨 계산 (좋아한 영화 수 + 본 영화 수)
        """
        liked_movies_count = obj.liked_movies.count()
        watched_movies_count = obj.watched_movies.count()
        return liked_movies_count + watched_movies_count
    
    def get_following_count(self, obj):
        """
        팔로잉 수
        """
        return obj.following.count()

    def get_followers_count(self, obj):
        """
        팔로워 수
        """
        return obj.followers.count()

# 유저 프로필 탭 2- 좋아하는 인물(배우, 감독)
class UserLikedPeopleSerializer(serializers.ModelSerializer):
    """
    CustomUser Profile - 좋아하는 인물 탭 시리얼라이저
    """
    # ActorCard 시리얼라이저 (내부 정의)
    class ActorCardSerializer(serializers.ModelSerializer):
        movies = serializers.StringRelatedField(many=True)  # 출연한 영화 이름 표시

        class Meta:
            model = Actor
            fields = ['id', 'name', 'profile_path', 'movies']  # 배우 ID, 이름, 프로필 경로, 영화 목록

    # DirectorCard 시리얼라이저 (내부 정의)
    class DirectorCardSerializer(serializers.ModelSerializer):
        movies = serializers.StringRelatedField(many=True)  # 연출한 영화 이름 표시

        class Meta:
            model = Director
            fields = ['id', 'name', 'profile_path', 'movies']  # 감독 ID, 이름, 프로필 경로, 영화 목록

    # 좋아하는 배우와 감독 필드
    favorite_actors = ActorCardSerializer(many=True, read_only=True)
    favorite_directors = DirectorCardSerializer(many=True, read_only=True)

    # 사용자 공통 필드
    is_following = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    favorite_genres = serializers.StringRelatedField(many=True)  # 선호 장르 이름을 역참조로 가져옴
    # 팔로잉/팔로워 수 추가
    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = [
            'id', 'profile_image', 'username', 'bio', 'favorite_genres',
            'is_following', 'level', 'favorite_actors', 'favorite_directors',
            'followers_count','following_count',
        ]

    def get_is_following(self, obj):
        """
        현재 로그인한 사용자가 이 사용자를 팔로우 중인지 확인
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_level(self, obj):
        """
        사용자 레벨 계산 (좋아한 영화 수 + 본 영화 수)
        """
        liked_movies_count = obj.liked_movies.count()
        watched_movies_count = obj.watched_movies.count()
        return liked_movies_count + watched_movies_count
    
    def get_following_count(self, obj):
        """
        팔로잉 수
        """
        return obj.following.count()

    def get_followers_count(self, obj):
        """
        팔로워 수
        """
        return obj.followers.count()


# 유저 프로필 탭 3- Activity(게시글, 리뷰, 댓글)
class UserProfileActivitySerializer(serializers.ModelSerializer):
    """
    CustomUser Profile - Activity 탭 시리얼라이저
    """

    # Recent Review 시리얼라이저 (내부 정의)
    class RecentReviewSerializer(serializers.ModelSerializer):
        movie_title = serializers.CharField(source='movie.title')  # 리뷰 대상 영화 제목
        movie_id = serializers.IntegerField(source='movie.id')    # 리뷰 대상 영화 ID

        class Meta:
            model = Review
            fields = [
                'id', 'movie_title', 'movie_id', 'content', 
                'rating', 'created_at', 'updated_at'
            ]

    # Recent Comment 시리얼라이저 (내부 정의)
    class RecentCommentSerializer(serializers.ModelSerializer):
        object_id = serializers.SerializerMethodField()  # 댓글 대상 객체 ID

        class Meta:
            model = Comment
            fields = [
                'id', 'object_id', 'content', 
                'like_count', 'dislike_count', 'created_at', 
            ]

        def get_object_id(self, obj):
            """
            댓글이 작성된 객체의 ID를 반환 (review, post, actor, director, movie, parent comment).
            """
            if obj.review:
                return obj.review.id
            elif obj.post:
                return obj.post.id
            elif obj.actor:
                return obj.actor.id
            elif obj.director:
                return obj.director.id
            elif obj.movie:
                return obj.movie.id
            elif obj.parent:
                return obj.parent.id
            return None
    def get_following_count(self, obj):
        """
        팔로잉 수
        """
        return obj.following.count()

    def get_followers_count(self, obj):
        """
        팔로워 수
        """
        return obj.followers.count()

    # Recent Post 시리얼라이저 (내부 정의)
    class RecentPostSerializer(serializers.ModelSerializer):
        class Meta:
            model = Post
            fields = [
                'id', 'title', 'content', 'created_at', 'updated_at'
            ]

    # 최근 데이터 필드 정의
    recent_reviews = RecentReviewSerializer(many=True, read_only=True)
    recent_comments = RecentCommentSerializer(many=True, read_only=True)
    recent_posts = RecentPostSerializer(many=True, read_only=True)

    # 사용자 공통 필드
    is_following = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    favorite_genres = serializers.StringRelatedField(many=True)  # 선호 장르 이름을 역참조로 가져옴

    # 팔로잉/팔로워 수 추가
    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = [
            'id', 'profile_image', 'username', 'bio', 'favorite_genres',
            'is_following', 'level', 'recent_reviews', 
            'recent_comments', 'recent_posts','followers_count', 'following_count',
        ]

    def get_is_following(self, obj):
        """
        현재 로그인한 사용자가 이 사용자를 팔로우 중인지 확인
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_level(self, obj):
        """
        사용자 레벨 계산 (좋아한 영화 수 + 본 영화 수)
        """
        liked_movies_count = obj.liked_movies.count()
        watched_movies_count = obj.watched_movies.count()
        return liked_movies_count + watched_movies_count



# 유저 프로필 탭 4- Social(팔로잉, 팔로워 관리)
class UserSocialTabSerializer(serializers.ModelSerializer):
    """
    CustomUser Profile - Social 탭 시리얼라이저
    """
    # 팔로워, 팔로잉, 맞팔로우 시리얼라이저 (내부 정의)
    class SimpleUserCardSerializer(serializers.ModelSerializer):
        class Meta:
            model = CustomUser
            fields = ['id', 'username', 'profile_image', 'bio']  # 공통적으로 필요한 카드 정보

    # 팔로워/팔로잉/맞팔로우 데이터
    followers = SimpleUserCardSerializer(many=True, read_only=True)
    following = SimpleUserCardSerializer(many=True, read_only=True)
    mutual_followers = serializers.SerializerMethodField()

    # 팔로잉/팔로워 수 추가
    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()

    # 사용자 공통 필드
    is_following = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    favorite_genres = serializers.StringRelatedField(many=True)  # 선호 장르 이름을 역참조로 가져옴

    class Meta:
        model = CustomUser
        fields = [
            'id', 'profile_image', 'username', 'bio', 'favorite_genres', 'is_following', 'level',
            'followers', 'followers_count', 'following', 'following_count', 'mutual_followers'
        ]

    def get_mutual_followers(self, obj):
        """
        맞팔로우 사용자 목록
        """
        mutual_follow_users = obj.followers.filter(id__in=obj.following.values_list('id', flat=True))
        serializer = self.SimpleUserCardSerializer(mutual_follow_users, many=True)
        return serializer.data

    def get_following_count(self, obj):
        """
        팔로잉 수
        """
        return obj.following.count()

    def get_followers_count(self, obj):
        """
        팔로워 수
        """
        return obj.followers.count()

    def get_is_following(self, obj):
        """
        현재 사용자가 이 유저를 팔로우하고 있는지 여부
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_level(self, obj):
        """
        사용자 레벨 계산 (좋아한 영화 수 + 본 영화 수)
        """
        liked_movies_count = obj.liked_movies.count()
        watched_movies_count = obj.watched_movies.count()
        return liked_movies_count + watched_movies_count

        
       


# -------------------------------------------------------------------------------------


# 5. 프로필 수정 페이지 GET 요청용 시리얼라이저
class UserProfileReadSerializer(serializers.ModelSerializer):
    favorite_genres = GenreSerializer(many=True, read_only=True)  # 장르 정보 반환

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'profile_image', 'bio', 'favorite_genres'
        ]

        

# 6. 프로필 수정 완료 후 Save Settings를 눌렀을 때(PUT 또는 PATCH 요청)용 시리얼라이저
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    favorite_genres_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all(), write_only=True
    )  # ID를 기반으로 업데이트

    class Meta:
        model = CustomUser
        fields = [
            'profile_image', 'bio', 'favorite_genres_ids'
        ]

    def update(self, instance, validated_data):
        # 프로필 이미지를 업데이트
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        # Bio(자기소개)를 업데이트
        instance.bio = validated_data.get('bio', instance.bio)
        # Favorite Genres 업데이트 (ManyToManyField)
        favorite_genres_ids = validated_data.get('favorite_genres_ids', [])
        instance.favorite_genres.set(favorite_genres_ids)  # ManyToManyField 처리
        instance.save()
        return instance

# -------------------------------------------------------------------------------------

# 7. 알림목록
class NotificationSerializer(serializers.ModelSerializer):
    """
    알림 데이터를 직렬화하기 위한 시리얼라이저
    """
    class Meta:
        model = Notification
        fields = ['id', 'content', 'is_read', 'created_at', 'type', 'link']
        
        
# -------------------------------------------------------------------------------------

# 8. 관리자 페이지 - 대시보드
from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils.timezone import now, timedelta

class DashboardSerializer(serializers.Serializer):
    """
    대시보드 데이터를 제공하는 시리얼라이저.
    """
    def to_representation(self, instance):
        # 사용자 성장 데이터
        user_growth = self.get_user_growth()

        # 장르별 영화 데이터
        genre_data = self.get_genre_movies()

        return {
            'user_growth': user_growth,  # 사용자 성장 그래프 데이터
            'movies_by_genre': genre_data,  # 장르별 영화 수 데이터
        }

    @staticmethod
    def get_user_growth():
        """
        최근 1년간 월별 사용자 증가 데이터를 반환합니다.
        """
        last_year = now() - timedelta(days=365)
        user_growth = CustomUser.objects.filter(created_at__gte=last_year).annotate(
            year=ExtractYear('created_at'),
            month=ExtractMonth('created_at')
        ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

        return [
            {
                'month': f"{data['year']}-{data['month']:02d}",  # '2023-01' 형식으로 반환
                'user_count': data['count'],
            }
            for data in user_growth
        ]

    @staticmethod
    def get_genre_movies():
        """
        각 장르별 영화 개수를 반환합니다.
        """
        genre_movies = Genre.objects.annotate(movie_count=Count('movies')).filter(movie_count__gt=0)
        return [
            {
                'genre': genre.name,
                'movie_count': genre.movie_count,
            }
            for genre in genre_movies
        ]



# 9. 관리자 페이지 - 영화 목록 조회 및 검색 (수정 삭제는 나중에)
class MovieAdminSerializer(serializers.ModelSerializer):
    """
    관리자 대시보드 영화 목록용 시리얼라이저.
    """
    class Meta:
        model = Movie
        fields = ['id', 'title', 'release_date', 'normalized_popularity', 'poster_path']
        

'''
AHS 소프트삭제
'''
# 10. 관리자 페이지 - 유저 목록 조회 및 검색 (수정 삭제는 나중에)
class UserAdminSerializer(serializers.ModelSerializer):
    """
    관리자 대시보드 유저 목록용 시리얼라이저.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'created_at','deleted_at']
        
        
'''
AHS 리뷰 삭제 버그 이슈
'''

# 11. 관리자 페이지 - 리뷰 목록 조회 및 검색 (수정 삭제는 나중에)
class ReviewAdminSerializer(serializers.ModelSerializer):
    """
    관리자 대시보드 리뷰 목록용 시리얼라이저.
    """
    movie_title = serializers.SerializerMethodField()  # 안전한 필드 생성
    user_username = serializers.CharField(source='user.username')

    class Meta:
        model = Review
        fields = ['id', 'movie_title', 'user_username', 'rating', 'content', 'created_at']

    def get_movie_title(self, obj):
        """
        movie가 None일 경우 'No Movie'를 반환.
        """
        return obj.movie.title if obj.movie else "No Movie"

'''
AHS 비밀번호 변경 -> 미구현
'''

from dj_rest_auth.serializers import PasswordResetSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomPasswordResetSerializer(PasswordResetSerializer):
    def validate_email(self, email):
        # 사용자 이메일 확인
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise ValidationError("이 사용자는 비활성화 상태입니다.")
            return email
        except User.DoesNotExist:
            raise ValidationError("해당 이메일을 가진 사용자가 없습니다.")