# accounts/views.py
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from movies.models import Actor, Movie, Genre, News
from community.models import Review, Post, Comment
from accounts.models import CustomUser, Notification
from accounts.serializers import UserProfileReadSerializer, UserProfileUpdateSerializer, DashboardSerializer, NotificationSerializer, CustomRegisterSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from accounts.serializers import MovieAdminSerializer, UserAdminSerializer, ReviewAdminSerializer
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
from utils import create_notification
from django.utils.timezone import now
from datetime import timedelta
from dj_rest_auth.registration.views import RegisterView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests

# 사용자 모델을 가져옴
User = get_user_model()

# 이메일 인증을 위한 API View
def email_verification_api_view(request, uidb64, token):
    try:
        # uidb64를 디코딩하여 사용자 ID를 얻음
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        # 사용자 ID가 유효하지 않을 경우 오류 메시지를 반환
        return Response({'success': False, 'message': 'Invalid user ID.'}, status=status.HTTP_400_BAD_REQUEST)

    # 토큰을 검증하여 사용자가 유효한지 확인
    if default_token_generator.check_token(user, token):
        # 사용자가 유효하다면 계정을 활성화하고 성공 메시지를 반환
        user.is_active = True
        user.save()
        return Response({'success': True, 'message': 'Email verified successfully.'})
    else:
        # 토큰이 유효하지 않을 경우 오류 메시지를 반환
        return Response({'success': False, 'message': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)



from rest_framework.viewsets import ModelViewSet
class UserViewSet(ModelViewSet):
    """
    UserViewSet:
    - 회원 프로필 CRUD (조회, 수정, 삭제)
    - 회원가입(create)은 별도로 처리.
    """
    queryset = CustomUser.objects.filter(deleted_at__isnull=True) #  is_active=True제외
    serializer_class = CustomRegisterSerializer

    def get_permissions(self):
        """
        회원가입(create)은 AllowAny, 나머지는 IsAuthenticated로 제한.
        """
        if self.action == 'create': # 사실상 안쓸 것
            return [AllowAny()]
        return [IsAuthenticated()] # 기존에는 회원가입에도 IsAuthenticated가 필요햇음.

    def perform_destroy(self, instance):
        """
        소프트 삭제: deleted_at에 삭제 시간을 기록.
        """
        instance.delete()

# 회원가입
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = CustomUser.objects.filter(deleted_at__isnull=True)
#     serializer_class = CustomRegisterSerializer
#     permission_classes = [IsAuthenticated]

#     def perform_destroy(self, instance):
#         instance.delete()




# 팔로우/팔로우해제 구현
class FollowViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        follower = request.user
        following_id = request.data.get('following_id')
        try:
            following = CustomUser.objects.get(id=following_id)
            if follower != following:
                if not follower.following.filter(id=following.id).exists():
                    follower.following.add(following)
                    return Response({'detail': 'Followed successfully'}, status=status.HTTP_201_CREATED)
                return Response({'detail': 'Already following this user'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        follower = request.user
        following_id = request.data.get('following_id')
        try:
            following = CustomUser.objects.get(id=following_id)
            if follower != following:
                if follower.following.filter(id=following.id).exists():
                    follower.following.remove(following)
                    return Response({'detail': 'Unfollowed successfully'}, status=status.HTTP_204_NO_CONTENT)
                return Response({'detail': 'You are not following this user'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'You cannot unfollow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)






'''
11-26 소셜로그인
'''
import json
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from django.conf import settings


@api_view(["POST"])
def google_login_view(request):
    """
    Google 소셜 로그인 처리
    """
    try:
        # 요청에서 Google ID 토큰 가져오기
        body = json.loads(request.body)
        token = body.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        # Google ID 토큰 검증
        CLIENT_ID = settings.GOOGLE_CLIENT_ID
        if not CLIENT_ID:
            return Response({"error": "GOOGLE_CLIENT_ID is not set"}, status=500)

        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        email = idinfo.get("email")
        name = idinfo.get("name", "Anonymous User")

        if not email:
            return Response({"error": "Invalid token: email not found"}, status=400)

        # 사용자 생성 또는 가져오기
        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "first_name": name},
        )

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=200,
        )

    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)




from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserProfileSerializer

'''
AHS
'''
@api_view(['GET'])
def user_profile_view(request, user_id):
    """
    사용자 프로필 데이터를 반환하는 함수형 뷰
    """
    try:
        user = CustomUser.objects.get(pk=user_id)

        # 최근 리뷰, 댓글, 게시글 계산
        recent_reviews = Review.objects.filter(user=user).order_by('-created_at')[:5]
        recent_comments = Comment.objects.filter(user=user).order_by('-created_at')[:5]
        recent_posts = Post.objects.filter(user=user).order_by('-created_at')[:5]

        # 사용자 데이터 시리얼라이징
        serializer = UserProfileSerializer(
            user,
            context={
                'request': request,
                'recent_reviews': recent_reviews,
                'recent_comments': recent_comments,
                'recent_posts': recent_posts,
            }
        )
        return Response(serializer.data)

    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)






class CommentsPagination(PageNumberPagination):
    """
    댓글 전용 페이지네이션 클래스:
    - 한 페이지당 댓글 5개 반환
    - 최대 페이지 크기 20개 제한
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20

class CustomPagination(PageNumberPagination):
    """
    커스텀 페이지네이션 클래스:
    - 한 페이지에 10개의 데이터를 반환합니다.
    - 최대 50개의 데이터를 반환하도록 제한합니다.
    """
    page_size = 10  # 기본 페이지 크기
    page_size_query_param = 'page_size'  # 클라이언트가 페이지 크기를 지정 가능
    max_page_size = 50  # 최대 페이지 크기 제한

# from django.contrib.auth import get_user_model

User = get_user_model()


# ------------------------------------------유저 프로필 페이지-----------------------------------------------------

# 1. 탭1 - 좋아요한 영화
from .serializers import UserLikedMoviesSerializer
from rest_framework.decorators import api_view, permission_classes
@swagger_auto_schema(
    method='get',
    operation_summary="유저 프로필 - 좋아하는 영화 탭",
    operation_description="""
        특정 사용자의 좋아하는 영화 목록을 반환합니다.
        - `user_id`는 조회할 사용자의 고유 ID입니다.
        - 정렬 기준: normalized_popularity(높은 순).
        - 페이지네이션 적용: 한 페이지에 반환할 영화 수를 제한합니다.
    """,
    responses={
        200: openapi.Response(
            description="좋아하는 영화 목록 반환 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "profile_image": "/path/to/profile_image.jpg",
                    "bio": "Movie enthusiast and avid watcher.",
                    "favorite_genres": ["Action", "Sci-Fi"],
                    "is_following": True,
                    "level": 15,
                    "liked_movies": {
                        "count": 10,
                        "next": "http://example.com/api/users/1/liked-movies/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "title": "Inception",
                                "poster_path": "/path/to/poster.jpg",
                                "normalized_popularity": 8.8,
                                "genres": ["Action", "Sci-Fi", "Thriller"]
                            }
                        ]
                    },
                    "followers_count": 50,
                    "following_count": 30
                }
            }
        ),
        403: openapi.Response(description="권한이 없음"),
        404: openapi.Response(description="사용자를 찾을 수 없음")
    },
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="조회할 사용자의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['GET'])
def user_liked_movies_view(request, user_id):
    """
    특정 사용자의 좋아하는 영화 목록 반환
    - normalized_popularity 기준으로 정렬
    - 페이지네이션 적용
    """
    # 1. 특정 사용자 가져오기
    user = get_object_or_404(CustomUser, id=user_id)

    # 2. 유저의 좋아하는 영화 쿼리셋
    liked_movies_queryset = user.liked_movies.order_by('-normalized_popularity')

    # 3. 페이지네이션 처리
    paginator = CommentsPagination()
    paginated_movies = paginator.paginate_queryset(liked_movies_queryset, request)

    # 4. 페이지네이션된 영화 데이터를 직렬화
    paginated_movies_data = [
        {
            'id': movie.id,
            'title': movie.title,
            'poster_path': movie.poster_path,
            'normalized_popularity': movie.normalized_popularity,
            'genres': [genre.name for genre in movie.genres.all()]
        }
        for movie in paginated_movies
    ]

    # 5. 유저 데이터 직렬화
    user_serialized_data = UserLikedMoviesSerializer(user, context={'request': request}).data

    # 6. 직렬화된 데이터에 페이지네이션된 좋아하는 영화 데이터 추가
    user_serialized_data['liked_movies'] = paginator.get_paginated_response(paginated_movies_data).data

    # 7. 최종 응답 반환
    return Response(user_serialized_data, status=status.HTTP_200_OK)


# 2. 탭2- 좋아하는 인물(배우, 감독)
from .serializers import UserLikedPeopleSerializer
@swagger_auto_schema(
    method='get',
    operation_summary="유저 프로필 - 좋아하는 배우 및 감독",
    operation_description="""
        특정 사용자가 좋아하는 배우 및 감독 목록을 반환합니다.
        - 페이지네이션이 적용됩니다.
    """,
    responses={
        200: openapi.Response(
            description="좋아하는 배우 및 감독 목록 반환 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "profile_image": None,
                    "bio": "사용자 자기소개",
                    "favorite_genres": ["Action", "Drama"],
                    "is_following": True,
                    "level": 12,
                    "favorite_actors": {
                        "count": 5,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "name": "Leonardo DiCaprio",
                                "profile_path": "/path/to/image.jpg",
                                "movies": ["Inception", "Titanic"]
                            }
                        ]
                    },
                    "favorite_directors": {
                        "count": 3,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "name": "Christopher Nolan",
                                "profile_path": "/path/to/image.jpg",
                                "movies": ["Inception", "Interstellar"]
                            }
                        ]
                    }
                }
            }
        ),
        404: openapi.Response(description="사용자를 찾을 수 없음"),
    },
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="조회할 사용자의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ]
)
@api_view(['GET'])
def user_liked_people_view(request, user_id):
    """
    특정 사용자가 좋아하는 배우 및 감독 목록 반환
    - 페이지네이션을 적용하여 반환
    """
    user = get_object_or_404(CustomUser, id=user_id)
    
    # 배우와 감독 쿼리셋
    favorite_actors = user.favorite_actors.order_by('name')
    favorite_directors = user.favorite_directors.order_by('name')

    # 페이지네이션 처리
    actor_pagination = CustomPagination()
    director_pagination = CustomPagination()

    paginated_actors = actor_pagination.paginate_queryset(favorite_actors, request)
    paginated_directors = director_pagination.paginate_queryset(favorite_directors, request)

    # 직렬화
    actor_serializer = UserLikedPeopleSerializer.ActorCardSerializer(paginated_actors, many=True)
    director_serializer = UserLikedPeopleSerializer.DirectorCardSerializer(paginated_directors, many=True)

    # 응답 데이터
    response_data = {
        "id": user.id,
        "profile_image": user.profile_image,
        "bio": user.bio,
        "favorite_genres": [genre.name for genre in user.favorite_genres.all()],
        "is_following": user.followers.filter(id=request.user.id).exists(),
        "level": user.liked_movies.count() + user.watched_movies.count(),
        "favorite_actors": actor_pagination.get_paginated_response(actor_serializer.data).data,
        "favorite_directors": director_pagination.get_paginated_response(director_serializer.data).data,
    }

    return Response(response_data, status=status.HTTP_200_OK)



# 3. 탭3- 활동(리뷰, 댓글, 게시글)
from .serializers import UserProfileActivitySerializer
@swagger_auto_schema(
    method='get',
    operation_summary="유저 프로필 - Activity 탭",
    operation_description="유저 프로필의 Activity 탭 데이터를 반환합니다.",
    responses={
        200: openapi.Response(
            description="성공적으로 데이터를 반환.",
            examples={
                "application/json": {
                    "id": 1,
                    "profile_image": "/path/to/profile_image.jpg",
                    "bio": "Avid movie enthusiast.",
                    "favorite_genres": ["Action", "Drama"],
                    "is_following": True,
                    "level": 25,
                    "following_count": 30,
                    "followers_count": 50,
                    "recent_reviews": {
                        "count": 5,
                        "next": "http://example.com/api/users/1/reviews/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "movie_title": "Inception",
                                "movie_id": 1,
                                "content": "Amazing movie!",
                                "rating": 5,
                                "created_at": "2024-11-19T12:00:00Z",
                                "updated_at": "2024-11-19T13:00:00Z"
                            }
                        ]
                    },
                    "recent_comments": {
                        "count": 5,
                        "next": "http://example.com/api/users/1/comments/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "object_id": 2,
                                "content": "Great post!",
                                "like_count": 10,
                                "dislike_count": 0,
                                "created_at": "2024-11-19T12:00:00Z"
                            }
                        ]
                    },
                    "recent_posts": {
                        "count": 5,
                        "next": "http://example.com/api/users/1/posts/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "title": "My First Post",
                                "content": "This is the content of the post.",
                                "created_at": "2024-11-19T12:00:00Z",
                                "updated_at": "2024-11-19T13:00:00Z"
                            }
                        ]
                    }
                }
            }
        ),
        404: openapi.Response(description="유저를 찾을 수 없음."),
    }
)
@api_view(['GET'])
def user_profile_activity_view(request, user_id):
    """
    User Profile - Activity 탭 데이터 조회 뷰
    - 리뷰, 댓글, 게시글 데이터를 페이지네이션하여 반환.
    """
    user = get_object_or_404(User, pk=user_id)

    # 페이지네이션 유틸리티 함수 정의
    def paginate_data(queryset, request, serializer_class):
        paginator = CommentsPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = serializer_class(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data).data

    # 쿼리셋 정의 및 페이지네이션 처리
    recent_reviews = Review.objects.filter(user=user).order_by('-created_at')
    recent_comments = Comment.objects.filter(user=user).order_by('-created_at')
    recent_posts = Post.objects.filter(user=user).order_by('-created_at')

    paginated_reviews = paginate_data(recent_reviews, request, UserProfileActivitySerializer.RecentReviewSerializer)
    paginated_comments = paginate_data(recent_comments, request, UserProfileActivitySerializer.RecentCommentSerializer)
    paginated_posts = paginate_data(recent_posts, request, UserProfileActivitySerializer.RecentPostSerializer)

    # 유저 데이터 직렬화
    serializer = UserProfileActivitySerializer(user, context={'request': request})
    serialized_data = serializer.data

    # 페이지네이션된 데이터 추가
    serialized_data['recent_reviews'] = paginated_reviews
    serialized_data['recent_comments'] = paginated_comments
    serialized_data['recent_posts'] = paginated_posts

    return Response(serialized_data, status=status.HTTP_200_OK)



# 4-1. 탭4- 소셜(팔로잉, 팔로워, 맞팔로우) - 조회
from .serializers import UserSocialTabSerializer
@swagger_auto_schema(
    method='get',
    operation_summary="유저 프로필 - 팔로잉 및 팔로워",
    operation_description="팔로워, 팔로잉, 맞팔로우 데이터를 페이지네이션 처리하여 반환합니다.",
    responses={
        200: openapi.Response(
            description="Social 탭 데이터 반환 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "profile_image": "/path/to/profile.jpg",
                    "bio": "Movie enthusiast.",
                    "favorite_genres": ["Action", "Drama"],
                    "is_following": True,
                    "level": 25,
                    "followers": {
                        "count": 5,
                        "next": "http://example.com/api/users/1/followers/?page=2",
                        "previous": None,
                        "results": [
                            {"id": 2, "username": "user456", "profile_image": "/path/to/image.jpg", "bio": "Another user"}
                        ]
                    },
                    "following": {
                        "count": 3,
                        "next": None,
                        "previous": None,
                        "results": [
                            {"id": 3, "username": "user789", "profile_image": "/path/to/image.jpg", "bio": "Following user"}
                        ]
                    },
                    "mutual_followers": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {"id": 4, "username": "user123", "profile_image": "/path/to/image.jpg", "bio": "Mutual follower"}
                        ]
                    }
                }
            }
        ),
        404: openapi.Response(description="유저를 찾을 수 없음."),
    }
)
@api_view(['GET'])
def user_social_tab_view(request, user_id):
    """
    User Profile - Social 탭 데이터 조회
    - 팔로워, 팔로잉, 맞팔로우 데이터를 페이지네이션 처리하여 반환합니다.
    """
    user = get_object_or_404(CustomUser, pk=user_id)

    # 페이지네이션 유틸리티 함수 정의
    def paginate_users(queryset, request):
        paginator = CommentsPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = UserSocialTabSerializer.SimpleUserCardSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data).data

    # 팔로잉, 팔로워, 맞팔로우 데이터 가져오기
    following_users = user.following.all()
    follower_users = user.followers.all()
    mutual_follow_users = following_users & follower_users

    # 페이지네이션 처리
    paginated_following = paginate_users(following_users, request)
    paginated_followers = paginate_users(follower_users, request)
    paginated_mutual_followers = paginate_users(mutual_follow_users, request)

    # 시리얼라이저 데이터 직렬화
    serializer = UserSocialTabSerializer(user, context={'request': request})
    serialized_data = serializer.data

    # 페이지네이션된 데이터 추가
    serialized_data['following'] = paginated_following
    serialized_data['followers'] = paginated_followers
    serialized_data['mutual_followers'] = paginated_mutual_followers

    return Response(serialized_data, status=status.HTTP_200_OK)


# 4-2. 탭4- 소셜(팔로잉, 팔로워, 맞팔로우) - 삭제

@api_view(['DELETE'])
def user_social_tab_delete_view(request, user_id):
    """
    User Profile - Social 탭 데이터 삭제
    """
    user = get_object_or_404(CustomUser, pk=user_id)
    action = request.query_params.get('action')
    target_id = request.query_params.get('target_user_id')  # 이름을 일치시킴

    if not action or not target_id:
        return Response({'error': "action과 target_user_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    target_user = get_object_or_404(CustomUser, pk=target_id)

    if action == 'follower':
        # 팔로워 삭제
        user.followers.remove(target_user)
    elif action == 'following':
        # 팔로잉 삭제
        user.following.remove(target_user)
    else:
        return Response({'error': "action 값이 잘못되었습니다. ('follower' 또는 'following')"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': "성공적으로 삭제되었습니다."}, status=status.HTTP_200_OK)

# 5. 팔로잉/언팔로우 토글
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
@swagger_auto_schema(
    method='post',
    operation_summary="팔로우/언팔로우 토글",
    operation_description="특정 사용자를 팔로우하거나 언팔로우합니다.",
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="팔로우/언팔로우할 유저의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="성공적으로 팔로잉 상태 변경",
            examples={
                "application/json": {
                    "message": "팔로우 완료",
                    "is_following": True
                }
            }
        ),
        400: openapi.Response(description="유효하지 않은 요청"),
        404: openapi.Response(description="대상 사용자를 찾을 수 없음")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_follow_view(request, user_id):
    """
    팔로우/언팔로우 토글 API
    - 요청한 사용자가 특정 유저를 팔로우하거나 언팔로우합니다.
    """
    # 대상 사용자 조회
    target_user = get_object_or_404(CustomUser, id=user_id)

    # 자기 자신을 팔로우하려는 경우 처리
    if target_user == request.user:
        return Response(
            {"error": "자기 자신을 팔로우할 수 없습니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 팔로우 상태 확인 및 처리
    if request.user.following.filter(id=target_user.id).exists():
        # 이미 팔로잉 상태 -> 언팔로우
        request.user.following.remove(target_user)
        return Response(
            {"message": "언팔로우 완료", "is_following": False},
            status=status.HTTP_200_OK
        )
    else:
        # 팔로우 추가
        request.user.following.add(target_user)

        # 팔로우 알림 생성
        create_notification(
            user=target_user,
            content=f"'{request.user.username}'님이 당신을 팔로우하기 시작했습니다.",
            type='follow',
        )

        return Response(
            {"message": "팔로우 완료", "is_following": True},
            status=status.HTTP_200_OK
        )



# ------------------------------------------유저 프로필 수정 페이지-----------------------------------------------------

# ------------------------------------------
# 유저 프로필 수정 페이지 조회 (GET 요청)
# ------------------------------------------
'''
AHS 유저 프로필 권한인증 삭제
'''
@swagger_auto_schema(
    method='get',
    operation_summary="유저 프로필 수정 페이지 조회",
    operation_description="특정 사용자의 프로필 정보를 조회합니다. 현재 로그인한 사용자만 자신의 프로필 정보를 조회할 수 있습니다.",
    responses={
        200: openapi.Response(description="프로필 조회 성공", schema=UserProfileReadSerializer),
        403: openapi.Response(description="인증이 필요합니다."),
        404: openapi.Response(description="사용자를 찾을 수 없습니다."),
    }
)
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def edit_user_profile_view(request):
    """
    유저 프로필 수정 페이지 조회:
    - GET 요청: 특정 사용자의 프로필 정보를 반환
    """
    user = request.user
    serializer = UserProfileReadSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------------------------------
# 유저 프로필 수정 페이지 저장 (PUT/PATCH 요청)
# ------------------------------------------
@swagger_auto_schema(
    method='patch',
    operation_summary="유저 프로필 수정",
    operation_description="현재 로그인한 사용자가 자신의 프로필 정보를 수정합니다.",
    request_body=UserProfileUpdateSerializer,
    responses={
        200: openapi.Response(
            description="프로필 수정 성공",
            examples={
                "application/json": {
                    "message": "프로필이 성공적으로 저장되었습니다.",
                    "updated_data": {
                        "profile_image": "/path/to/image.jpg",
                        "bio": "새로운 자기소개입니다.",
                        "favorite_genres_ids": [1, 2, 3],
                    }
                }
            }
        ),
        400: openapi.Response(
            description="유효하지 않은 데이터.",
            examples={
                "application/json": {
                    "message": "프로필 저장 중 오류가 발생했습니다.",
                    "errors": {"bio": ["이 필드는 필수입니다."]}
                }
            }
        ),
        403: openapi.Response(
            description="권한이 없습니다.",
            examples={
                "application/json": {"error": "권한이 없습니다."}
            }
        ),
        404: openapi.Response(
            description="사용자를 찾을 수 없습니다.",
            examples={
                "application/json": {"error": "사용자를 찾을 수 없습니다."}
            }
        ),
    },
    manual_parameters=[
        openapi.Parameter(
            "user_id",
            openapi.IN_PATH,
            description="수정할 사용자의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
def save_user_profile_and_redirect(request):
    """
    유저 프로필 수정:
    - PATCH 요청: 현재 로그인한 사용자의 프로필 정보를 업데이트
    """
    user = request.user
    serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "프로필이 성공적으로 저장되었습니다.",
            "updated_data": serializer.data,
        }, status=status.HTTP_200_OK)
    
    return Response({
        "message": "프로필 저장 중 오류가 발생했습니다.",
        "errors": serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


    
# ------------------------------------------------알림 목록-----------------------------------------------------
from .serializers import NotificationSerializer
from django.db.models import Q

# class NotificationPagination(PageNumberPagination):
#     """
#     알림 페이지네이션:
#     - 한 페이지당 10개의 알림 반환
#     - 최대 50개의 알림 반환
#     """
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 50
    

# 알림목록 조회 뷰
@swagger_auto_schema(
    method='get',
    operation_summary="알림 목록 조회",
    operation_description="""
        사용자의 알림 목록을 최신순으로 조회합니다.
        - 읽음 상태(`is_read`), 알림 타입(`type`) 필터링 가능
        - 7일 이내의 알림만 반환
    """,
    manual_parameters=[
        openapi.Parameter(
            'is_read',
            openapi.IN_QUERY,
            description="읽음 상태 필터링. 'true' 또는 'false' 값 허용",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'type',
            openapi.IN_QUERY,
            description="알림 타입 필터링. 'comment', 'like', 'follow', 'review' 값 중 하나",
            type=openapi.TYPE_STRING,
            required=False
        )
    ],
    responses={
        200: openapi.Response(
            description="알림 목록 조회 성공",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "content": "A님이 게시글에 댓글을 작성했습니다.",
                        "is_read": False,
                        "created_at": "2024-11-20T12:00:00Z",
                        "type": "comment",
                        "link": "/post/123/"
                    },
                    {
                        "id": 2,
                        "content": "B님이 당신을 팔로우하기 시작했습니다.",
                        "is_read": True,
                        "created_at": "2024-11-19T15:30:00Z",
                        "type": "follow",
                        "link": "/profile/456/"
                    }
                ]
            }
        ),
        403: openapi.Response(description="인증이 필요합니다."),
    }
)
# @permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_notifications_view(request):
    """
    알림 조회 API
    - 최신순 정렬
    - 읽음 유무 및 알림 타입별 필터링 지원
    - 7일 이내의 알림만 반환
    - 인증 데코레이터로 통일
    """
    # if not request.user.is_authenticated:
    #     return Response({"error": "인증이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

    # 7일 이내 알림 필터
    seven_days_ago = now() - timedelta(days=7)

    # 필터링: 읽음 상태 및 알림 타입
    is_read = request.query_params.get('is_read')
    notif_type = request.query_params.get('type')

    filters = Q(user=request.user, created_at__gte=seven_days_ago)
    if is_read is not None:
        filters &= Q(is_read=(is_read.lower() == 'true'))
    if notif_type:
        filters &= Q(type=notif_type)

    # 필터링된 알림 쿼리셋
    notifications = Notification.objects.filter(filters).order_by('-created_at')

    # 데이터 직렬화
    serializer = NotificationSerializer(notifications, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# 모두 읽음 처리
@swagger_auto_schema(
    method='post',
    operation_summary="모든 알림 읽음 처리",
    operation_description="사용자의 모든 알림을 읽음 상태로 업데이트합니다.",
    responses={
        200: openapi.Response(description="성공적으로 모든 알림을 읽음 처리했습니다."),
        403: openapi.Response(description="인증이 필요합니다.")
    }
)
@api_view(['POST'])
def mark_all_as_read(request):
    """
    모든 알림 읽음 처리
    """
    if not request.user.is_authenticated:
        return Response({"error": "인증이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"message": "모든 알림을 읽음 처리했습니다."}, status=status.HTTP_200_OK)



# 모두 안읽음 처리
@swagger_auto_schema(
    method='post',
    operation_summary="모든 알림 안읽음 처리",
    operation_description="사용자의 모든 알림을 안읽음 상태로 업데이트합니다.",
    responses={
        200: openapi.Response(description="성공적으로 모든 알림을 안읽음 처리했습니다."),
        403: openapi.Response(description="인증이 필요합니다.")
    }
)
@api_view(['POST'])
def mark_all_as_unread(request):
    """
    모든 알림 안읽음 처리
    """
    if not request.user.is_authenticated:
        return Response({"error": "인증이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

    Notification.objects.filter(user=request.user, is_read=True).update(is_read=False)
    return Response({"message": "모든 알림을 안읽음 처리했습니다."}, status=status.HTTP_200_OK)

'''
24.11.23. 03:19 AHS
알림읽음 토글 기능 개선.
정상 작동 확인
'''
# 알림 읽음/안읽음 토글
@swagger_auto_schema(
    method='post',
    operation_summary="개별 알림 읽음/안읽음 토글",
    operation_description="특정 알림의 읽음 상태를 토글합니다.",
    manual_parameters=[
        openapi.Parameter(
            'notification_id',
            openapi.IN_PATH,
            description="읽음/안읽음 상태를 토글할 알림의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="성공적으로 알림 읽음 상태가 토글되었습니다.",
            examples={
                "application/json": {
                    "message": "알림 읽음 상태가 변경되었습니다.",
                    "is_read": True
                }
            }
        ),
        403: openapi.Response(description="인증이 필요합니다."),
        404: openapi.Response(description="알림을 찾을 수 없습니다.")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_notification_read_status(request, notification_id):
    """
    알림 읽음/안읽음 토글 API
    - 특정 알림의 읽음 상태를 변경합니다.
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        return Response({"error": "해당 알림을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 현재 읽음 상태를 반전
    notification.is_read = not notification.is_read
    notification.save()

    return Response({
        "success": True,
        "message": "알림 읽음 상태가 변경되었습니다.",
        "data": {
            "is_read": notification.is_read
        }
    }, status=status.HTTP_200_OK)



# 전체 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="모든 알림 삭제",
    operation_description="사용자의 모든 알림을 삭제합니다.",
    responses={
        200: openapi.Response(description="성공적으로 모든 알림을 삭제했습니다."),
        403: openapi.Response(description="인증이 필요합니다.")
    }
)
@api_view(['DELETE'])
def delete_all_notifications(request):
    """
    모든 알림 삭제
    """
    if not request.user.is_authenticated:
        return Response({"error": "인증이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

    Notification.objects.filter(user=request.user).delete()
    return Response({"message": "모든 알림이 삭제되었습니다."}, status=status.HTTP_200_OK)



# 개별 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="개별 알림 삭제",
    operation_description="특정 알림을 삭제합니다.",
    manual_parameters=[
        openapi.Parameter(
            'notification_id',
            openapi.IN_PATH,
            description="삭제할 알림의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(description="성공적으로 알림을 삭제했습니다."),
        403: openapi.Response(description="인증이 필요합니다."),
        404: openapi.Response(description="알림을 찾을 수 없습니다.")
    }
)
@api_view(['DELETE'])
def delete_notification(request, notification_id):
    """
    개별 알림 삭제
    """
    if not request.user.is_authenticated:
        return Response({"error": "인증이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return Response({"message": "알림이 삭제되었습니다."}, status=status.HTTP_200_OK)



# ---------------------------------------------관리자 대시보드----------------------------------------------------------

# 관리자 대시보드 - 월 별 성장 그래프 대시보드
@swagger_auto_schema(
    method='get',
    operation_summary="관리자 대시보드 - 월별 사용자 성장 데이터",
    operation_description="""
        최근 1년간 월별 사용자 증가 데이터를 반환합니다.
        - 사용자 증가 데이터는 '년-월' 형식으로 정리됩니다.
        - 장르별 영화 데이터도 함께 반환합니다.
    """,
    responses={
        200: openapi.Response(
            description="성공적으로 대시보드 데이터를 반환",
            examples={
                "application/json": {
                    "user_growth": [
                        {"month": "2023-01", "user_count": 50},
                        {"month": "2023-02", "user_count": 75}
                    ],
                    "movies_by_genre": [
                        {"genre": "Action", "movie_count": 120},
                        {"genre": "Drama", "movie_count": 95}
                    ]
                }
            }
        )
    }
)
@api_view(['GET'])
def admin_dashboard_view(request):
    """
    관리자 대시보드 데이터를 제공하는 API:
    - 월별 사용자 증가 데이터를 반환합니다.
    - 장르별 영화 데이터를 포함합니다.
    """
    serializer = DashboardSerializer()
    data = serializer.to_representation(None)  # 대시보드 데이터 반환
    return Response(data, status=status.HTTP_200_OK)





# 관리자 대시보드 - 영화 목록 조회 및 제목 검색

# 영화 목록용 페이지네이션 클래스
class MoviePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

@swagger_auto_schema(
    method='get',
    operation_summary="관리자 대시보드 - 영화 목록 조회 및 검색",
    operation_description="""
        영화 목록을 반환하거나 영화 제목으로 검색합니다.
        - `title` 파라미터를 통해 제목 검색이 가능합니다.
        - `sort` 파라미터를 통해 정렬 기준을 동적으로 지정할 수 있습니다.
        - 정렬 가능한 필드: `title`, `release_date`, `normalized_popularity`
    """,
    manual_parameters=[
        openapi.Parameter(
            'title', openapi.IN_QUERY, description="영화 제목 검색어", type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'sort', openapi.IN_QUERY, description="정렬 기준 (title, release_date, normalized_popularity)", type=openapi.TYPE_STRING
        )
    ],
    responses={
        200: openapi.Response(
            description="영화 목록 반환 성공",
            examples={
                "application/json": {
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {"id": 1, "title": "Inception", "release_date": "2010-07-16", "poster_path": "/path.jpg"},
                        {"id": 2, "title": "Interstellar", "release_date": "2014-11-07", "poster_path": "/path.jpg"}
                    ]
                }
            }
        )
    }
)
@api_view(['GET'])
def admin_movie_list_view(request):
    """
    관리자 대시보드 - 영화 목록 조회 및 검색 API:
    - 영화 목록을 반환합니다.
    - `title` 쿼리 파라미터를 통해 제목으로 검색할 수 있습니다.
    - `sort` 쿼리 파라미터를 통해 정렬 기준을 동적으로 지정할 수 있습니다.
    """
    query = request.query_params.get('title', None)  # 검색어
    sort_by = request.query_params.get('sort', 'title')  # 기본 정렬 기준: 제목순

    # 허용된 정렬 필드
    allowed_sort_fields = ['title', 'release_date', 'normalized_popularity']
    if sort_by not in allowed_sort_fields:
        return Response(
            {"error": f"Invalid sort field. Allowed fields are {', '.join(allowed_sort_fields)}."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 제목 검색 및 정렬 적용
    movies = Movie.objects.filter(title__icontains=query).order_by(sort_by) if query else Movie.objects.all().order_by(sort_by)

    # 페이지네이션 처리
    paginator = MoviePagination()
    paginated_movies = paginator.paginate_queryset(movies, request)
    serializer = MovieAdminSerializer(paginated_movies, many=True)

    return paginator.get_paginated_response(serializer.data)


# 관리자 대시보드 - 사용자 목록 조회 및 사용자명 검색

@swagger_auto_schema(
    method='get',
    operation_summary="관리자 대시보드 - 사용자 목록 조회 및 검색",
    operation_description="""
        사용자 목록을 반환하거나 사용자명 또는 이메일로 검색합니다.
        - `username` 파라미터를 통해 사용자명을 검색할 수 있습니다.
        - `email` 파라미터를 통해 이메일로 검색할 수 있습니다.
        - 결과는 사용자명순으로 정렬됩니다.
        - 페이지네이션 지원 (기본 10개, 최대 50개)
    """,
    manual_parameters=[
        openapi.Parameter(
            'username', openapi.IN_QUERY, description="사용자명 검색어", type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'email', openapi.IN_QUERY, description="이메일 검색어", type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY, description="페이지 번호", type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY, description="한 페이지당 데이터 개수 (기본값 10, 최대 50)", type=openapi.TYPE_INTEGER
        )
    ],
    responses={
        200: openapi.Response(
            description="사용자 목록 반환 성공",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 사용자 수"),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, description="다음 페이지 URL"),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, description="이전 페이지 URL"),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="사용자 ID"),
                                'username': openapi.Schema(type=openapi.TYPE_STRING, description="사용자명"),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, description="이메일"),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="계정 생성 날짜"),
                            }
                        )
                    )
                }
            )
        )
    }
)
@api_view(['GET'])
def admin_user_list_view(request):
    """
    관리자 대시보드 - 사용자 목록 조회 및 검색 API:
    - 사용자 목록을 반환합니다.
    - `username` 또는 `email` 쿼리 파라미터로 검색할 수 있습니다.
    """
    username_query = request.query_params.get('username', None)
    email_query = request.query_params.get('email', None)

    if username_query:
        users = CustomUser.objects.filter(username__icontains=username_query).order_by('username')
    elif email_query:
        users = CustomUser.objects.filter(email__icontains=email_query).order_by('username')
    else:
        users = CustomUser.objects.all().order_by('username')

    # 페이지네이션 처리
    paginator = PageNumberPagination()
    paginator.page_size = 10  # 기본 페이지 크기
    paginator.max_page_size = 50  # 최대 페이지 크기
    paginated_users = paginator.paginate_queryset(users, request)

    serializer = UserAdminSerializer(paginated_users, many=True)
    return paginator.get_paginated_response(serializer.data)



# 관리자 대시보드 - 리뷰 목록 조회 및 리뷰명 검색
@swagger_auto_schema(
    method='get',
    operation_summary="관리자 대시보드 - 리뷰 목록 조회 및 검색",
    operation_description="""
        리뷰 목록을 최신순으로 조회하거나, 특정 영화 제목 또는 사용자명을 기반으로 필터링합니다.
        - 최신순 정렬
        - 영화 제목(`movie_title`) 또는 사용자명(`username`)으로 필터링 가능
        - 페이지네이션 지원 (기본 10개, 최대 50개)
    """,
    manual_parameters=[
        openapi.Parameter(
            'movie_title', openapi.IN_QUERY, description="검색할 영화 제목", type=openapi.TYPE_STRING, required=False
        ),
        openapi.Parameter(
            'username', openapi.IN_QUERY, description="검색할 사용자명", type=openapi.TYPE_STRING, required=False
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY, description="페이지 번호", type=openapi.TYPE_INTEGER, required=False
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY, description="한 페이지당 데이터 개수 (기본값 10, 최대 50)", type=openapi.TYPE_INTEGER, required=False
        )
    ],
    responses={
        200: openapi.Response(
            description="리뷰 목록 조회 성공",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 리뷰 수"),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, description="다음 페이지 URL"),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, description="이전 페이지 URL"),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="리뷰 ID"),
                                'movie_title': openapi.Schema(type=openapi.TYPE_STRING, description="리뷰 대상 영화 제목"),
                                'user_username': openapi.Schema(type=openapi.TYPE_STRING, description="리뷰 작성자"),
                                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description="별점"),
                                'content': openapi.Schema(type=openapi.TYPE_STRING, description="리뷰 내용"),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="리뷰 생성 날짜"),
                            }
                        )
                    )
                }
            )
        ),
        400: openapi.Response(description="잘못된 요청"),
    }
)
@api_view(['GET'])
def admin_review_list_view(request):
    """
    리뷰 목록을 조회하거나 영화 제목 또는 사용자명을 검색하는 API.
    - 최신순 정렬
    - 영화 제목 또는 사용자명으로 필터링 가능
    - 페이지네이션 지원
    """
    # 쿼리 파라미터
    movie_query = request.query_params.get('movie_title', None)  # 영화 제목 검색
    user_query = request.query_params.get('username', None)     # 사용자명 검색

    # 검색 조건 처리
    if movie_query:
        # 특정 영화에 작성된 리뷰 필터링
        reviews = Review.objects.filter(movie__title__icontains=movie_query).order_by('-created_at')
    elif user_query:
        # 특정 사용자가 작성한 리뷰 필터링
        reviews = Review.objects.filter(user__username__icontains=user_query).order_by('-created_at')
    else:
        # 검색 조건이 없는 경우: 모든 리뷰를 최신순으로 반환
        reviews = Review.objects.all().order_by('-created_at')

    # 페이지네이션 처리
    paginator = PageNumberPagination()
    paginator.page_size = 10  # 기본 페이지 크기 설정
    paginated_reviews = paginator.paginate_queryset(reviews, request)

    # 직렬화 및 응답 반환
    serializer = ReviewAdminSerializer(paginated_reviews, many=True)
    return paginator.get_paginated_response(serializer.data)

# 주석 설명:
# 1. movie_title 파라미터: 특정 영화에 작성된 리뷰를 검색
#    - 예: /admin/reviews/?movie_title=Inception
#    - 결과: 영화 "Inception"에 작성된 모든 리뷰 반환
# 
# 2. username 파라미터: 특정 사용자가 작성한 리뷰를 검색
#    - 예: /admin/reviews/?username=user1
#    - 결과: 사용자 "user1"이 작성한 모든 리뷰 반환
# 
# 3. 페이지네이션:
#    - 한 페이지에 10개의 리뷰 반환
#    - 예: /admin/reviews/?page=2
#    - 결과: 두 번째 페이지의 리뷰 반환


'''
AHS
'''
# 관리자 삭제 기능

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound

# 영화 삭제 뷰
@csrf_exempt
def admin_movie_delete_view(request):
    if request.method == "DELETE":
        movie_id = request.GET.get('id')
        if not movie_id:
            return HttpResponseBadRequest("Missing 'id' parameter.")
        movie = get_object_or_404(Movie, id=movie_id)
        movie.delete()
        return JsonResponse({'message': f'Movie with id {movie_id} deleted successfully.'})
    return HttpResponseBadRequest("Only DELETE method is allowed.")

# 사용자 삭제 뷰
from django.utils import timezone

@csrf_exempt
def admin_user_delete_view(request):
    """
    사용자 소프트 삭제 뷰:
    deleted_at 필드를 현재 시간으로 설정하여 소프트 삭제 처리.
    """
    if request.method == "DELETE":
        user_id = request.GET.get('id')
        if not user_id:
            return HttpResponseBadRequest("Missing 'id' parameter.")
        
        # 사용자 객체 가져오기
        user = get_object_or_404(User, id=user_id)

        # 이미 소프트 삭제된 사용자 처리
        if user.deleted_at:
            return JsonResponse({'message': f'User with id {user_id} is already deleted.'}, status=400)

        # 소프트 삭제 처리
        user.delete()

        return JsonResponse({'message': f'User with id {user_id} has been soft deleted successfully.'})
    
    return HttpResponseBadRequest("Only DELETE method is allowed.")




# 소프트삭제 되살리기 뷰
@csrf_exempt
def admin_user_restore_view(request):
    """
    관리자 대시보드 - 사용자 복원 API:
    - 소프트 삭제된 사용자의 deleted_at 필드를 None으로 설정하여 복원합니다.
    """
    if request.method == "POST":
        user_id = request.GET.get('id')
        if not user_id:
            return HttpResponseBadRequest("Missing 'id' parameter.")
        
        # 소프트 삭제된 사용자 가져오기
        user = get_object_or_404(User, id=user_id, deleted_at__isnull=False)

        # 복원 처리 (deleted_at 필드를 None으로 설정)
        user.deleted_at = None
        user.save()

        return JsonResponse({'message': f'User with id {user_id} has been restored successfully.'})
    
    return HttpResponseBadRequest("Only POST method is allowed.")














# 리뷰 삭제 뷰
@csrf_exempt
def admin_review_delete_view(request):
    if request.method == "DELETE":
        review_id = request.GET.get('id')
        if not review_id:
            return HttpResponseBadRequest("Missing 'id' parameter.")
        review = get_object_or_404(Review, id=review_id)
        review.delete()
        return JsonResponse({'message': f'Review with id {review_id} deleted successfully.'})
    return HttpResponseBadRequest("Only DELETE method is allowed.")








