# movies/serializers.py
from rest_framework import serializers
from community.models import Review, Post, Comment
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Max
from movies.models import Movie, Genre, Actor, Director, News, ActorCharacter
from community.models import Review, Post
from accounts.models import CustomUser, Notification


User = get_user_model()
from django.db.models import Max
from django.core.cache import cache

# 재사용 좀
class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # 사용자 이름
    user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)  # 사용자 ID
    like_count = serializers.IntegerField(read_only=True)
    dislike_count = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField()
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'user_id', 'content', 'created_at',
            'like_count', 'dislike_count', 'movie', 'actor', 'director', 'replies', 'parent'
        ]
        read_only_fields = ['id', 'user', 'user_id', 'created_at', 'like_count', 'dislike_count']

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data





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

    genres = GenreSerializer(many=True, read_only=True)  # 영화의 장르들

    class Meta:
        model = Movie
        fields = ['id', 'title', 'poster_path', 'release_date', 'popularity', 'normalized_popularity', 'genres']

# 통합 시리얼라이저
class UnifiedMovieDetailSerializer(serializers.ModelSerializer):
    # 배우 카드 시리얼라이저
    class MovieActorCardSerializer(serializers.ModelSerializer):
        character_name = serializers.CharField()  # 배역 이름
        actor_id = serializers.IntegerField(source='actor.id')  # 배우 ID
        actor_name = serializers.CharField(source='actor.name')  # 배우 이름
        actor_profile_path = serializers.CharField(source='actor.profile_path')  # 배우 프로필 사진

        class Meta:
            model = ActorCharacter
            fields = ['actor_id', 'actor_name', 'actor_profile_path', 'character_name']

    # 감독 카드 시리얼라이저
    class MovieDirectorCardSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()  # 감독 ID
        name = serializers.CharField()  # 감독 이름
        profile_path = serializers.CharField()  # 감독 프로필 사진

        class Meta:
            model = Director
            fields = ['id', 'name', 'profile_path']

    # 뉴스 시리얼라이저
    class NewsSerializer(serializers.ModelSerializer):
        class Meta:
            model = News
            fields = ['title', 'content', 'url', 'created_at']

    # 댓글 시리얼라이저
    class CommentSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 댓글 작성자 이름 표시

        class Meta:
            model = Comment
            fields = ['id', 'user', 'content', 'created_at', 'like_count', 'dislike_count']

    # 관련 영화 카드 시리얼라이저
    class RelatedMovieCardSerializer(serializers.ModelSerializer):
        genres = serializers.StringRelatedField(many=True)  # 장르 이름 추가

        class Meta:
            model = Movie
            fields = ['id', 'title', 'poster_path', 'normalized_popularity', 'genres']

    # 리뷰 카드 시리얼라이저
    class ReviewCardSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 리뷰 작성자 이름 표시

        class Meta:
            model = Review
            fields = ['id', 'rating', 'content', 'user', 'created_at', 'updated_at']

    # 공통 필드
    genres = serializers.StringRelatedField(many=True)  # 장르 이름
    is_liked = serializers.SerializerMethodField()  # 좋아요 여부

    # 필드
    cast = MovieActorCardSerializer(source='actor_roles', many=True, read_only=True)  # 출연 배우
    crews = MovieDirectorCardSerializer(source='director_movies', many=True, read_only=True)  # 감독 정보
    news = NewsSerializer(many=True, read_only=True)  # 뉴스
    comments = CommentSerializer(source='movie_comments', many=True, read_only=True)  # 댓글
    related_movies = RelatedMovieCardSerializer(many=True, read_only=True)  # 관련 영화
    reviews = ReviewCardSerializer(many=True, read_only=True)  # 리뷰
    trailer_link = serializers.CharField(read_only=True)  # 예고편 링크

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'poster_path', 'genres', 'overview', 'release_date',
            'normalized_popularity', 'is_liked', 'cast', 'crews', 'news', 'comments',
            'related_movies', 'reviews', 'trailer_link'
        ]

    def get_is_liked(self, obj):
        """
        현재 사용자가 이 영화를 좋아요 했는지 여부를 확인.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.liked_movies.filter(pk=obj.pk).exists()
        return False



'''# 영화 디테일 시리얼라이저 탭1
class MovieDetailTabOneSerializer(serializers.ModelSerializer):
    # 배우 카드 시리얼라이저 (내부 정의)
    class MovieActorCardSerializer(serializers.ModelSerializer):
        character_name = serializers.CharField()  # 배역 이름
        actor_id = serializers.IntegerField(source='actor.id')  # 배우 ID
        actor_name = serializers.CharField(source='actor.name')  # 배우 이름
        actor_profile_path = serializers.CharField(source='actor.profile_path')  # 배우 프로필 사진

        class Meta:
            model = ActorCharacter
            fields = ['actor_id', 'actor_name', 'actor_profile_path', 'character_name']

    # 감독 카드 시리얼라이저 (내부 정의)
    class MovieDirectorCardSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()  # 감독 ID
        name = serializers.CharField()  # 감독 이름
        profile_path = serializers.CharField()  # 감독 프로필 사진

        class Meta:
            model = Director
            fields = ['id', 'name', 'profile_path']

    # 뉴스 시리얼라이저 (내부 정의)
    class MovieTabOneNewsSerializer(serializers.ModelSerializer):
        class Meta:
            model = News
            fields = ['title', 'content', 'url', 'created_at']

    # 댓글 시리얼라이저 (내부 정의)
    class MovieTabOneCommentSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 댓글 작성자 이름 표시

        class Meta:
            model = Comment
            fields = ['id', 'user', 'content', 'created_at', 'like_count', 'dislike_count']

    # Cast & Crews 필드
    cast = MovieActorCardSerializer(source='actor_roles', many=True, read_only=True)  # 영화 출연 배우
    crews = MovieDirectorCardSerializer(source='director_movies', many=True, read_only=True)  # 영화 감독

    # 뉴스 및 댓글 필드
    news = MovieTabOneNewsSerializer(many=True, read_only=True)  # 영화 관련 뉴스
    comments = MovieTabOneCommentSerializer(source='movie_comments', many=True, read_only=True)  # 영화 댓글 목록

    # 공통 필드
    genres = serializers.StringRelatedField(many=True)  # StringRelatedField 사용
    is_liked = serializers.SerializerMethodField()  # 좋아요 여부

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'poster_path', 'genres', 'overview', 'release_date',
            'normalized_popularity', 'is_liked', 'news', 'comments', 'cast', 'crews'
        ]

    def get_is_liked(self, obj):
        """
        현재 사용자가 이 영화를 좋아요 했는지 여부를 확인.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.liked_movies.filter(pk=obj.pk).exists()
        return False


# 영화 디테일 시리얼라이저 탭2
class MovieTrailerTabTwoSerializer(serializers.ModelSerializer):
    # 관련된 기사 시리얼라이저 (내부 정의)
    class MovieTabTwoNewsSerializer(serializers.ModelSerializer):
        class Meta:
            model = News
            fields = ['title', 'content', 'url', 'created_at']
    
    # 댓글 시리얼라이저 (내부 정의)
    class MovieTabTwoCommentSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 댓글 작성자의 이름 표시

        class Meta:
            model = Comment
            fields = ['id', 'user', 'content', 'created_at', 'like_count', 'dislike_count']

    # 공통 필드
    genres = serializers.StringRelatedField(many=True)  # StringRelatedField 사용
    # news = MovieTabTwoNewsSerializer(many=True, read_only=True)  # 영화 관련 뉴스
    # comments = MovieTabTwoCommentSerializer(source='movie_comments', many=True, read_only=True)  # 영화 댓글 목록
    is_liked = serializers.SerializerMethodField()  # 좋아요 여부

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'poster_path', 'genres', 'overview', 'release_date',
            'normalized_popularity', 'is_liked', 'trailer_link',
        ]

    def get_is_liked(self, obj):
        """
        현재 사용자가 이 영화를 좋아요 했는지 여부를 확인.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.liked_movies.filter(pk=obj.pk).exists()
        return False


# 영화 디테일 시리얼라이저 탭3
class MovieRelatedTabThreeSerializer(serializers.ModelSerializer):
    # 뉴스 시리얼라이저 (내부 정의)
    class MovieTabThreeNewsSerializer(serializers.ModelSerializer):
        class Meta:
            model = News
            fields = ['title', 'content', 'url', 'created_at']

    # 댓글 시리얼라이저 (내부 정의)
    class MovieTabThreeCommentSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 댓글 작성자 이름 표시

        class Meta:
            model = Comment
            fields = ['id', 'user', 'content', 'created_at', 'like_count', 'dislike_count']
            
    # 관련 영화 카드 시리얼라이저 (내부 정의)
    class RelatedMovieCardSerializer(serializers.ModelSerializer):
        genres = serializers.StringRelatedField(many=True)  # 장르 이름 추가

        class Meta:
            model = Movie
            fields = ['id', 'title', 'poster_path', 'normalized_popularity', 'genres']

    # 리뷰 카드 시리얼라이저 (내부 정의)
    class RelatedReviewCardSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 리뷰 작성자 이름 표시

        class Meta:
            model = Review
            fields = ['id', 'rating', 'content', 'user', 'created_at', 'updated_at']

    # 관련 영화와 리뷰 역참조 필드
    related_movies = RelatedMovieCardSerializer(many=True, read_only=True)  # 관련 영화 목록
    reviews = RelatedReviewCardSerializer(many=True, read_only=True)  # 리뷰 목록

    # 공통 필드
    
    # 뉴스 및 댓글 필드
    # news = MovieTabThreeNewsSerializer(many=True, read_only=True)  # 영화 관련 뉴스
    # comments = MovieTabThreeCommentSerializer(source='movie_comments', many=True, read_only=True)  # 영화 댓글 목록
    genres = serializers.StringRelatedField(many=True)  # 장르 이름
    is_liked = serializers.SerializerMethodField()  # 좋아요 여부

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'poster_path', 'genres', 'overview', 'release_date',
            'normalized_popularity', 'is_liked', 'related_movies', 'reviews'
        ]

    def get_is_liked(self, obj):
        """
        현재 사용자가 이 영화를 좋아요 했는지 여부를 확인.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.liked_movies.filter(pk=obj.pk).exists()
        return False'''




# 배우 프로필 시리얼라이저
class ActorDetailSerializer(serializers.ModelSerializer):
    # 필모그래피 시리얼라이저 (내부 정의)
    class ProfileMovieCardSerializer(serializers.ModelSerializer):
        class Meta:
            model = Movie
            ref_name = "ActorProfileMovieCardSerializer"  # 고유한 ref_name 설정
            fields = ['id', 'title', 'release_date', 'poster_path', 'normalized_popularity']
    
    # 댓글 시리얼라이저 (내부 정의)
    class ActorCommentSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 댓글 작성자의 이름 표시

        class Meta:
            model = Comment
            fields = ['id', 'user', 'content', 'created_at', 'like_count', 'dislike_count']
            
     # 맡았던 캐릭터 목록 시리얼라이저 (내부 정의)
    class CharacterRoleSerializer(serializers.ModelSerializer):
        movie_title = serializers.CharField(source='movie.title')  # 영화 제목
        id = serializers.IntegerField(source='movie.id')  # 영화 id
        class Meta:
            model = ActorCharacter
            fields = ['character_name', 'movie_title', 'id']  # 캐릭터 이름과 영화 제목, 영화 id 포함

    
    
    # 필모그래피와 댓글 역참조 필드
    filmography = ProfileMovieCardSerializer(source='movies', many=True, read_only=True)  # 영화 목록
    comments = ActorCommentSerializer(source='actor_comments', many=True, read_only=True)  # 댓글 목록
    is_liked = serializers.SerializerMethodField()  # 좋아요 여부 확인
    notable_roles = CharacterRoleSerializer(source='movie_roles', many=True, read_only=True)  # 맡았던 캐릭터 목록
    class Meta:
        model = Actor
        fields = [
            'id', 'profile_path', 'name', 'gender', 'birthdate', 'birthplace', 
            'biography', 'filmography', 'comments', 'notable_roles', 'is_liked'
        ]

    def get_is_liked(self, obj):
        """
        좋아요 여부를 역참조를 통해 확인.
        """
        request = self.context.get('request')  # 요청 객체 가져오기
        if request and request.user.is_authenticated:
            # 역참조를 통해 현재 사용자가 이 배우를 좋아요 했는지 확인
            return request.user.favorite_actors.filter(pk=obj.pk).exists()
        return False

# 감독 프로필 시리얼라이저
class DirectorDetailSerializer(serializers.ModelSerializer):
    # 영화 카드 시리얼라이저 (내부 정의)
    class ProfileMovieCardSerializer(serializers.ModelSerializer):

        class Meta:
            model = Movie
            fields = ['id', 'title', 'release_date', 'poster_path', 'normalized_popularity']
            ref_name = "DirectorProfileMovieCardSerializer"  # 고유한 ref_name 설정


    # 댓글 시리얼라이저 (내부 정의)
    class DirectorCommentSerializer(serializers.ModelSerializer):
        user = serializers.StringRelatedField()  # 댓글 작성자의 이름 표시

        class Meta:
            model = Comment
            fields = ['id', 'user', 'content', 'created_at', 'like_count', 'dislike_count']

    # 필모그래피와 댓글 역참조 필드
    filmography = ProfileMovieCardSerializer(source='movies', many=True, read_only=True)  # 영화 목록
    comments = DirectorCommentSerializer(source='director_comments', many=True, read_only=True)  # 댓글 목록
    is_liked = serializers.SerializerMethodField()  # 좋아요 여부 확인

    class Meta:
        model = Director
        fields = [
            'id', 'profile_path', 'name', 'gender', 'birthdate', 'birthplace', 
            'biography', 'filmography', 'comments', 'is_liked'
        ]

    def get_is_liked(self, obj):
        """
        좋아요 여부를 확인.
        """
        request = self.context.get('request')  # 요청 객체 가져오기
        if request and request.user.is_authenticated:
            # 역참조를 통해 현재 사용자가 이 감독을 좋아요 했는지 확인
            return request.user.favorite_directors.filter(pk=obj.pk).exists()
        return False


'''
24.11.22. 20:37 WKH
웹 서비스의 통합 검색 페이지에 Actor, Director, CustomUser를 모두 전달해서 검색 가능하게 만들기 위한 시리얼라이저
'''
class ActorSerializer(serializers.ModelSerializer):
    favorited_count = serializers.IntegerField(read_only=True)  # 사용자 수

    class Meta:
        model = Actor
        fields = ['id', 'name', 'gender', 'profile_path', 'birthdate', 'biography', 'birthplace', 'favorited_count']

class DirectorSerializer(serializers.ModelSerializer):
    favorited_count = serializers.IntegerField(read_only=True)  # 사용자 수

    class Meta:
        model = Director
        fields = ['id', 'name', 'gender', 'profile_path', 'birthdate', 'biography', 'birthplace', 'favorited_count']

class CustomUserSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)  # 팔로워 수

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'profile_image', 'bio', 'followers_count']

''''''