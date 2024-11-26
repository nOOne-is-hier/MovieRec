# movies/views.py

import requests
from django.http import JsonResponse
from movies.models import Movie, Actor, Director, Genre
from datetime import datetime
import time
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from movies.models import Actor, Movie, Genre, News
from community.models import Review, Post, Comment
from accounts.models import CustomUser, Notification
from django.contrib.auth import get_user_model
from movies.serializers import MovieCardSerializer
# from movies.serializers import MovieDetailSerializer
from rest_framework.permissions import IsAuthenticated
from movies.serializers import ActorDetailSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from utils import create_notification
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from accounts.models import CustomUser
from movies.models import Actor, Director
from .serializers import ActorSerializer, DirectorSerializer, CustomUserSerializer, UnifiedMovieDetailSerializer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Sentence Transformers 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')
User = get_user_model()

'''# ㅍ페이지네이터
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
    max_page_size = 50  # 최대 페이지 크기 제한'''


# 영화 리스트 뷰 함수 (영화 검색 결과도 동일한 것 사용)
@swagger_auto_schema(
    method='get',
    operation_summary="영화 목록 조회 (페이지네이션 적용)",
    operation_description="영화 목록 데이터를 반환합니다. 필터링 및 검색은 프론트엔드에서 처리됩니다.",
    responses={
        200: openapi.Response(
            description="성공적으로 영화 목록을 조회함",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="총 데이터 개수"),
                    "next": openapi.Schema(type=openapi.TYPE_STRING, description="다음 페이지 URL"),
                    "previous": openapi.Schema(type=openapi.TYPE_STRING, description="이전 페이지 URL"),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="영화 ID"),
                                "title": openapi.Schema(type=openapi.TYPE_STRING, description="영화 제목"),
                                "poster_path": openapi.Schema(type=openapi.TYPE_STRING, description="포스터 이미지 경로"),
                                "release_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="개봉일"),
                                "popularity": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="영화의 인기 점수"),
                                "normalized_popularity": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="정규화된 평점"),
                                "genres": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING, description="장르 이름")
                                ),
                            }
                        )
                    ),
                },
            )
        ),
    }
)
@api_view(['GET'])
def movie_list_view(request):
    """
    영화 목록 조회 API
    - 기본 정렬 기준: normalized_popularity 내림차순
    - 클라이언트가 다른 정렬 기준을 요청하면 이를 적용합니다.
    """
    # 기본 정렬 기준 설정: normalized_popularity 내림차순
    default_ordering = '-normalized_popularity'

    # 클라이언트 요청에서 정렬 기준 가져오기 (없으면 기본값 사용)
    ordering = request.query_params.get('ordering', default_ordering)

    # 정렬된 영화 데이터 가져오기
    movies = Movie.objects.all().order_by(ordering)

    # 페이지네이터 생성 및 적용
    # paginator = CustomPagination()
    # paginated_movies = paginator.paginate_queryset(movies, request)

    # 데이터 직렬화
    serializer = MovieCardSerializer(movies, many=True)

    # 페이지네이션 응답 반환
    return Response(serializer.data)

# ----------------------------------------영화 디테일 통합 -------------------------------------    


@swagger_auto_schema(
    method='get',
    operation_summary="영화 세부 정보 조회",
    operation_description="""
        영화의 세부 정보를 반환합니다.
        - Cast & Crews (배우 및 감독)
        - 영화의 트레일러 링크
        - 관련 영화
        - 리뷰
        - 뉴스
        - 댓글
    """,
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="조회할 영화의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(description="성공적으로 영화 데이터를 반환"),
        404: openapi.Response(description="해당 영화를 찾을 수 없음")
    }
)
@api_view(['GET'])
def unified_movie_detail_view(request, movie_id):
    """
    영화의 세부 정보를 반환하는 단일 API 엔드포인트.

    - Cast & Crews 정보 (배우 및 감독)
    - 영화 트레일러 링크
    - 관련 영화
    - 뉴스 및 댓글
    - 영화 리뷰
    """
    # 영화 객체 가져오기
    movie = get_object_or_404(Movie, pk=movie_id)

    # 기본 직렬화 데이터
    serializer = UnifiedMovieDetailSerializer(movie, context={'request': request})
    serialized_data = serializer.data

    # 관련 영화 데이터 추가
    related_movies = Movie.objects.filter(
        genres__in=movie.genres.all()
    ).exclude(id=movie.id).distinct().order_by('-normalized_popularity')[:8]
    serialized_data['related_movies'] = [
        {
            'id': rel_movie.id,
            'title': rel_movie.title,
            'poster_path': rel_movie.poster_path,
            'normalized_popularity': rel_movie.normalized_popularity,
            'genres': [genre.name for genre in rel_movie.genres.all()],
        }
        for rel_movie in related_movies
    ]

    # 리뷰 데이터 추가
    reviews_queryset = movie.reviews.all().order_by('-rating')
    serialized_data['reviews'] = [
        {
            "id": review.id,
            "rating": review.rating,
            "content": review.content,
            "user": review.user.username,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
        }
        for review in reviews_queryset
    ]

    # 댓글 데이터 추가 (부모 댓글만 포함)
    parent_comments = movie.movie_comments.filter(parent=None).order_by('-created_at')
    comments_data = CommentSerializer(parent_comments, many=True, context={'request': request}).data
    serialized_data['comments'] = comments_data

    return Response(serialized_data, status=status.HTTP_200_OK)


# 영화 디테일 뷰 -> 탭 1(Cast & Crews)
'''from .serializers import MovieDetailTabOneSerializer

@swagger_auto_schema(
    method='get',
    operation_summary="Cast & Crews 정보 조회",
    operation_description="영화의 배우와 감독 정보를 포함한 Cast & Crews 데이터를 반환합니다. 뉴스 및 댓글도 함께 반환됩니다.",
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="Cast & Crews 데이터를 조회할 영화의 ID",
            type=openapi.TYPE_INTEGER
        )
    ],
    responses={
        200: openapi.Response(
            description="성공적으로 Cast & Crews 데이터를 반환",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "Inception",
                    "poster_path": "/path/to/poster.jpg",
                    "genres": ["Action", "Sci-Fi"],
                    "overview": "A thief who steals corporate secrets...",
                    "release_date": "2010-07-16",
                    "normalized_popularity": 8.8,
                    "is_liked": True,
                    "news": [
                    {
                        "title": "New Sci-Fi Movie",
                        "content": "A deep dive into dream-sharing technology...",
                        "url": "https://example.com/news",
                        "created_at": "2024-11-20T12:00:00Z"
                    }
],
"comments": {
    "count": 10,
    "next": "http://example.com/api/movies/1/comments/?page=2",
    "previous": None,
    "results": [
        {
            "id": 1,
            "user": "user123",
            "content": "Great movie!",
            "created_at": "2024-11-19T12:00:00Z",
            "like_count": 5,
            "dislike_count": 0
        }
    ]
},
"cast": [
    {"id": 1, "name": "Leonardo DiCaprio", "character": "Cobb"},
    {"id": 2, "name": "Joseph Gordon-Levitt", "character": "Arthur"}
],
"crews": [
    {"id": 1, "name": "Christopher Nolan", "job": "Director"}
],

                }
            }
        ),
        404: openapi.Response(description="해당 영화를 찾을 수 없음")
    }
)
@api_view(['GET'])
def movie_cast_and_crews_view(request, movie_id):
    """
    영화의 배우, 감독, 뉴스, 댓글 정보를 반환하는 API 엔드포인트.

    - Cast & Crews 정보는 전체 데이터를 반환합니다.
    - 댓글 정보는 페이지네이션을 적용하여 반환합니다.

    Args:
        request: HTTP 요청 객체
        movie_id (int): 조회할 영화의 ID

    Returns:
        Response: JSON 응답 (Cast & Crews, 뉴스, 댓글)
    """
    # 1. 영화 객체 가져오기
    movie = get_object_or_404(Movie, pk=movie_id)
    serializer = MovieDetailTabOneSerializer(movie, context={'request': request})
    serialized_data = serializer.data

    # 댓글 데이터 가져오기
    parent_comments = movie.movie_comments.filter(parent=None).order_by('-created_at')  # 부모 댓글만 필터링
    
    # 페이지네이션 주석 처리
    # paginator = CommentsPagination()
    # paginated_comments = paginator.paginate_queryset(comments, request)

    # 댓글 데이터를 직렬화 (전체 데이터를 반환)
    serialized_comments = CommentSerializer(parent_comments, many=True, context={'request': request}).data

    # 댓글 데이터 추가 (전체 댓글 반환)
    # serialized_data['comments'] = paginator.get_paginated_response(serialized_comments).data
    serialized_data['comments'] = serialized_comments  # 페이지네이션 제거

    return Response(serialized_data, status=status.HTTP_200_OK)






# 영화 디테일 뷰 -> 탭 2(Trailer)
from .serializers import MovieTrailerTabTwoSerializer
@swagger_auto_schema(
    method='get',
    operation_summary="영화 트레일러 조회",
    operation_description="""
        영화의 트레일러 링크와 공통 데이터를 반환합니다.
        - 포스터 사진
        - 영화 제목
        - 장르
        - overview
        - release date
        - 정규화된 평점
        - 좋아요 여부
        - 관련 뉴스
        - 영화 댓글 (페이지네이션 적용)
    """,
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="조회할 영화의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="성공적으로 영화 데이터를 반환",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "Inception",
                    "poster_path": "/path/to/poster.jpg",
                    "genres": ["Action", "Sci-Fi", "Thriller"],
                    "overview": "A thief who steals corporate secrets...",
                    "release_date": "2010-07-16",
                    "normalized_popularity": 8.8,
                    "is_liked": True,
                    "trailer_link": "https://youtube.com/trailer_link",  # 누락된 필드 추가
                    "news": [
                        {
                            "title": "The Science Behind Inception",
                            "content": "Exploring dream-sharing technology...",
                            "url": "https://example.com/science-of-inception",
                            "created_at": "2024-11-19T10:00:00Z"
                        }
                    ],
                    "comments": {
                        "count": 10,
                        "next": "http://example.com/api/movies/1/comments/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "user": "user123",
                                "content": "Amazing movie!",
                                "created_at": "2024-11-19T12:00:00Z",
                                "like_count": 10,
                                "dislike_count": 0
                            }
                        ]
                    }
                }
            }
        ),
        404: openapi.Response(description="해당 영화를 찾을 수 없음")
    }
)
@api_view(['GET'])
def movie_trailer_view(request, movie_id):
    """
    영화 트레일러 및 공통 데이터를 반환하는 API 엔드포인트.

    - 트레일러 링크와 기본 영화 정보를 포함합니다.
    - 댓글 데이터는 페이지네이션 적용 후 반환됩니다.
    """
    # 1. 특정 영화 가져오기
    movie = get_object_or_404(Movie, pk=movie_id)
    serializer = MovieTrailerTabTwoSerializer(movie, context={'request': request})
    serialized_data = serializer.data

    # 댓글 데이터 가져오기
    # comments = movie.movie_comments.all().order_by('-created_at')
    
    # 페이지네이션 주석 처리
    # paginator = CommentsPagination()
    # paginated_comments = paginator.paginate_queryset(comments, request)

    # 댓글 데이터를 직렬화 (전체 데이터를 반환)
    # serialized_comments = CommentSerializer(comments, many=True, context={'request': request}).data

    # 댓글 데이터 추가 (전체 댓글 반환)
    # serialized_data['comments'] = paginator.get_paginated_response(serialized_comments).data
    # serialized_data['comments'] = serialized_comments  # 페이지네이션 제거

    return Response(serialized_data, status=status.HTTP_200_OK)




# 영화 디테일 뷰 -> 탭 3(related)
from .serializers import MovieRelatedTabThreeSerializer
@swagger_auto_schema(
    method='get',
    operation_summary="관련 영화 및 리뷰 데이터 조회",
    operation_description="""
        현재 영화와 관련된 영화와 리뷰 데이터를 반환합니다.
        - 같은 장르를 가진 영화 중 정규화된 평점이 높은 순으로 반환
        - 해당 영화의 리뷰 목록도 포함 (페이지네이션 적용)
        - 해당 영화의 댓글 목록도 포함 (페이지네이션 적용)
    """,
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="조회할 영화의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(description="성공적으로 관련 영화 및 리뷰 데이터를 반환"),
        404: openapi.Response(description="해당 영화를 찾을 수 없음")
    }
)
@api_view(['GET'])
def movie_related_view(request, movie_id):
    """
    관련된 영화, 리뷰 및 댓글 데이터를 반환하는 API 엔드포인트.

    - 관련 영화는 같은 장르를 공유하며 정규화된 평점 순으로 정렬.
    - 리뷰와 댓글 목록은 페이지네이션 처리하여 반환.
    """
    # 1. 특정 영화 가져오기
    movie = get_object_or_404(Movie, pk=movie_id)

    # 관련 영화 쿼리셋
    related_movies = Movie.objects.filter(
        genres__in=movie.genres.all()
    ).exclude(
        id=movie.id
    ).distinct().order_by('-normalized_popularity')[:8]

    # 댓글 데이터 가져오기
    # comments_queryset = movie.movie_comments.all().order_by('-created_at')
    
    # 페이지네이션 주석 처리
    # comments_data = paginate_data(
    #     comments_queryset, 
    #     request, 
    #     lambda comments: [
    #         {
    #             "id": comment.id,
    #             "user": comment.user.username,
    #             "content": comment.content,
    #             "created_at": comment.created_at,
    #             "like_count": comment.like_count,
    #             "dislike_count": comment.dislike_count,
    #         }
    #         for comment in comments
    #     ]
    # )
    # comments_data = [
    #     {
    #         "id": comment.id,
    #         "user": comment.user.username,
    #         "content": comment.content,
    #         "created_at": comment.created_at,
    #         "like_count": comment.like_count,
    #         "dislike_count": comment.dislike_count,
    #     }
    #     for comment in comments_queryset
    # ]

    # 리뷰 데이터 가져오기
    reviews_queryset = movie.reviews.all().order_by('-rating')

    # 페이지네이션 주석 처리
    # reviews_data = paginate_data(
    #     reviews_queryset, 
    #     request, 
    #     lambda reviews: [
    #         {
    #             "id": review.id,
    #             "rating": review.rating,
    #             "content": review.content,
    #             "user": review.user.username,
    #             "created_at": review.created_at,
    #             "updated_at": review.updated_at,
    #         }
    #         for review in reviews
    #     ]
    # )
    reviews_data = [
        {
            "id": review.id,
            "rating": review.rating,
            "content": review.content,
            "user": review.user.username,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
        }
        for review in reviews_queryset
    ]

    # 기본 데이터 직렬화
    serializer = MovieRelatedTabThreeSerializer(movie, context={'request': request})
    serialized_data = serializer.data

    # 관련 영화 데이터를 추가
    serialized_data['related_movies'] = [
        {
            'id': rel_movie.id,
            'title': rel_movie.title,
            'poster_path': rel_movie.poster_path,
            'normalized_popularity': rel_movie.normalized_popularity,
            'genres': [genre.name for genre in rel_movie.genres.all()],
        }
        for rel_movie in related_movies
    ]

    # 댓글 및 리뷰 데이터를 추가
    # serialized_data['comments'] = comments_data
    serialized_data['reviews'] = reviews_data

    return Response(serialized_data, status=status.HTTP_200_OK)'''



# 영화 댓글 작성
from .serializers import CommentSerializer
@swagger_auto_schema(
    method='post',
    operation_summary="영화 댓글 작성",
    operation_description="특정 영화에 댓글을 작성합니다. 부모 댓글 ID(`parent`)를 포함하면 대댓글로 작성됩니다.",
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="댓글을 작성할 영화의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'content': openapi.Schema(type=openapi.TYPE_STRING, description="댓글 내용", example="This is a comment"),
            'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description="부모 댓글 ID (대댓글 작성 시)", example=5),
        },
        required=['content'],  # parent는 필수가 아니므로 제외
    ),
    responses={
        201: "댓글 작성 성공",
        400: "잘못된 요청 데이터"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def movie_comment_create_view(request, movie_id):
    """
    특정 영화에 댓글 작성 API
    """
    movie = get_object_or_404(Movie, pk=movie_id)
    data = request.data.copy()
    data['movie'] = movie_id

    parent_id = data.get('parent')

    if parent_id:
        parent_comment = get_object_or_404(Comment, pk=parent_id)
        if parent_comment.movie_id != movie_id:
            return Response({"detail": "부모 댓글이 현재 영화에 속하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        data['parent'] = parent_comment.id

    serializer = CommentSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        comment = serializer.save(user=request.user, movie=movie)
        response_data = serializer.data
        response_data["parent"] = comment.parent_id  # 부모 댓글 정보 포함
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# 영화 댓글 수정
@swagger_auto_schema(
    method='put',
    operation_summary="영화 댓글 수정",
    operation_description="특정 영화의 댓글을 수정합니다. 작성자 본인만 수정할 수 있습니다.",
    request_body=CommentSerializer,
    responses={
        200: openapi.Response(
            description="댓글 수정 성공.",
            schema=CommentSerializer
        ),
        400: openapi.Response(description="유효하지 않은 데이터."),
        403: openapi.Response(description="권한이 없음."),
        404: openapi.Response(description="댓글을 찾을 수 없음."),
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def movie_comment_update_view(request, movie_id, comment_id):
    """
    영화 댓글 수정 API
    """
    comment = get_object_or_404(Comment, pk=comment_id, movie_id=movie_id)
    if comment.user != request.user:
        return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = CommentSerializer(comment, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 영화 댓글 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="영화 댓글 삭제",
    operation_description="특정 영화의 댓글을 삭제합니다. 작성자 본인만 삭제할 수 있습니다.",
    responses={
        204: openapi.Response(description="댓글 삭제 성공."),
        403: openapi.Response(description="권한이 없음."),
        404: openapi.Response(description="댓글을 찾을 수 없음."),
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def movie_comment_delete_view(request, movie_id, comment_id):
    """
    영화 댓글 삭제 API
    """
    comment = get_object_or_404(Comment, pk=comment_id, movie_id=movie_id)
    if comment.user != request.user:
        return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    comment.delete()
    return Response({"comment_id": comment_id}, status=status.HTTP_204_NO_CONTENT)



# 영화 좋아요/좋아요 취소 API
@swagger_auto_schema(
    method='post',
    operation_summary="영화 좋아요/좋아요 취소",
    operation_description="사용자가 특정 영화를 좋아요하거나 좋아요를 취소합니다.",
    responses={
        200: openapi.Response(
            description="성공적으로 좋아요 상태를 변경",
            examples={
                "application/json": {
                    "message": "좋아요 완료",
                    "is_favorited": True
                }
            }
        ),
        403: openapi.Response(description="로그인이 필요합니다."),
        404: openapi.Response(description="해당 영화를 찾을 수 없음")
    },
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="좋아요 상태를 변경할 영화의 ID",
            type=openapi.TYPE_INTEGER
        )
    ]
)
@api_view(['POST'])
def toggle_movie_favorite_view(request, movie_id):
    """
    영화 좋아요/좋아요 취소 API
    - 요청한 사용자가 특정 영화를 좋아요하거나 좋아요를 취소합니다.
    """
    # 인증 여부 확인
    if not request.user.is_authenticated:
        # request.user = User.objects.first()  # 개발용 첫 번째 사용자로 설정
        return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

    # 영화 가져오기
    movie = get_object_or_404(Movie, id=movie_id)

    # 좋아요 상태 확인 및 토글
    if movie.liked_movies_by_users.filter(id=request.user.id).exists():
        movie.liked_movies_by_users.remove(request.user)  # 좋아요 취소
        return Response({"message": "좋아요 취소 완료", "is_favorited": False}, status=status.HTTP_200_OK)
    else:
        movie.liked_movies_by_users.add(request.user)  # 좋아요 추가
        return Response({"message": "좋아요 완료", "is_favorited": True}, status=status.HTTP_200_OK)
    


# -----------------------------------------배우 디테일(댓글 생성 수정 삭제테스트 필요)-------------------------------------

# 배우 프로필 조회 API
@swagger_auto_schema(
    method='get',
    operation_summary="배우 상세 정보 조회",
    operation_description="""
        배우의 상세 정보를 조회합니다. 다음 정보를 포함합니다:
        - 배우의 기본 정보
        - 필모그래피 (출연작 목록)
        - 배우에 대한 댓글 (페이지네이션 적용)
        - 좋아요 여부
    """,
    manual_parameters=[
        openapi.Parameter(
            'actor_id',
            openapi.IN_PATH,
            description="조회할 배우의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="배우 상세 정보 조회 성공.",
            examples={
                "application/json": {
                    "id": 1,
                    "name": "Leonardo DiCaprio",
                    "biography": "Leonardo Wilhelm DiCaprio is an American actor...",
                    "birthdate": "1974-11-11",  # 수정: birth_date -> birthdate
                    "birthplace": "Los Angeles, California, USA",  # 수정: birth_place -> birthplace
                    "profile_path": "/path/to/profile.jpg",
                    "is_liked": True,
                    "filmography": [
                        {
                            "id": 1,
                            "title": "Inception",
                            "release_date": "2010-07-16",
                            "poster_path": "/path/to/poster.jpg",
                            "normalized_popularity": 8.8
                        }
                    ],
                    "comments": {
                        "count": 5,
                        "next": "http://example.com/api/actors/1/comments/?page=2",
                        "previous": None,  # JSON에서는 null
                        "results": [
                            {
                                "id": 1,
                                "user": "user123",
                                "content": "Great performance in Inception!",
                                "created_at": "2024-11-19T12:00:00Z",
                                "like_count": 10,
                                "dislike_count": 0
                            }
                        ]
                    },
                    "notable_roles": [
                        {
                            "character_name": "Cobb",
                            "movie_title": "Inception",
                            "movie_id": 1
                        }
                    ]
                }
            }
        ),
        404: openapi.Response(description="해당 배우를 찾을 수 없음.")
    }
)
@api_view(['GET'])
def actor_detail_view(request, actor_id):
    """
    배우의 상세 정보를 조회하는 API 엔드포인트.
    """
    # 1. actor_id에 해당하는 Actor 객체를 가져옴. 없으면 404 반환.
    actor = get_object_or_404(Actor, pk=actor_id)

    # 2. 배우에 달린 parent가 없는 댓글만 가져오기
    comments_queryset = Comment.objects.filter(actor_id=actor_id, parent=None).order_by('-created_at')

    # 3. CommentSerializer를 활용하여 댓글 직렬화
    comments_data = CommentSerializer(comments_queryset, many=True, context={'request': request}).data

    # 4. 배우 기본 데이터 직렬화
    serializer = ActorDetailSerializer(actor, context={'request': request})
    serialized_data = serializer.data

    # 5. 직렬화된 데이터에 모든 댓글 추가
    serialized_data['comments'] = comments_data

    # 6. 최종 데이터 반환
    return Response(serialized_data, status=status.HTTP_200_OK)



# 배우 좋아요/좋아요 취소 API
@swagger_auto_schema(
    method='post',
    operation_summary="배우 좋아요 토글",
    operation_description="사용자가 배우를 좋아요하거나 좋아요를 취소합니다.",
    responses={
        200: openapi.Response(
            description="좋아요 상태 토글 성공.",
            examples={"application/json": {"liked": True}}
        ),
        404: openapi.Response(description="해당 배우를 찾을 수 없음."),
        403: openapi.Response(description="인증 정보가 제공되지 않음."),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 인증된 사용자만 접근 가능
def actor_toggle_like_view(request, actor_id):
    """
    배우에 대해 좋아요/좋아요 취소를 토글하는 API 엔드포인트.
    - 사용자가 이미 좋아요를 눌렀다면 좋아요를 취소합니다.
    - 좋아요를 누르지 않았다면 좋아요를 추가합니다.

    Args:
        request (HttpRequest): 클라이언트 요청 객체 (인증된 사용자 필요).
        actor_id (int): 좋아요를 토글하려는 배우의 고유 ID.

    Returns:
        Response: 좋아요 상태(`liked: True/False`)와 HTTP 상태 코드.
    """
    # 1. actor_id에 해당하는 Actor 객체를 데이터베이스에서 가져옴.
    #    객체가 없으면 404 오류 반환.
    actor = get_object_or_404(Actor, pk=actor_id)

    # 2. 요청을 보낸 사용자 객체를 가져옴.
    user = request.user

    # 3. 사용자가 이미 좋아요를 눌렀는지 확인.
    if actor.favorited_actors_by_users.filter(pk=user.pk).exists():
        # 좋아요가 이미 눌러져 있다면 좋아요를 취소 (관계 제거).
        actor.favorited_actors_by_users.remove(user)
        liked = False  # 좋아요 취소 상태
    else:
        # 좋아요가 눌러져 있지 않다면 좋아요를 추가 (관계 추가).
        actor.favorited_actors_by_users.add(user)
        liked = True  # 좋아요 상태

    # 4. 좋아요 상태를 JSON 형식으로 반환.
    return Response({'liked': liked}, status=status.HTTP_200_OK)



# 배우 댓글 작성
@swagger_auto_schema(
    method='post',
    operation_summary="배우에 대한 댓글 작성",
    operation_description="배우에 대한 새 댓글을 작성합니다. 인증된 사용자만 접근 가능합니다.",
    request_body=ActorDetailSerializer.ActorCommentSerializer,
    responses={
        201: openapi.Response(
            description="댓글 작성 성공.",
            schema=ActorDetailSerializer.ActorCommentSerializer
        ),
        400: openapi.Response(description="유효하지 않은 데이터."),
        404: openapi.Response(description="해당 배우를 찾을 수 없음."),
        403: openapi.Response(description="인증 정보가 제공되지 않음."),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def actor_comment_create_view(request, actor_id):
    """
    특정 배우에 댓글 작성 API
    """
    actor = get_object_or_404(Actor, pk=actor_id)
    data = request.data.copy()
    data['actor'] = actor_id

    parent_id = data.get('parent')

    if parent_id:
        parent_comment = get_object_or_404(Comment, pk=parent_id)
        if parent_comment.actor_id != actor_id:
            return Response({"detail": "부모 댓글이 현재 배우에 속하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        data['parent'] = parent_comment.id

    serializer = CommentSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        comment = serializer.save(user=request.user, actor=actor)
        response_data = serializer.data
        response_data["parent"] = comment.parent_id  # 부모 댓글 정보 포함
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 배우 댓글 수정 뷰
@swagger_auto_schema(
    method='put',
    operation_summary="배우 댓글 수정",
    operation_description="기존 배우 댓글을 수정합니다. 작성자 본인만 수정할 수 있습니다.",
    request_body=ActorDetailSerializer.ActorCommentSerializer,
    responses={
        200: openapi.Response(
            description="댓글 수정 성공.",
            schema=ActorDetailSerializer.ActorCommentSerializer
        ),
        400: openapi.Response(description="유효하지 않은 데이터."),
        403: openapi.Response(description="권한이 없음."),
        404: openapi.Response(description="댓글을 찾을 수 없음."),
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actor_comment_update_view(request, actor_id, comment_id):
    """
    배우 댓글 수정 API
    - 요청 사용자가 본인의 댓글만 수정할 수 있습니다.
    """
    # 1. actor_id와 comment_id를 사용해 댓글을 가져옴.
    comment = get_object_or_404(Comment, pk=comment_id, actor_id=actor_id)

    # 2. 요청 사용자가 댓글 작성자가 아닌 경우 권한 오류 반환.
    if comment.user != request.user:
        return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    # 3. 댓글 내용 수정
    serializer = ActorDetailSerializer.ActorCommentSerializer(comment, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 4. 유효하지 않은 데이터 처리
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# 배우 댓글 삭제 뷰
@swagger_auto_schema(
    method='delete',
    operation_summary="배우 댓글 삭제",
    operation_description="기존 배우 댓글을 삭제합니다. 작성자 본인만 삭제할 수 있습니다.",
    responses={
        204: openapi.Response(description="댓글 삭제 성공."),
        403: openapi.Response(description="권한이 없음."),
        404: openapi.Response(description="댓글을 찾을 수 없음."),
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def actor_comment_delete_view(request, actor_id, comment_id):
    """
    배우 댓글 삭제 API
    - 요청 사용자가 본인의 댓글만 삭제할 수 있습니다.
    """
    # 1. actor_id와 comment_id를 사용해 댓글을 가져옴.
    comment = get_object_or_404(Comment, pk=comment_id, actor_id=actor_id)

    # 2. 요청 사용자가 댓글 작성자가 아닌 경우 권한 오류 반환.
    if comment.user != request.user:
        return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    # 3. 댓글 삭제
    comment.delete()
    return Response({"message": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)




# -----------------------------------------감독 디테일(댓글 생성 수정 삭제테스트 필요)-------------------------------------

from .serializers import DirectorDetailSerializer 
# DirectorDetailSerializer.CommentSerializer

# 감독 프로필 조회 API
@swagger_auto_schema(
    method='get',
    operation_summary="감독 상세 정보 조회",
    operation_description="""
        특정 감독의 상세 정보를 조회합니다. 다음 정보를 포함합니다:
        - 감독의 기본 정보
        - 필모그래피 (감독한 영화 목록)
        - 감독에 대한 댓글 (페이지네이션 적용)
        - 좋아요 여부
    """,
    manual_parameters=[
        openapi.Parameter(
            'director_id',
            openapi.IN_PATH,
            description="조회할 감독의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="감독 상세 정보 조회 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "name": "Christopher Nolan",
                    "biography": "Christopher Edward Nolan is a British-American film director...",
                    "birthdate": "1970-07-30",  # 수정: birth_date -> birthdate
                    "birthplace": "London, England, UK",  # 수정: birth_place -> birthplace
                    "profile_path": "/path/to/profile.jpg",
                    "is_liked": True,
                    "filmography": [
                        {
                            "id": 1,
                            "title": "Inception",
                            "release_date": "2010-07-16",
                            "poster_path": "/path/to/poster.jpg",
                            "normalized_popularity": 8.8
                        }
                    ],
                    "comments": {
                        "count": 5,
                        "next": "http://example.com/api/directors/1/comments/?page=2",
                        "previous": None,  # JSON에서는 null
                        "results": [
                            {
                                "id": 1,
                                "user": "user123",
                                "content": "Great director!",
                                "created_at": "2024-11-19T12:00:00Z",
                                "like_count": 10,
                                "dislike_count": 0
                            }
                        ]
                    }
                }
            }
        ),
        404: openapi.Response(description="해당 감독을 찾을 수 없음")
    }
)
@api_view(['GET'])
def director_detail_view(request, director_id):
    """
    감독의 상세 정보를 조회하는 API 엔드포인트.
    """
    # 1. director_id에 해당하는 Director 객체를 가져옴. 없으면 404 반환.
    director = get_object_or_404(Director, pk=director_id)

    # 2. 감독에 달린 parent가 없는 댓글만 가져오기
    comments_queryset = Comment.objects.filter(director_id=director_id, parent=None).order_by('-created_at')

    # 3. CommentSerializer를 활용하여 댓글 직렬화
    comments_data = CommentSerializer(comments_queryset, many=True, context={'request': request}).data

    # 4. 감독 기본 데이터 직렬화
    serializer = DirectorDetailSerializer(director, context={'request': request})
    serialized_data = serializer.data

    # 5. 직렬화된 데이터에 모든 댓글 추가
    serialized_data['comments'] = comments_data

    # 6. 최종 데이터 반환
    return Response(serialized_data, status=status.HTTP_200_OK)





# 감독 좋아요 토글
@swagger_auto_schema(
    method='post',
    operation_summary="감독 좋아요 토글",
    operation_description="""
        특정 감독에 대해 좋아요를 추가하거나 취소합니다.
        - 사용자가 이미 좋아요를 누른 상태라면, 좋아요가 취소됩니다.
        - 사용자가 좋아요를 누르지 않은 상태라면, 좋아요가 추가됩니다.
    """,
    manual_parameters=[
        openapi.Parameter(
            'director_id',
            openapi.IN_PATH,
            description="좋아요를 토글할 감독의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="좋아요 상태 토글 성공",
            examples={"application/json": {"liked": True}}
        ),
        404: openapi.Response(description="해당 감독을 찾을 수 없음"),
        403: openapi.Response(description="인증 정보가 제공되지 않음")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def director_toggle_like_view(request, director_id):
    """
    감독에 대해 좋아요/좋아요 취소를 토글하는 API 엔드포인트.

    - 사용자가 좋아요를 이미 눌렀으면 좋아요를 취소하고, 그렇지 않으면 좋아요를 추가합니다.

    Args:
        request (HttpRequest): 클라이언트 요청 객체.
        director_id (int): 좋아요를 토글하려는 감독의 고유 ID.

    Returns:
        Response: 좋아요 상태(JSON 형식)와 HTTP 상태 코드.
    """
    # 1. 감독 객체 가져오기
    director = get_object_or_404(Director, pk=director_id)

    # 2. 요청한 사용자 가져오기
    user = request.user

    # 3. 좋아요 상태 토글
    if director.favorited_directors_by_users.filter(pk=user.pk).exists():
        director.favorited_directors_by_users.remove(user)
        liked = False
    else:
        director.favorited_directors_by_users.add(user)
        liked = True

    # 4. 좋아요 상태 반환
    return Response({'liked': liked}, status=status.HTTP_200_OK)





# 감독 댓글 작성
@swagger_auto_schema(
    method='post',
    operation_summary="감독 댓글 작성",
    operation_description="특정 감독에 대해 댓글을 작성합니다. 인증된 사용자만 접근 가능합니다.",
    request_body=DirectorDetailSerializer.DirectorCommentSerializer,
    responses={
        201: openapi.Response(
            description="댓글 작성 성공",
            schema=DirectorDetailSerializer.DirectorCommentSerializer
        ),
        400: openapi.Response(description="유효하지 않은 데이터"),
        404: openapi.Response(description="해당 감독을 찾을 수 없음"),
        403: openapi.Response(description="인증 정보가 제공되지 않음")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def director_comment_create_view(request, director_id):
    """
    특정 감독에 댓글 작성 API
    """
    director = get_object_or_404(Director, pk=director_id)
    data = request.data.copy()
    data['director'] = director_id

    parent_id = data.get('parent')

    if parent_id:
        parent_comment = get_object_or_404(Comment, pk=parent_id)
        if parent_comment.director_id != director_id:
            return Response({"detail": "부모 댓글이 현재 감독에 속하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        data['parent'] = parent_comment.id

    serializer = CommentSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        comment = serializer.save(user=request.user, director=director)
        response_data = serializer.data
        response_data["parent"] = comment.parent_id  # 부모 댓글 정보 포함
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# 감독 댓글 수정
@swagger_auto_schema(
    method='put',
    operation_summary="감독 댓글 수정",
    operation_description="감독에 대한 기존 댓글을 수정합니다. 작성자 본인만 수정 가능합니다.",
    request_body=DirectorDetailSerializer.DirectorCommentSerializer,
    responses={
        200: openapi.Response(
            description="댓글 수정 성공",
            schema=DirectorDetailSerializer.DirectorCommentSerializer
        ),
        400: openapi.Response(description="유효하지 않은 데이터"),
        403: openapi.Response(description="권한이 없음"),
        404: openapi.Response(description="댓글을 찾을 수 없음")
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # 인증된 사용자만 접근 가능
def director_comment_update_view(request, director_id, comment_id):
    """
    감독 댓글 수정 API
    - 요청 사용자가 본인의 댓글만 수정할 수 있습니다.
    """
    # 1. director_id와 comment_id로 댓글 객체를 가져옴
    comment = get_object_or_404(Comment, pk=comment_id, director_id=director_id)

    # 2. 요청 사용자가 댓글 작성자가 아닌 경우 권한 오류 반환
    if comment.user != request.user:
        return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    # 3. 댓글 내용 수정
    serializer = DirectorDetailSerializer.DirectorCommentSerializer(comment, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 4. 유효하지 않은 데이터 처리
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# 감독 댓글 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="감독 댓글 삭제",
    operation_description="감독에 대한 기존 댓글을 삭제합니다. 작성자 본인만 삭제 가능합니다.",
    responses={
        204: openapi.Response(description="댓글 삭제 성공"),
        403: openapi.Response(description="권한이 없음"),
        404: openapi.Response(description="댓글을 찾을 수 없음")
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # 인증된 사용자만 접근 가능
def director_comment_delete_view(request, director_id, comment_id):
    """
    감독 댓글 삭제 API
    - 요청 사용자가 본인의 댓글만 삭제할 수 있습니다.
    """
    # 1. director_id와 comment_id로 댓글 객체를 가져옴
    comment = get_object_or_404(Comment, pk=comment_id, director_id=director_id)

    # 2. 요청 사용자가 댓글 작성자가 아닌 경우 권한 오류 반환
    if comment.user != request.user:
        return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    # 3. 댓글 삭제
    comment.delete()
    return Response({"message": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)







































# ---------------------------------------------------------------------------------------------------------
# --------------------------------------데이터 크롤링-------------------------------------------------------
from django.conf import settings  # settings에서 환경 변수 불러오기
import requests
from datetime import datetime

from django.conf import settings  # settings에서 환경 변수 불러오기
import requests
from datetime import datetime
from django.http import JsonResponse
from .models import Movie, Actor, Director, Genre
import time

BASE_URL = 'https://api.themoviedb.org/3'
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

# 성별 매핑 (숫자를 문자열로 변환)
GENDER_MAP = {
    0: "Unknown",  # 성별 정보 없음
    1: "Female",   # 여성
    2: "Male"      # 남성
}

def fetch_trailer_from_youtube(movie_title):
    """YouTube에서 영화 트레일러를 검색하고 첫 번째 결과의 링크를 반환합니다."""
    try:
        query = f"{movie_title} 트레일러"
        params = {
            'part': 'snippet',
            'q': query,
            'key': settings.YOUTUBE_API_KEY,  # YouTube API 키 사용
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
    """TMDB API에서 장르 데이터를 가져와 데이터베이스에 저장합니다."""
    try:
        url = f'{BASE_URL}/genre/movie/list'
        headers = {'Authorization': settings.TMDB_API_TOKEN}  # TMDB API 토큰 사용
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


def fetch_popular_movies_and_credits(request):
    """TMDB에서 인기 영화 데이터를 가져오고, 관련 정보를 데이터베이스에 저장합니다."""
    try:
        # TMDB에서 장르 데이터를 가져와 저장
        fetch_and_store_genres()

        # TMDB에서 인기 영화 데이터를 5페이지씩 가져오기
        for page in range(1, 5):  # 페이지 범위는 필요에 따라 변경
            url = f'{BASE_URL}/movie/popular'
            headers = {'Authorization': settings.TMDB_API_TOKEN}
            params = {'language': 'ko-KR', 'page': page}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                movies = response.json().get('results', [])
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

                    # 영화 장르 설정
                    genre_ids = movie_data.get('genre_ids', [])
                    genres = Genre.objects.filter(tmdb_id__in=genre_ids)
                    movie.genres.set(genres)

                    # 영화 출연진 및 감독 정보 저장
                    fetch_movie_credits(movie)

                    # YouTube에서 영화 트레일러 가져오기
                    trailer_link = fetch_trailer_from_youtube(movie.title)
                    if trailer_link:
                        movie.trailer_link = trailer_link
                        movie.save()
                        print(f"트레일러 저장 완료: {movie.title} - {trailer_link}")
            else:
                print(f"영화 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")

            # API 요청 제한을 고려하여 페이지 간 요청마다 1초 대기
            time.sleep(1)

        return JsonResponse({'success': '영화 데이터가 성공적으로 저장되었습니다!'})
    except Exception as e:
        return JsonResponse({'error': f'오류 발생: {str(e)}'}, status=500)


def parse_release_date(date_str):
    """문자열로 된 날짜를 'YYYY-MM-DD' 형식으로 파싱합니다."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def fetch_movie_credits(movie):
    """특정 영화의 출연진 및 감독 데이터를 TMDB에서 가져와 데이터베이스에 저장합니다."""
    try:
        url = f'{BASE_URL}/movie/{movie.tmdb_id}/credits'
        headers = {'Authorization': settings.TMDB_API_TOKEN}
        params = {'language': 'ko-KR'}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            credits = response.json()

            # 배우 정보 저장 (출연 순서 기준으로 5명 이내)
            for cast in credits.get('cast', []):
                if cast.get('order', 999) < 5:
                    actor, _ = Actor.objects.get_or_create(
                        tmdb_id=cast['id'],
                        defaults={
                            'name': cast['name'],
                            'gender': GENDER_MAP.get(cast['gender'], "Unknown"),
                            'profile_path': cast.get('profile_path'),
                        }
                    )
                    actor.movies.add(movie)
                    print(f"배우 저장 완료: {actor.name} (영화: {movie.title})")
        else:
            print(f"출연진 정보를 가져오는 데 실패했습니다. 영화: {movie.title}")
    except Exception as e:
        print(f"출연진 정보를 가져오는 중 오류 발생. 영화: {movie.title}, 오류: {str(e)}")

def fetch_person_details(person_id):
    """
    TMDB에서 특정 인물의 추가 정보를 가져와 데이터베이스에 저장합니다.
    """
    try:
        url = f'{BASE_URL}/person/{person_id}'
        headers = {'Authorization': settings.TMDB_API_TOKEN}
        params = {'language': 'en-US'}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            person_details = response.json()
            return {
                'birthdate': person_details.get('birthday'),
                'biography': person_details.get('biography'),
                'birthplace': person_details.get('place_of_birth')
            }
        else:
            print(f"인물 정보를 가져오는 데 실패했습니다. 인물 ID: {person_id}, 상태 코드: {response.status_code}")
            return None
    except Exception as e:
        print(f"인물 정보를 가져오는 중 오류 발생. 인물 ID: {person_id}, 오류: {str(e)}")
        return None


def update_biography_for_all_movies(request):
    """
    모든 영화에 대해 출연진 및 감독의 biography 필드를 업데이트합니다.
    """
    try:
        # Movie 모델에 저장된 모든 영화에 대해 배우 및 감독의 biography 필드를 업데이트
        movies = Movie.objects.all()
        for movie in movies:
            url = f'{BASE_URL}/movie/{movie.tmdb_id}/credits'
            headers = {'Authorization': settings.TMDB_API_TOKEN}
            params = {'language': 'en-US'}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                credits = response.json()

                # 배우 정보 업데이트 (출연 순서 기준으로 5명 이내)
                for cast in credits.get('cast', []):
                    if cast.get('order', 999) < 5:
                        try:
                            actor = Actor.objects.get(tmdb_id=cast['id'])
                            actor_details = fetch_person_details(cast['id'])
                            if actor_details:
                                actor.biography = actor_details.get('biography')
                                actor.save(update_fields=['biography'])
                                print(f"배우 {actor.name}의 biography 업데이트 완료.")
                        except Actor.DoesNotExist:
                            print(f"Actor with TMDB ID {cast['id']} does not exist.")

                # 감독 정보 업데이트
                for crew in credits.get('crew', []):
                    if crew['job'] == 'Director':
                        try:
                            director = Director.objects.get(tmdb_id=crew['id'])
                            director_details = fetch_person_details(crew['id'])
                            if director_details:
                                director.biography = director_details.get('biography')
                                director.save(update_fields=['biography'])
                                print(f"감독 {director.name}의 biography 업데이트 완료.")
                        except Director.DoesNotExist:
                            print(f"Director with TMDB ID {crew['id']} does not exist.")
            else:
                print(f"출연진 정보를 가져오는 데 실패했습니다. 영화: {movie.title}, 상태 코드: {response.status_code}")

        return JsonResponse({'success': '모든 영화에 대한 출연진 및 감독의 biography 업데이트 완료'})
    except Exception as e:
        return JsonResponse({'error': f'오류 발생: {str(e)}'}, status=500)




def update_overview_for_all_movies(request):
    """
    모든 영화에 대해 overview 필드를 업데이트합니다.
    """
    try:
        # Movie 모델에 저장된 모든 영화에 대해 overview 필드를 업데이트
        movies = Movie.objects.all()
        for movie in movies:
            url = f'{BASE_URL}/movie/{movie.tmdb_id}'
            headers = {'Authorization': settings.TMDB_API_TOKEN}
            params = {'language': 'en-US'}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                movie_data = response.json()
                if not movie.overview:  # overview가 비어 있는 경우에만 업데이트
                    movie.overview = movie_data.get('overview')
                    movie.save(update_fields=['overview'])
                    print(f"영화 {movie.title}의 overview 업데이트 완료.")
            else:
                print(f"영화 정보를 가져오는 데 실패했습니다. 영화: {movie.title}, 상태 코드: {response.status_code}")

        return JsonResponse({'success': '모든 영화에 대한 overview 업데이트 완료'})
    except Exception as e:
        return JsonResponse({'error': f'오류 발생: {str(e)}'}, status=500)
    
    
    
from django.http import JsonResponse
from .models import Movie
from .tasks import fetch_and_save_movie_news
import time

def fetch_news_for_all_movies(request):
    """
    모든 영화에 대해 뉴스를 검색하고 저장.
    """
    movies = Movie.objects.all()
    for movie in movies:
        fetch_and_save_movie_news(movie.title)
        time.sleep(0.3)  # 1초 간격으로 요청

    return JsonResponse({"message": "모든 영화의 뉴스 저장 완료"})

from movies.models import Movie, Actor, Director
from movies.models import fetch_image_config


'''
24.11.22. 20:43 WKH
웹 서비스의 통합 검색 페이지에 Actor, Director, CustomUser를 모두 전달해서 검색 가능하게 만들기 위한 클래스 뷰
'''
class SearchDataView(APIView):
    """
    Actor, Director, CustomUser 데이터를 반환하는 API 뷰.
    역참조 데이터(사용자 수 등)를 포함.
    """
    def get(self, request, *args, **kwargs):
        # Actor 데이터: favorite_count 기준 내림차순 정렬
        actors = Actor.objects.annotate(
            favorited_count=Count('favorited_actors_by_users')
        ).order_by('-favorited_count')
        actor_serializer = ActorSerializer(actors, many=True)

        # Director 데이터: favorite_count 기준 내림차순 정렬
        directors = Director.objects.annotate(
            favorited_count=Count('favorited_directors_by_users')
        ).order_by('-favorited_count')
        director_serializer = DirectorSerializer(directors, many=True)

        # CustomUser 데이터: followers_count 기준 내림차순 정렬
        users = CustomUser.objects.annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')
        user_serializer = CustomUserSerializer(users, many=True)

        # 통합 응답 데이터
        response_data = {
            "actors": actor_serializer.data,
            "directors": director_serializer.data,
            "users": user_serializer.data,
        }
        return Response(response_data)
    
    
    
    
'''
11-24 07:20 AHS 추천알고리즘 추가

1. 사용자 정보 기반 추천
2. 사용자 입력 키워드 기반 추천

'''

# 1. 사용자 정보 기반

def calculate_genre_similarity(movie, user):
    """
    사용자 선호 장르와 영화 장르 간의 유사도를 계산.
    """
    user_genres = user.favorite_genres.all()
    movie_genres = movie.genres.all()
    common_genres = set(user_genres).intersection(movie_genres)
    return len(common_genres) / len(user_genres) if user_genres else 0


def calculate_liked_movies_similarity(movie, user):
    """
    사용자가 좋아요한 영화와 현재 영화의 장르 유사도를 계산.
    """
    liked_movies = user.liked_movies.all()
    similarities = [
        1 for liked_movie in liked_movies
        if liked_movie.genres.filter(id__in=movie.genres.values_list('id', flat=True)).exists()
    ]
    return sum(similarities) / len(liked_movies) if liked_movies else 0


def calculate_actor_similarity(movie, user):
    """
    사용자가 즐겨찾기한 배우가 출연한 영화인지 확인.
    """
    favorite_actors = user.favorite_actors.all()
    movie_actors = movie.actor_movies.all()
    common_actors = set(favorite_actors).intersection(movie_actors)
    return len(common_actors) / len(favorite_actors) if favorite_actors else 0

def calculate_director_similarity(movie, user):
    """
    사용자가 즐겨찾기한 감독이 연출한 영화인지 확인.
    """
    favorite_directors = user.favorite_directors.all()
    movie_directors = movie.director_movies.all()
    common_directors = set(favorite_directors).intersection(movie_directors)
    return len(common_directors) / len(favorite_directors) if favorite_directors else 0

def calculate_friend_activity(movie, user):
    """
    팔로우한 친구들이 좋아요한 영화와의 유사도 계산.
    """
    friends = user.following.all()
    friend_liked_movies = Movie.objects.filter(liked_movies_by_users__in=friends).distinct()
    return 1 if movie in friend_liked_movies else 0


def personalized_recommendations(user):
    """
    사용자 개인화 추천 리스트 생성
    """
    movies = Movie.objects.prefetch_related('genres', 'actor_movies', 'director_movies').all()
    recommendations = []

    for movie in movies:
        genre_score = calculate_genre_similarity(movie, user)
        liked_movie_score = calculate_liked_movies_similarity(movie, user)
        actor_score = calculate_actor_similarity(movie, user)
        director_score = calculate_director_similarity(movie, user)
        friend_score = calculate_friend_activity(movie, user)

        # 가중치 기반 최종 점수 계산
        total_score = (
            0.3 * genre_score +
            0.2 * liked_movie_score +
            0.2 * actor_score +
            0.2 * director_score +
            0.1 * friend_score
        )

        recommendations.append({"movie": movie, "score": total_score})

    # 점수 기준 정렬
    recommendations = sorted(recommendations, key=lambda x: x["score"], reverse=True)
    return recommendations[:10]  # 상위 10개 영화 반환


# 2. 키워드 기반


# 전역 캐싱 딕셔너리
movie_embeddings_cache = {}

def get_movie_embeddings(movie):
    """
    영화의 제목과 설명 임베딩을 반환. 캐싱을 사용해 중복 계산 방지.
    """
    if movie.id not in movie_embeddings_cache:
        movie_embeddings_cache[movie.id] = {
            "title_embedding": model.encode(movie.title),
            "overview_embedding": model.encode(movie.overview or "")
        }
    return movie_embeddings_cache[movie.id]


import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def keyword_based_recommendations_optimized(keyword):
    """
    최적화된 키워드 기반 영화 추천.
    """
    movies = Movie.objects.prefetch_related('genres').all()
    keyword_embedding = model.encode(keyword)

    title_embeddings = []
    overview_embeddings = []
    movie_list = []

    # 영화 데이터에서 캐싱된 임베딩 가져오기
    for movie in movies:
        embeddings = get_movie_embeddings(movie)
        title_embeddings.append(embeddings["title_embedding"])
        overview_embeddings.append(embeddings["overview_embedding"])
        movie_list.append(movie)

    # 배치로 코사인 유사도 계산
    title_similarities = cosine_similarity([keyword_embedding], title_embeddings)[0]
    overview_similarities = cosine_similarity([keyword_embedding], overview_embeddings)[0]

    # 가중치를 적용해 점수 계산
    recommendations = []
    for i, movie in enumerate(movie_list):
        total_score = 0.6 * title_similarities[i] + 0.4 * overview_similarities[i]
        recommendations.append({"movie": movie, "score": total_score})

    # 점수 기준으로 정렬
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:10]





@swagger_auto_schema(
    method='post',
    operation_summary="영화추천",
    operation_description="키워드를 기반으로 영화 추천을 반환합니다. (로그인 필요)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'keyword': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='추천받고 싶은 영화의 키워드 (선택)',
                example='time travel'
            ),
        },
        required=[]  # 키워드는 선택 필드
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'personalized_recommendations': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="개인화 추천 영화 리스트",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'title': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="영화 제목",
                                example="Inception"
                            ),
                            'score': openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="추천 점수",
                                example=0.92
                            )
                        }
                    )
                ),
                'keyword_based_recommendations': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="키워드 기반 추천 영화 리스트",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'title': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="영화 제목",
                                example="Interstellar"
                            ),
                            'score': openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="추천 점수",
                                example=0.89
                            )
                        }
                    )
                ),
            },
        ),
        401: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="에러 메시지",
                    example="Authentication credentials were not provided."
                )
            }
        ),
    }
)
@api_view(['POST'])
def recommendations_view(request):
    user = request.user  # 현재 로그인한 사용자
    keyword = request.data.get('keyword', None)  # 키워드 입력받기

    user = User.objects.get(pk=12)
    # 개인화 추천 생성
    personalized = personalized_recommendations(user)
    personalized_movies = [rec["movie"] for rec in personalized]

    # 키워드 기반 추천 생성
    if keyword:
        keyword_based = keyword_based_recommendations_optimized(keyword)
        keyword_movies = [rec["movie"] for rec in keyword_based]
    else:
        keyword_movies = []

    # 영화 정보 직렬화
    personalized_serialized = MovieCardSerializer(personalized_movies, many=True).data
    keyword_serialized = MovieCardSerializer(keyword_movies, many=True).data

    # 결과 반환
    response_data = {
        "personalized_recommendations": personalized_serialized,
        "keyword_based_recommendations": keyword_serialized,
    }

    return Response(response_data)


'''
24.11.24. WKH
'''
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def like_movie_view(request, movie_id):
    """
    영화 좋아요/좋아요 취소 API
    - 요청한 사용자가 특정 영화를 좋아요하거나 좋아요를 취소합니다.
    """
    # 인증된 사용자 가져오기
    user = request.user

    # 영화 객체 가져오기
    movie = get_object_or_404(Movie, id=movie_id)

    # 좋아요 상태 확인 및 토글
    if movie in user.liked_movies.all():
        user.liked_movies.remove(movie)  # 좋아요 취소
        return Response({"message": "좋아요 취소 완료", "is_favorited": False}, status=status.HTTP_200_OK)
    else:
        user.liked_movies.add(movie)  # 좋아요 추가
        return Response({"message": "좋아요 완료", "is_favorited": True}, status=status.HTTP_200_OK)
