from rest_framework import serializers
from .models import Actor, Movie, Review
from django.shortcuts import get_object_or_404
from movies.models import Movie, Genre, Actor, Director, News, ActorCharacter
from community.models import Review, Post, Comment
from accounts.models import CustomUser, Notification
from django.db.models import Count

        
from rest_framework import serializers
from .models import Comment

'''
AHS 11-26
'''
class ReviewValidSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'movie', 'movie_title', 'title', 'content', 'rating', 'created_at']



class CommentSerializer(serializers.ModelSerializer):
    """
    댓글 Serializer
    """
    user = serializers.SerializerMethodField()  # 작성자 정보
    like_count = serializers.ReadOnlyField()  # 좋아요 수
    dislike_count = serializers.ReadOnlyField()  # 싫어요 수
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), allow_null=True)  # 부모 댓글 ID
    replies = serializers.SerializerMethodField()  # 대댓글

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "content",
            "created_at",
            "parent",        # 부모 댓글 ID
            "like_count",    # 좋아요 수
            "dislike_count", # 싫어요 수
            "post",          # 게시글
            "review",        # 리뷰
            "actor",         # 배우
            "director",      # 감독
            "movie",         # 영화
            "replies"        # 대댓글 리스트
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "like_count",
            "dislike_count",
            "post",
            "review",
            "actor",
            "director",
            "movie",
            "replies"
        ]

    def get_user(self, obj):
        """
        작성자 정보 반환
        """
        request = self.context.get("request")
        base_url = f"{request.scheme}://{request.get_host()}"
        profile_image_url = obj.user.profile_image.url if obj.user.profile_image else "/media/default_profile.png"
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "profile_image": f"{base_url}{profile_image_url}",
            "profile_url": f"/accounts/users/{obj.user.id}/"
        }

    def get_replies(self, obj):
        """
        대댓글 리스트 반환
        """
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []

    def create(self, validated_data):
        # user 및 movie를 저장 시 전달받아 사용
        user = self.context['request'].user
        movie = validated_data.pop('movie', None)
        return Comment.objects.create(user=user, movie=movie, **validated_data)


# ---------------------------------------자유게시판----------------------------------------
# 자유게시판 - 게시글 목록
class PostSerializer(serializers.ModelSerializer):
    # 작성자 정보 Serializer
    class UserSerializer(serializers.ModelSerializer):
        profile_url = serializers.SerializerMethodField()

        class Meta:
            model = CustomUser
            fields = ['id', 'username', 'profile_image', 'profile_url']

        def get_profile_url(self, obj):
            """작성자 프로필 URL 반환"""
            return f"/accounts/users/{obj.id}/liked-movies/"

    user = UserSerializer(read_only=True)  # 작성자 정보
    like_count = serializers.IntegerField(read_only=True)  # 좋아요 수
    comment_count = serializers.IntegerField(read_only=True)  # 댓글 수

    class Meta:
        model = Post
        fields = [
            "id",          # 게시글 ID
            "title",       # 게시글 제목
            "content",     # 게시글 내용
            "created_at",  # 작성일
            "user",        # 작성자 정보
            "like_count",  # 좋아요 수
            "comment_count"  # 댓글 수
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    """게시글 상세 Serializer"""
    user = serializers.SerializerMethodField()  # 작성자 정보
    like_count = serializers.IntegerField(read_only=True)  # 좋아요 수
    comment_count = serializers.IntegerField(read_only=True)  # 댓글 수
    comments = serializers.SerializerMethodField()  # 댓글 목록
    is_liked = serializers.SerializerMethodField()  # 사용자의 좋아요 여부

    def get_user(self, obj):
        """작성자 정보"""
        request = self.context.get("request")
        base_url = f"{request.scheme}://{request.get_host()}"
        profile_image_url = obj.user.profile_image.url if obj.user.profile_image else "/media/default_profile.png"
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "profile_image": f"{base_url}{profile_image_url}",  # 백엔드 URL 포함
            "profile_url": f"/accounts/users/{obj.user.id}/liked-movies/"
        }


    def get_is_liked(self, obj):
        """현재 사용자가 게시글에 좋아요를 눌렀는지 여부"""
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.liked_posts_by_users.filter(id=user.id).exists()
        return False

    def get_comments(self, obj):
        """게시글에 달린 댓글 목록"""
        comments = self.context.get("comments")  # context에서 댓글 데이터 가져오기
        return CommentSerializer(comments, many=True, context=self.context).data

    class Meta:
        model = Post
        fields = [
            "id", "title", "content", "created_at", "updated_at",
            "user", "like_count", "comment_count", "comments", "is_liked"
        ]




# ---------------------------------------리뷰게시판----------------------------------------


class ReviewSerializer(serializers.ModelSerializer):
    class UserSerializer(serializers.ModelSerializer):
        profile_url = serializers.SerializerMethodField()

        class Meta:
            model = CustomUser
            fields = ['id', 'username', 'profile_image', 'profile_url']

        def get_profile_url(self, obj):
            return f"/accounts/users/{obj.id}/liked-movies/"

    class MovieSerializer(serializers.ModelSerializer):
        movie_url = serializers.SerializerMethodField()

        def get_movie_url(self, obj):
            return f"/movies/{obj.id}/cast-and-crews/"

        def to_representation(self, instance):
            if not instance:
                return {
                    "id": None,
                    "title": "No Movie",
                    "poster_path": "/default-poster.jpg",
                    "movie_url": None
                }
            return super().to_representation(instance)

        class Meta:
            model = Movie
            fields = ['id', 'title', 'poster_path', 'movie_url']

    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)  # 영화 객체를 완전히 직렬화
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True)

    def get_like_count(self, obj):
        return obj.liked_reviews_by_users.count()

    class Meta:
        model = Review
        fields = [
            "id",
            "title",
            "content",
            "rating",
            "created_at",
            "user",
            "movie",
            "like_count",
            "comment_count",
        ]


# 리뷰게시판 - 리뷰 상세

from rest_framework import serializers
from django.db.models import Count

class ReviewDetailSerializer(serializers.ModelSerializer):
    """
    리뷰 상세 Serializer
    - 리뷰 정보, 작성자 정보, 영화 정보, 댓글 목록 포함
    """

    class MovieSerializer(serializers.ModelSerializer):
        """
        영화 정보 Serializer
        - 리뷰와 연결된 영화의 정보를 포함
        """
        movie_url = serializers.SerializerMethodField()

        def get_movie_url(self, obj):
            """영화 디테일 페이지 URL"""
            return f"http://localhost:3000/?movieId={obj.id}" if obj else None

        def to_representation(self, instance):
            """영화가 없을 경우 기본값 반환"""
            if not instance:
                return {
                    "id": None,
                    "title": "No Movie",
                    "poster_path": "/default-poster.jpg",  # 기본 포스터 경로
                    "trailer_link": None,
                    "movie_url": None
                }
            return super().to_representation(instance)

        class Meta:
            model = Movie
            fields = [
                "id",          # 영화 ID
                "title",       # 영화 제목
                "poster_path", # 영화 포스터 경로
                "trailer_link", # 영화 트레일러 링크
                "movie_url"    # 영화 디테일 페이지 URL
            ]

    class CommentSerializer(serializers.ModelSerializer):
        """
        댓글 Serializer
        - 좋아요 수와 싫어요 수를 포함
        """
        user = serializers.SerializerMethodField()  # 댓글 작성자 정보
        like_count = serializers.IntegerField(read_only=True)  # 좋아요 수
        dislike_count = serializers.IntegerField(read_only=True)  # 싫어요 수
        is_liked = serializers.SerializerMethodField()  # 사용자의 좋아요 여부
        is_disliked = serializers.SerializerMethodField()  # 사용자의 싫어요 여부

        def get_user(self, obj):
            """댓글 작성자 정보"""
            request = self.context.get("request")
            base_url = f"{request.scheme}://{request.get_host()}"
            profile_image_url = obj.user.profile_image.url if obj.user.profile_image else "/media/default_profile.png"
            return {
                "id": obj.user.id,
                "username": obj.user.username,
                "profile_image": f"{base_url}{profile_image_url}",  # 백엔드 URL 포함
                "profile_url": f"/accounts/users/{obj.user.id}/liked-movies/"
            }

        def get_is_liked(self, obj):
            """현재 사용자가 댓글을 좋아요했는지 여부"""
            user = self.context.get("request").user
            if user.is_authenticated:
                return obj.likes.filter(id=user.id).exists()
            return False

        def get_is_disliked(self, obj):
            """현재 사용자가 댓글을 싫어요했는지 여부"""
            user = self.context.get("request").user
            if user.is_authenticated:
                return obj.dislikes.filter(id=user.id).exists()
            return False

        class Meta:
            model = Comment
            fields = [
                "id",          # 댓글 ID
                "user",        # 댓글 작성자 정보
                "content",     # 댓글 내용
                "created_at",  # 댓글 작성일
                "parent",      # 부모 댓글 (대댓글의 경우)
                "like_count",  # 좋아요 수
                "dislike_count",  # 싫어요 수
                "is_liked",    # 사용자의 좋아요 여부
                "is_disliked"  # 사용자의 싫어요 여부
            ]

    user = serializers.SerializerMethodField()  # 작성자 정보
    movie = MovieSerializer(read_only=True)  # 영화 정보
    like_count = serializers.IntegerField(read_only=True)  # 좋아요 수
    is_liked = serializers.SerializerMethodField()  # 사용자의 좋아요 여부
    comments = serializers.SerializerMethodField()  # 댓글 목록

    def get_user(self, obj):
        """리뷰 작성자 정보"""
        request = self.context.get("request")
        base_url = f"{request.scheme}://{request.get_host()}"
        profile_image_url = obj.user.profile_image.url if obj.user.profile_image else "/media/default_profile.png"
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "profile_image": f"{base_url}{profile_image_url}",  # 백엔드 URL 포함
            "profile_url": f"/accounts/users/{obj.user.id}/liked-movies/"
        }

    def get_is_liked(self, obj):
        """현재 사용자가 리뷰를 좋아요했는지 여부"""
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.liked_reviews_by_users.filter(id=user.id).exists()
        return False

    def get_comments(self, obj):
        """리뷰에 달린 댓글 목록"""
        comments = obj.review_comments.annotate(
            like_count=Count('likes'),         # 좋아요 수
            dislike_count=Count('dislikes')   # 싫어요 수
        )
        return self.CommentSerializer(comments, many=True, context=self.context).data

    class Meta:
        model = Review
        fields = [
            "id",          # 리뷰 ID
            "title",       # 리뷰 제목
            "content",     # 리뷰 내용
            "rating",      # 리뷰 별점
            "created_at",  # 작성일
            "updated_at",  # 수정일
            "user",        # 작성자 정보
            "movie",       # 영화 정보
            "like_count",  # 좋아요 수
            "is_liked",    # 사용자의 좋아요 여부
            "comments"     # 댓글 목록
        ]




'''
AHS 오류 방지
'''


class ReviewCreateSerializer(serializers.ModelSerializer):
    movie = serializers.PrimaryKeyRelatedField(queryset=Movie.objects.all(), required=False)
    rating = serializers.IntegerField(required=False, default=0)  # 기본값 0 설정

    class Meta:
        model = Review
        fields = ['title', 'content', 'rating', 'movie']

    def validate(self, data):
        # 영화가 선택되었는데 평점이 없는 경우 검증 오류 방지
        if data.get('movie') and data.get('rating') is None:
            data['rating'] = 0  # 평점이 없을 경우 기본값 설정
        return data







class ReviewMovieSerializer(serializers.ModelSerializer):
    """
    리뷰 작성용 영화 Serializer
    - 필요한 필드만 포함
    """
    class Meta:
        model = Movie
        fields = ['id', 'title', 'poster_path']  # 필요한 필드만 직렬화