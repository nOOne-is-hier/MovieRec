from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # 게시글 관련
    path('posts/', views.post_list_view, name='post-list'),  # 게시글 목록
    path('posts/<int:post_id>/', views.post_detail_view, name='post-detail'),  # 게시글 상세
    path('posts/<int:post_id>/like-toggle/', views.post_like_toggle_view, name='post-like-toggle'),  # 게시글 좋아요 토글
    path('posts/create/', views.create_post_view, name='create-post'),  # 게시글 생성
    path('posts/<int:post_id>/update/', views.update_post_view, name='update-post'),  # 게시글 수정
    path('posts/<int:post_id>/delete/', views.delete_post_view, name='delete-post'),  # 게시글 삭제
    path('posts/<int:post_id>/comments/', views.create_comment_view, name='create-post-comment'),  # 게시글 댓글 생성

    # 리뷰 관련
    path('reviews/', views.review_list_view, name='review-list'),  # 리뷰 목록
    path('reviews/<int:review_id>/', views.review_detail_view, name='review-detail'),  # 리뷰 상세
    path('reviews/<int:review_id>/like-toggle/', views.review_like_toggle_view, name='review-like-toggle'),  # 리뷰 좋아요 토글
    path('reviews/create/', views.create_review_view, name='create-review'),  # 리뷰 생성
    path('reviews/<int:review_id>/update/', views.update_review_view, name='update-review'),  # 리뷰 수정
    path('reviews/<int:review_id>/delete/', views.delete_review_view, name='delete-review'),  # 리뷰 삭제
    path('reviews/<int:review_id>/comments/', views.create_comment_view, name='create-review-comment'),  # 리뷰 댓글 생성
    path('review-movies/', views.review_movie_list_view, name='review-movie-list'),

    # 11-25:5:30
    # path('user-reviews/', views.user_reviews_view, name='user_reviews'),


    # 댓글 관련 (공통)
    path('comments/<int:comment_id>/update/', views.update_comment_view, name='update-comment'),  # 댓글 수정
    path('comments/<int:comment_id>/delete/', views.delete_comment_view, name='delete-comment'),  # 댓글 삭제
    path('comments/<int:comment_id>/like-toggle/', views.toggle_comment_like_view, name='comment-like-toggle'), # 좋아요 토글
    path('comments/<int:comment_id>/dislike-toggle/', views.toggle_comment_dislike_view, name='comment-dislike-toggle'), # 싫어요 토글


    # 추가 기능 (선택 사항)
    # path('reviews/<int:review_id>/report/', views.review_report_view, name='review-report'),  # 리뷰 신고
    # path('comments/<int:comment_id>/report/', views.review_comment_report_view, name='review-comment-report'),  # 댓글 신고
]
