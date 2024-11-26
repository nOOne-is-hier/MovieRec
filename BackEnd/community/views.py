from django.shortcuts import render
from utils import create_notification
from movies.models import Movie, Genre, Actor, Director, News, ActorCharacter
from community.models import Review, Post, Comment
from accounts.models import CustomUser, Notification 
from django.db.models import Count, Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import PostSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import CommentSerializer
from django.shortcuts import get_object_or_404
from .serializers import PostDetailSerializer
from rest_framework.exceptions import NotFound
from rest_framework import status



# 페이지네이션 클래스
class CustomPagination(PageNumberPagination):
    page_size = 10  # 한 페이지당 보여줄 항목 수
    page_size_query_param = 'page_size'  # 클라이언트가 page_size를 조정할 수 있게 함
    max_page_size = 100  # 최대 허용 page_size 값

    def paginate_queryset(self, queryset, request, view=None):
        """
        페이지네이션에서 빈 페이지 요청 시 빈 리스트 반환
        """
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            # 빈 페이지 요청 시 빈 리스트 반환
            self.page = None
            return []

    def get_paginated_response(self, data):
        """
        페이지네이션 응답 데이터 포맷
        """
        return Response({
            'count': self.page.paginator.count if self.page else 0,  # 전체 항목 수
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data  # 요청한 페이지 데이터
        })

# ---------------------------------------------------- 자유 게시판----------------------------------------------


# 자유게시판 - 목록 뷰

@swagger_auto_schema(
    method='get',
    operation_summary="게시글 목록 조회",
    operation_description="게시글 목록을 검색, 필터링, 정렬하여 가져옵니다.",
    manual_parameters=[
        openapi.Parameter(
            'query', openapi.IN_QUERY, 
            description="검색어. 기본값은 빈 문자열.", 
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'search_type', openapi.IN_QUERY,
            description=(
                "검색 조건:\n"
                "- `author`: 작성자 이름\n"
                "- `title`: 제목\n"
                "- `title_content`: 제목 또는 내용\n"
                "- `title_content_comment`: 제목, 내용 또는 댓글 내용"
            ),
            type=openapi.TYPE_STRING,
            enum=['author', 'title', 'title_content', 'title_content_comment'],
            default='title'
        ),
        openapi.Parameter(
            'sort', openapi.IN_QUERY,
            description=(
                "정렬 조건:\n"
                "- `created_at_desc`: 최신순 (기본값)\n"
                "- `created_at_asc`: 오래된 순\n"
                "- `comments_desc`: 댓글 많은 순\n"
                "- `likes_desc`: 좋아요 많은 순"
            ),
            type=openapi.TYPE_STRING,
            enum=['created_at_desc', 'created_at_asc', 'comments_desc', 'likes_desc'],
            default='created_at_desc'
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="페이지 번호 (기본값: 1).",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY,
            description="한 페이지당 표시할 게시글 수 (기본값: 10).",
            type=openapi.TYPE_INTEGER,
            default=10
        )
    ],
    responses={
        200: openapi.Response(
            description="성공적으로 게시글 목록을 반환합니다.",
            examples={
                "application/json": {
                    "count": 100,
                    "next": "http://example.com/community/posts/?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "게시글 제목 1",
                            "content": "게시글 내용...",
                            "created_at": "2024-11-20T14:32:00Z",
                            "user": {
                                "id": 101,
                                "username": "작성자1",
                                "profile_image": "https://example.com/user1.jpg",
                                "profile_url": "/accounts/users/101/liked-movies/"
                            },
                            "like_count": 90,
                            "comment_count": 4
                        },
                        {
                            "id": 2,
                            "title": "게시글 제목 2",
                            "content": "또 다른 게시글 내용...",
                            "created_at": "2024-11-19T13:20:00Z",
                            "user": {
                                "id": 102,
                                "username": "작성자2",
                                "profile_image": "https://example.com/user2.jpg",
                                "profile_url": "/accounts/users/102/liked-movies/"
                            },
                            "like_count": 77,
                            "comment_count": 4
                        }
                    ]
                }
            }
        )
    }
)
@api_view(['GET'])
def post_list_view(request):
    # 프론트엔드에서 URL 파라미터로 전달할 수 있는 검색 조건들
    query = request.GET.get('query', '')  # 검색어
    search_type = request.GET.get('search_type', 'title')  # 검색 조건
    sort = request.GET.get('sort', 'created_at_desc')  # 정렬 조건

    # 기본 QuerySet 설정
    # annotate를 사용하여 각 게시글의 좋아요 수와 댓글 수를 미리 계산
    posts = Post.objects.annotate(
        like_count=Count('liked_posts_by_users', distinct=True),  # 좋아요 수
        comment_count=Count('post_comments', distinct=True)  # 댓글 수
    )


    # 1️⃣ 검색 조건 적용
    if query:
        if search_type == 'author':
            # 작성자 이름으로 검색
            posts = posts.filter(user__username__icontains=query)
        elif search_type == 'title':
            # 제목으로 검색
            posts = posts.filter(title__icontains=query)
        elif search_type == 'title_content':
            # 제목 또는 내용으로 검색
            posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
        elif search_type == 'title_content_comment':
            # 제목, 내용, 또는 댓글 내용으로 검색
            posts = posts.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(post_comments__content__icontains=query)
            ).distinct()

    # 2️⃣ 정렬 조건 적용
    if sort == 'created_at_desc':
        # 최신순 정렬
        posts = posts.order_by('-created_at')
    elif sort == 'created_at_asc':
        # 오래된순 정렬
        posts = posts.order_by('created_at')
    elif sort == 'comments_desc':
        # 댓글 많은순 정렬
        posts = posts.order_by('-comment_count')
    elif sort == 'likes_desc':
        # 좋아요 많은순 정렬
        posts = posts.order_by('-like_count')

    # 3️⃣ 페이지네이션 처리
    paginator = CustomPagination()
    paginated_posts = paginator.paginate_queryset(posts, request)

    # 4️⃣ 데이터 직렬화
    serializer = PostSerializer(paginated_posts, many=True)
    return paginator.get_paginated_response(serializer.data)



# 자유게시판 게시글 - 상세 뷰
class CommentPagination(PageNumberPagination):
    page_size = 10  # 한 페이지에 보여줄 댓글 수


@swagger_auto_schema(
    method='get',
    operation_summary="게시글 상세 조회",
    operation_description="특정 게시글의 상세 정보를 반환하며, 페이지네이션이 적용된 댓글 목록을 포함합니다.",
    responses={
        200: openapi.Response(
            description="게시글 상세 조회 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "게시글 제목",
                    "content": "게시글 내용",
                    "like_count": 10,
                    "comment_count": 5,
                    "comments": [
                        {
                            "id": 1,
                            "content": "댓글 내용",
                            "like_count": 3,
                            "dislike_count": 0
                        }
                    ]
                }
            }
        ),
        404: openapi.Response(description="게시글을 찾을 수 없습니다.")
    },
    manual_parameters=[
        openapi.Parameter(
            "post_id",
            openapi.IN_PATH,
            description="조회할 게시글의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['GET'])
def post_detail_view(request, post_id):
    """
    게시글 상세 조회 API
    - 게시글의 상세 정보, 작성자 정보, 댓글 목록 등을 반환합니다.
    - 댓글 목록은 페이지네이션이 적용됩니다.
    """
    # 게시글 조회
    post = get_object_or_404(Post.objects.annotate(
        like_count=Count('liked_posts_by_users'),  # 게시글 좋아요 수
        comment_count=Count('post_comments')  # 게시글에 달린 댓글 수
    ), id=post_id)

    # 댓글 목록 조회 및 페이지네이션 적용
    comments = Comment.objects.filter(post=post).annotate(
    annotated_like_count=Count('likes'),  # 이름 변경
    annotated_dislike_count=Count('dislikes')  # 이름 변경
).order_by('-created_at')

    paginator = CommentPagination()
    paginated_comments = paginator.paginate_queryset(comments, request)

    # 직렬화
    serializer = PostDetailSerializer(post, context={
        "request": request,
        "comments": paginated_comments  # 페이지네이션된 댓글 전달
    })
    return paginator.get_paginated_response(serializer.data)




# 자유게시판 게시글 - 좋아요/취소 토글

@swagger_auto_schema(
    method='post',
    operation_summary="게시글 좋아요/취소 토글",
    operation_description="게시글의 좋아요 상태를 반전시킵니다.",
    responses={
        200: openapi.Response(
            description="좋아요 상태 변경 성공",
            examples={
                "application/json": {
                    "message": "좋아요 상태가 변경되었습니다.",
                    "liked": True,
                    "like_count": 15
                }
            }
        ),
        401: openapi.Response(
            description="로그인이 필요합니다.",
            examples={"application/json": {"message": "로그인이 필요합니다."}}
        ),
        404: openapi.Response(description="게시글을 찾을 수 없습니다.")
    },
    manual_parameters=[
        openapi.Parameter(
            "post_id",
            openapi.IN_PATH,
            description="좋아요를 토글할 게시글의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['POST'])
def post_like_toggle_view(request, post_id):
    """
    게시글 좋아요/취소 토글 API
    """
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if user.is_authenticated:
        if post in user.liked_posts.all():
            user.liked_posts.remove(post)  # 좋아요 취소
            liked = False
        else:
            user.liked_posts.add(post)  # 좋아요 추가
            liked = True

            # 좋아요 알림 생성
            if post.user != user:  # 자기 자신에게는 알림 X
                create_notification(
                    user=post.user,
                    content=f"'{user.username}'님이 게시글을 좋아합니다.",
                    type='like',
                    instance=post
                )

        return Response({
            "message": "좋아요 상태가 변경되었습니다.",
            "liked": liked,
            "like_count": post.liked_posts_by_users.count()
        }, status=200)
    return Response({"message": "로그인이 필요합니다."}, status=401)

'''
AHS 버그 픽스
'''
from .serializers import ReviewValidSerializer 
# 게시글 생성 수정 삭제
@api_view(['GET'])
def user_reviews_view(request):
    # 현재 로그인된 사용자를 기준으로 리뷰 필터링!!!

    user = request.user  # user 객체 직접 사용

    # 현재 사용자가 작성한 리뷰 필터링
    reviews = Review.objects.filter(user=user)

    # 리뷰가 없는 경우 빈 배열 반환
    if not reviews.exists():
        return Response([], status=status.HTTP_200_OK)

    # 영화가 연결된 리뷰만 필터링하여 직렬화
    reviews_with_movies = reviews.filter(movie__isnull=False)

    serializer = ReviewSerializer(reviews_with_movies, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# 게시글 생성 - 알림 트리거 생성
@swagger_auto_schema(
    method='post',
    operation_summary="게시글 생성",
    operation_description=(
        "새로운 게시글을 생성합니다. "
        "팔로워들에게 알림이 전송됩니다."
    ),
    request_body=PostSerializer,
    responses={
        201: openapi.Response(
            description="게시글 생성 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "새로운 게시글 제목",
                    "content": "게시글 내용입니다."
                }
            }
        ),
        400: openapi.Response(
            description="유효하지 않은 데이터",
            examples={
                "application/json": {
                    "message": "데이터 형식이 잘못되었습니다."
                }
            }
        )
    }
)
@api_view(['POST'])
def create_post_view(request):
    """
    게시글 생성 API
    """
    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        post = serializer.save(user=request.user)  # 게시글 생성

        # 팔로워들에게 알림 생성
        followers = request.user.followers.all()
        for follower in followers:
            create_notification(
                user=follower,
                content=f"'{request.user.username}'님이 새로운 게시글을 작성했습니다.",
                type='follow',
                instance=post
            )

        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)




# 게시글 수정
@swagger_auto_schema(
    method='patch',
    operation_summary="게시글 수정",
    operation_description="특정 게시글의 일부 내용을 수정합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="수정할 게시글 제목 (선택 입력 가능)"
            ),
            "content": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="수정할 게시글 내용 (선택 입력 가능)"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="게시글 수정 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "수정된 게시글 제목",
                    "content": "수정된 게시글 내용"
                }
            }
        ),
        400: openapi.Response(
            description="잘못된 요청 데이터",
            examples={
                "application/json": {
                    "message": "잘못된 데이터입니다."
                }
            }
        ),
        403: openapi.Response(
            description="수정 권한 없음",
            examples={
                "application/json": {
                    "message": "수정 권한이 없습니다."
                }
            }
        ),
        404: openapi.Response(
            description="게시글을 찾을 수 없음",
            examples={
                "application/json": {
                    "message": "게시글을 찾을 수 없습니다."
                }
            }
        )
    },
    manual_parameters=[
        openapi.Parameter(
            "post_id",
            openapi.IN_PATH,
            description="수정할 게시글 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['PATCH'])
def update_post_view(request, post_id):
    """
    게시글 수정 API
    - 게시글의 일부 내용을 수정합니다.
    """
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return Response({"message": "수정 권한이 없습니다."}, status=403)

    serializer = PostSerializer(post, data=request.data, partial=True)  # PATCH: partial=True
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)









# 게시글 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="게시글 삭제",
    operation_description="특정 게시글을 삭제합니다.",
    responses={
        200: openapi.Response(
            description="게시글 삭제 성공",
            examples={"application/json": {"message": "게시글이 삭제되었습니다."}}
        ),
        403: openapi.Response(description="삭제 권한이 없습니다."),
        404: openapi.Response(description="게시글을 찾을 수 없습니다.")
    },
    manual_parameters=[
        openapi.Parameter(
            "post_id",
            openapi.IN_PATH,
            description="삭제할 게시글의 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['DELETE'])
def delete_post_view(request, post_id):
    """
    게시글 삭제 API
    """
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return Response({"message": "삭제 권한이 없습니다."}, status=403)

    post.delete()
    return Response({"message": "게시글이 삭제되었습니다."}, status=200)




# ----------------------------------------------- 리뷰 게시판-------------------------------

# 리뷰게시판 게시글 - 목록 뷰
from .serializers import ReviewSerializer
@swagger_auto_schema(
    method='get',
    operation_summary="리뷰 목록 조회",
    operation_description="""
    검색 조건 및 정렬 조건을 기반으로 리뷰 목록을 조회합니다.
    페이지네이션을 지원하며, 좋아요 수 및 댓글 수와 함께 반환됩니다.
    """,
    manual_parameters=[
        openapi.Parameter(
            'query', openapi.IN_QUERY,
            description="검색어 (작성자, 제목, 내용 등)",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'search_type', openapi.IN_QUERY,
            description="검색 조건: author(작성자), title(제목), title_content(제목+내용), title_content_comment(제목+내용+댓글)",
            type=openapi.TYPE_STRING,
            enum=["author", "title", "title_content", "title_content_comment"],
            default="title"
        ),
        openapi.Parameter(
            'sort', openapi.IN_QUERY,
            description="정렬 조건: created_at_desc(최신순), created_at_asc(오래된 순), comments_desc(댓글 많은 순), likes_desc(좋아요 많은 순), rating_desc(별점 높은 순), rating_asc(별점 낮은 순)",
            type=openapi.TYPE_STRING,
            enum=["created_at_desc", "created_at_asc", "comments_desc", "likes_desc", "rating_desc", "rating_asc"],
            default="created_at_desc"
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="페이지 번호 (기본값: 1)",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY,
            description="페이지 크기 (기본값: 10, 최대값: 100)",
            type=openapi.TYPE_INTEGER,
            default=10
        ),
    ],
    responses={
        200: openapi.Response(
            description="리뷰 목록 반환 성공",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="전체 리뷰 개수",
                        example=50
                    ),
                    "next": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="다음 페이지 URL (없을 경우 null)",
                        example="http://example.com/community/reviews/?page=2"
                    ),
                    "previous": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="이전 페이지 URL (없을 경우 null)",
                        example=None
                    ),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="리뷰 ID",
                                    example=1
                                ),
                                "title": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="리뷰 제목",
                                    example="Inception 리뷰"
                                ),
                                "content": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="리뷰 내용",
                                    example="영화 정말 최고였습니다!"
                                ),
                                "rating": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="별점 (1~5)",
                                    example=5
                                ),
                                "created_at": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="작성일",
                                    example="2024-11-20T14:32:00Z"
                                ),
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="작성자 ID",
                                            example=101
                                        ),
                                        "username": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="작성자 이름",
                                            example="리뷰작성자"
                                        ),
                                        "profile_image": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="작성자 프로필 이미지 URL",
                                            example="https://example.com/user1.jpg"
                                        )
                                    }
                                ),
                                "like_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="좋아요 수",
                                    example=20
                                ),
                                "comment_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="댓글 수",
                                    example=5
                                )
                            }
                        )
                    )
                }
            )
        ),
        400: openapi.Response(
            description="잘못된 요청",
            examples={
                "application/json": {"detail": "Invalid parameters."}
            }
        ),
        500: openapi.Response(
            description="서버 오류",
            examples={
                "application/json": {"detail": "Internal server error."}
            }
        )
    }
)
@api_view(['GET'])
def review_list_view(request):
    """
    리뷰 목록 API
    - 검색 조건 및 정렬 조건을 기반으로 리뷰 목록을 반환
    - 페이지네이션 적용
    """
    query = request.GET.get('query', '')  # 검색어
    search_type = request.GET.get('search_type', 'title')  # 검색 조건
    sort = request.GET.get('sort', 'created_at_desc')  # 정렬 조건

    # 기본 QuerySet
    reviews = Review.objects.annotate(
        comment_count=Count('review_comments')  # 댓글 수
    )

    # 검색 조건 적용
    if query:
        if search_type == 'author':
            reviews = reviews.filter(user__username__icontains=query)
        elif search_type == 'title':
            reviews = reviews.filter(title__icontains=query)
        elif search_type == 'title_content':
            reviews = reviews.filter(Q(title__icontains=query) | Q(content__icontains=query))
        elif search_type == 'title_content_comment':
            reviews = reviews.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(review_comments__content__icontains=query)
            ).distinct()

    # 정렬 조건 적용
    if sort == 'created_at_desc':
        reviews = reviews.order_by('-created_at')
    elif sort == 'created_at_asc':
        reviews = reviews.order_by('created_at')
    elif sort == 'comments_desc':
        reviews = reviews.order_by('-comment_count')
    elif sort == 'likes_desc':
        reviews = reviews.annotate(like_count=Count('liked_reviews_by_users')).order_by('-like_count')
    elif sort == 'rating_desc':
        reviews = reviews.order_by('-rating')
    elif sort == 'rating_asc':
        reviews = reviews.order_by('rating')

    # 페이지네이션 처리
    paginator = CustomPagination()
    paginated_reviews = paginator.paginate_queryset(reviews, request)

    # 데이터 직렬화 및 응답 반환
    serializer = ReviewSerializer(paginated_reviews, many=True)
    return paginator.get_paginated_response(serializer.data)


# 리뷰게시판 게시글 - 상세 뷰 
'''
11-24 AHS 수정
'''
from .serializers import ReviewDetailSerializer
@swagger_auto_schema(
    method='get',
    operation_summary="리뷰 상세 조회",
    operation_description="리뷰의 상세 정보를 조회합니다. 댓글 목록은 페이지네이션이 적용되어 반환됩니다.",
    responses={
        200: openapi.Response(
            description="리뷰 상세 조회 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "영화 리뷰 제목",
                    "content": "영화 리뷰 내용입니다.",
                    "rating": 5,
                    "created_at": "2024-11-20T12:00:00Z",
                    "updated_at": "2024-11-20T13:00:00Z",
                    "like_count": 25,
                    "is_liked": True,
                    "user": {
                        "id": 1,
                        "username": "리뷰작성자",
                        "profile_image": "https://example.com/profile.jpg",
                        "profile_url": "/accounts/users/1/liked-movies/"
                    },
                    "movie": {
                        "id": 10,
                        "title": "Inception",
                        "poster_path": "https://example.com/poster.jpg",
                        "movie_url": "/movies/10/cast-and-crews/"
                    },
                    "comments": [
                        {
                            "id": 1,
                            "content": "첫 번째 댓글입니다.",
                            "user": {
                                "id": 2,
                                "username": "댓글작성자",
                                "profile_image": "https://example.com/user2.jpg"
                            },
                            "like_count": 5,
                            "dislike_count": 0,
                            "created_at": "2024-11-20T12:30:00Z"
                        },
                        {
                            "id": 2,
                            "content": "두 번째 댓글입니다.",
                            "user": {
                                "id": 3,
                                "username": "댓글작성자2",
                                "profile_image": "https://example.com/user3.jpg"
                            },
                            "like_count": 3,
                            "dislike_count": 1,
                            "created_at": "2024-11-20T12:45:00Z"
                        }
                    ]
                }
            }
        ),
        404: openapi.Response(description="리뷰를 찾을 수 없음"),
    },
    manual_parameters=[
        openapi.Parameter(
            "review_id",
            openapi.IN_PATH,
            description="리뷰 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="댓글 페이지 번호 (기본값: 1)",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
    ]
)
@api_view(['GET'])
def review_detail_view(request, review_id):
    """
    리뷰 상세 조회 API
    - 리뷰의 상세 정보, 작성자 정보, 영화 정보, 댓글 목록을 반환합니다.
    - 댓글 목록은 페이지네이션이 적용됩니다.
    """
    # 리뷰 객체 가져오기
    try:
        review = Review.objects.annotate(
            like_count=Count('liked_reviews_by_users')  # 리뷰 좋아요 수 계산
        ).get(id=review_id)
    except Review.DoesNotExist:
        raise NotFound({"message": "리뷰를 찾을 수 없습니다."})

    # 댓글 목록 조회
    comments = Comment.objects.filter(review=review).select_related('user').prefetch_related('likes', 'dislikes').order_by('-created_at')

    # 페이지네이션 적용
    paginator = CommentPagination()
    paginated_comments = paginator.paginate_queryset(comments, request)

    # 댓글 직렬화
    comment_serializer = CommentSerializer(paginated_comments, many=True, context={"request": request})

    # 응답 데이터 구성
    response_data = {
        "id": review.id,
        "title": review.title,
        "content": review.content,
        "rating": review.rating,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
        "like_count": review.like_count,
        "is_liked": review.liked_reviews_by_users.filter(id=request.user.id).exists() if request.user.is_authenticated else False,
        "user": {
            "id": review.user.id,
            "username": review.user.username,
            "profile_image": review.user.profile_image.url if review.user.profile_image else None
        },
        "movie": {
            "id": review.movie.id if review.movie else None,
            "title": review.movie.title if review.movie else "No Movie",
            "poster_path": review.movie.poster_path if review.movie and review.movie.poster_path else "/default-poster.jpg",
            "movie_url": f"/movies/{review.movie.id}/cast-and-crews/" if review.movie else None,
        },
        "comments": comment_serializer.data  # 직렬화된 댓글 데이터 포함
    }

    # 페이지네이션 응답 반환
    return paginator.get_paginated_response(response_data)



# 리뷰게시판 게시글 - 좋아요/취소 토글
@swagger_auto_schema(
    method='post',
    operation_summary="리뷰 좋아요/취소 토글",
    operation_description="특정 리뷰의 좋아요 상태를 토글합니다.",
    responses={
        200: openapi.Response(
            description="토글 성공",
            examples={
                "application/json": {
                    "message": "좋아요 상태가 변경되었습니다.",
                    "liked": True,
                    "like_count": 10
                }
            }
        ),
        401: openapi.Response(description="로그인이 필요합니다."),
        404: openapi.Response(description="리뷰를 찾을 수 없습니다.")
    },
    manual_parameters=[
        openapi.Parameter(
            "review_id",
            openapi.IN_PATH,
            description="좋아요를 토글할 리뷰 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['POST'])
def review_like_toggle_view(request, review_id):
    """
    리뷰 좋아요/취소 토글 API
    """
    review = get_object_or_404(Review, id=review_id)
    user = request.user

    if user.is_authenticated:
        if review in user.liked_reviews.all():
            user.liked_reviews.remove(review)  # 좋아요 취소
            liked = False
        else:
            user.liked_reviews.add(review)  # 좋아요 추가
            liked = True

            # 좋아요 알림 생성
            if review.user != user:  # 자기 자신에게는 알림 X
                create_notification(
                    user=review.user,
                    content=f"'{user.username}'님이 리뷰를 좋아합니다.",
                    type='like',
                    instance=review
                )

        return Response({
            "message": "좋아요 상태가 변경되었습니다.",
            "liked": liked,
            "like_count": review.liked_reviews_by_users.count()
        }, status=200)
    return Response({"message": "로그인이 필요합니다."}, status=401)


'''
AHS 기능 개선
'''
# 리뷰 생성 수정 삭제
from .serializers import ReviewSerializer
from .serializers import ReviewCreateSerializer
from django.http import JsonResponse
import json
# 리뷰 생성
@swagger_auto_schema(
    method='post',
    operation_summary="리뷰 생성",
    operation_description="새로운 리뷰를 생성합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING, description="리뷰 제목"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, description="리뷰 내용"),
            "rating": openapi.Schema(type=openapi.TYPE_INTEGER, description="별점 (1~5)", example=5),
            "movie": openapi.Schema(type=openapi.TYPE_INTEGER, description="리뷰 대상 영화 ID", example=1)
        },
        required=["title", "content", "rating"]
    ),
    responses={
        201: openapi.Response(
            description="리뷰 생성 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "영화 리뷰 제목",
                    "content": "영화 내용입니다.",
                    "rating": 5,
                    "movie": {"id": 1, "title": "Inception"}
                }
            }
        ),
        400: openapi.Response(description="잘못된 요청 데이터")
    }
)
@api_view(['POST'])
def create_review_view(request):
    if request.method == "POST":
        try:
            # 요청 데이터 로깅
            data = json.loads(request.body)
            print("요청 데이터:", data)
        except json.JSONDecodeError:
            return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 검증 오류 로깅
            print("검증 오류:", serializer.errors)
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'error': '잘못된 요청 방식입니다.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



from .serializers import ReviewMovieSerializer

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomReviewPagination(PageNumberPagination):
    page_size = 10  # 기본 페이지 크기
    page_size_query_param = 'page_size'  # 클라이언트에서 페이지 크기를 요청에 포함할 수 있음
    max_page_size = 100  # 최대 페이지 크기 제한


'''
AHS 페이지네이션 방식 변화
'''
@api_view(['GET'])
def review_movie_list_view(request):
    """
    리뷰 작성용 영화 전체 목록 API
    """
    # 모든 영화 데이터 반환
    movies = Movie.objects.distinct()

    # 직렬화
    serializer = ReviewMovieSerializer(movies, many=True)
    return Response(serializer.data)




# 리뷰 수정
@swagger_auto_schema(
    method='patch',
    operation_summary="리뷰 수정",
    operation_description="특정 리뷰의 일부 또는 전체 내용을 수정합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="수정할 리뷰 제목"
            ),
            "content": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="수정할 리뷰 내용"
            ),
            "rating": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="수정할 별점 (1~5)",
                example=4
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="리뷰 수정 성공",
            examples={
                "application/json": {
                    "id": 1,
                    "title": "수정된 리뷰 제목",
                    "content": "수정된 리뷰 내용",
                    "rating": 4
                }
            }
        ),
        400: openapi.Response(
            description="잘못된 요청 데이터",
            examples={
                "application/json": {
                    "message": "잘못된 데이터입니다."
                }
            }
        ),
        403: openapi.Response(
            description="수정 권한 없음",
            examples={
                "application/json": {
                    "message": "수정 권한이 없습니다."
                }
            }
        ),
        404: openapi.Response(
            description="리뷰를 찾을 수 없음",
            examples={
                "application/json": {
                    "message": "리뷰를 찾을 수 없습니다."
                }
            }
        )
    },
    manual_parameters=[
        openapi.Parameter(
            "review_id",
            openapi.IN_PATH,
            description="수정할 리뷰 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['PATCH'])
def update_review_view(request, review_id):
    """
    리뷰 수정 API
    - 리뷰의 일부 또는 전체 내용을 수정합니다.
    """
    review = get_object_or_404(Review, id=review_id)
    if review.user != request.user:
        return Response({"message": "수정 권한이 없습니다."}, status=403)

    serializer = ReviewSerializer(review, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)




# 리뷰 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="리뷰 삭제",
    operation_description="특정 리뷰를 삭제합니다.",
    responses={
        200: openapi.Response(description="리뷰 삭제 성공"),
        403: openapi.Response(description="삭제 권한 없음"),
        404: openapi.Response(description="리뷰를 찾을 수 없음")
    },
    manual_parameters=[
        openapi.Parameter(
            "review_id",
            openapi.IN_PATH,
            description="삭제할 리뷰 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['DELETE'])
def delete_review_view(request, review_id):
    """
    리뷰 삭제 API
    """
    review = get_object_or_404(Review, id=review_id)
    if review.user != request.user:
        return Response({"message": "삭제 권한이 없습니다."}, status=403)

    review.delete()
    return Response({"message": "리뷰가 삭제되었습니다."}, status=200)



# ----------------------------------------댓글------------------------------------------------

# 댓글 작성 - 알림 트리거 -> 11-23 AHS
def validate_parent_relationship(parent_comment, parent_object):
    """
    부모 댓글과 게시글/리뷰의 관계 검증
    """
    if parent_comment.post != parent_object and parent_comment.review != parent_object:
        raise ValueError("부모 댓글이 지정된 게시글 또는 리뷰와 연결되어 있지 않습니다.")

# 댓글 작성 - 알림 트리거 -> 11-23 AHS 수정
@swagger_auto_schema(
    method='post',
    operation_summary="댓글/대댓글 작성",
    operation_description=(
        "게시글 또는 리뷰에 댓글을 작성하거나, "
        "기존 댓글에 대댓글을 작성합니다. "
        "작성 시 관련 사용자에게 알림이 생성됩니다."
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "content": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="댓글 내용"
            ),
            "parent_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="부모 댓글 ID (대댓글인 경우)",
                example=5,
                nullable=True
            ),
        },
        required=["content"]
    ),
    responses={
        201: openapi.Response(
            description="댓글 작성 성공",
            examples={
                "application/json": {
                    "message": "댓글이 작성되었습니다.",
                    "comment_id": 10,
                    "content": "댓글 내용입니다.",
                    "parent_id": 5
                }
            }
        ),
        400: openapi.Response(
            description="요청 데이터 오류",
            examples={
                "application/json": {
                    "message": "댓글 내용을 입력해주세요."
                }
            }
        ),
        404: openapi.Response(
            description="게시글/리뷰 또는 부모 댓글을 찾을 수 없습니다."
        ),
    }
)
@api_view(['POST'])
def create_comment_view(request, review_id=None, post_id=None):
    parent_object = None
    if review_id:
        parent_object = get_object_or_404(Review, id=review_id)
    elif post_id:
        parent_object = get_object_or_404(Post, id=post_id)
    else:
        return Response({"message": "게시글 ID 또는 리뷰 ID를 제공해야 합니다."}, status=400)

    content = request.data.get("content")
    parent_id = request.data.get("parent")  # 요청에서 "parent" 사용

    if not content:
        return Response({"message": "댓글 내용을 입력해주세요."}, status=400)

    parent_comment = None
    if parent_id:
        parent_comment = get_object_or_404(Comment, id=parent_id)

    comment = Comment.objects.create(
        user=request.user,
        post=parent_object if post_id else None,
        review=parent_object if review_id else None,
        content=content.strip(),
        parent=parent_comment
    )

    return Response({
        "message": "댓글이 작성되었습니다.",
        "comment_id": comment.id,
        "content": comment.content,
        "parent": comment.parent.id if comment.parent else None  # 응답에서도 "parent" 사용
    }, status=201)



def create_comment_notifications(author, parent_object, parent_comment, comment):
    """
    댓글 작성 알림 생성
    """
    # 댓글 작성 알림 (게시글 또는 리뷰)
    if isinstance(parent_object, Post):
        create_notification(
            user=parent_object.user,
            content=f"'{author.username}'님이 게시글에 댓글을 작성했습니다.",
            type='comment',
            instance=comment
        )
    elif isinstance(parent_object, Review):
        create_notification(
            user=parent_object.user,
            content=f"'{author.username}'님이 리뷰에 댓글을 작성했습니다.",
            type='comment',
            instance=comment
        )

    # 대댓글 작성 알림
    if parent_comment and parent_comment.user != author:
        create_notification(
            user=parent_comment.user,
            content=f"'{author.username}'님이 당신의 댓글에 답글을 작성했습니다.",
            type='reply',
            instance=comment
        )



# 댓글 수정
@swagger_auto_schema(
    method='patch',
    operation_summary="댓글 수정",
    operation_description="특정 댓글의 내용을 수정합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "content": openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="수정할 댓글 내용"
            )
        },
        required=["content"]
    ),
    responses={
        200: openapi.Response(
            description="댓글 수정 성공",
            examples={
                "application/json": {
                    "message": "댓글이 수정되었습니다.",
                    "content": "수정된 댓글 내용"
                }
            }
        ),
        400: openapi.Response(
            description="잘못된 요청 데이터",
            examples={
                "application/json": {"message": "댓글 내용을 입력해주세요."}
            }
        ),
        403: openapi.Response(
            description="수정 권한 없음",
            examples={
                "application/json": {"message": "수정 권한이 없습니다."}
            }
        ),
        404: openapi.Response(
            description="댓글을 찾을 수 없음",
            examples={
                "application/json": {"message": "댓글을 찾을 수 없습니다."}
            }
        )
    },
    manual_parameters=[
        openapi.Parameter(
            "comment_id",
            openapi.IN_PATH,
            description="수정할 댓글 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['PATCH'])
def update_comment_view(request, comment_id):
    """
    댓글 수정 API
    - 댓글 또는 대댓글 내용을 수정합니다.
    """
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return Response({"message": "수정 권한이 없습니다."}, status=403)

    content = request.data.get('content')
    if not content:
        return Response({"message": "댓글 내용을 입력해주세요."}, status=400)

    comment.content = content
    comment.save()

    return Response({"message": "댓글이 수정되었습니다.", "content": comment.content}, status=200)


# 댓글 삭제
@swagger_auto_schema(
    method='delete',
    operation_summary="댓글 삭제",
    operation_description="특정 댓글을 삭제합니다.",
    responses={
        200: openapi.Response(description="댓글 삭제 성공"),
        403: openapi.Response(description="삭제 권한 없음"),
        404: openapi.Response(description="댓글을 찾을 수 없음")
    },
    manual_parameters=[
        openapi.Parameter(
            "comment_id",
            openapi.IN_PATH,
            description="삭제할 댓글 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['DELETE'])
def delete_comment_view(request, comment_id):
    """
    댓글 삭제 API
    - 댓글 또는 대댓글을 삭제합니다.
    """
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return Response({"message": "삭제 권한이 없습니다."}, status=403)

    comment.delete()
    return Response({"message": "댓글이 삭제되었습니다."}, status=200)




# 하단은 댓글 좋아요 관련


# 댓글 좋아요 토글
@swagger_auto_schema(
    method='post',
    operation_summary="댓글 좋아요 토글",
    operation_description="댓글에 대해 좋아요를 토글합니다. 현재 상태에 따라 좋아요를 추가하거나 취소합니다.",
    responses={
        200: openapi.Response(
            description="좋아요 상태 변경 성공",
            examples={
                "application/json": {
                    "message": "댓글 좋아요 상태가 변경되었습니다.",
                    "liked": True,
                    "like_count": 10,
                    "dislike_count": 2
                }
            }
        ),
        401: openapi.Response(
            description="로그인이 필요합니다.",
            examples={"application/json": {"message": "로그인이 필요합니다."}}
        ),
        404: openapi.Response(description="댓글을 찾을 수 없습니다."),
    },
    manual_parameters=[
        openapi.Parameter(
            "comment_id",
            openapi.IN_PATH,
            description="좋아요를 토글할 댓글 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['POST'])
def toggle_comment_like_view(request, comment_id):
    """
    댓글 좋아요/취소 토글 API
    """
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    if user.is_authenticated:
        if comment.likes.filter(id=user.id).exists():
            comment.likes.remove(user)  # 좋아요 취소
            liked = False
        else:
            comment.likes.add(user)  # 좋아요 추가
            liked = True

            # 좋아요 알림 생성
            if comment.user != user:  # 자기 자신에게는 알림 X
                create_notification(
                    user=comment.user,
                    content=f"'{user.username}'님이 댓글을 좋아합니다.",
                    type='like',
                    instance=comment
                )

        return Response({
            "message": "좋아요 상태가 변경되었습니다.",
            "liked": liked,
            "like_count": comment.likes.count()
        }, status=200)
    return Response({"message": "로그인이 필요합니다."}, status=401)


# 댓글 싫어요 토글
@swagger_auto_schema(
    method='post',
    operation_summary="댓글 싫어요 토글",
    operation_description="댓글에 대해 싫어요를 토글합니다. 현재 상태에 따라 싫어요를 추가하거나 취소합니다.",
    responses={
        200: openapi.Response(
            description="싫어요 상태 변경 성공",
            examples={
                "application/json": {
                    "message": "댓글 싫어요 상태가 변경되었습니다.",
                    "disliked": True,
                    "like_count": 10,
                    "dislike_count": 2
                }
            }
        ),
        401: openapi.Response(
            description="로그인이 필요합니다.",
            examples={"application/json": {"message": "로그인이 필요합니다."}}
        ),
        404: openapi.Response(description="댓글을 찾을 수 없습니다."),
    },
    manual_parameters=[
        openapi.Parameter(
            "comment_id",
            openapi.IN_PATH,
            description="싫어요를 토글할 댓글 ID",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ]
)
@api_view(['POST'])
def toggle_comment_dislike_view(request, comment_id):
    """
    댓글 싫어요 토글 API
    - 싫어요 상태를 토글합니다.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    if not user.is_authenticated:
        return Response({"message": "로그인이 필요합니다."}, status=401)

    if user in comment.dislikes.all():
        comment.dislikes.remove(user)
        disliked = False
        message = "댓글 싫어요를 취소했습니다."
    else:
        comment.dislikes.add(user)
        comment.likes.remove(user)  # 좋아요 제거
        disliked = True
        message = "댓글 싫어요를 눌렀습니다."

    return Response({
        "message": message,
        "disliked": disliked,
        "like_count": comment.likes.count(),
        "dislike_count": comment.dislikes.count()
    }, status=200)
