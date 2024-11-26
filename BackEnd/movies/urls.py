from django.urls import path
from . import views

app_name = 'movies'

'''
11-24 07:20 AHS 추천알고리즘 추가

1. 사용자 정보 기반 추천
2. 사용자 입력 키워드 기반 추천

'''

urlpatterns = [
    

    
    # movie, actor, director, genre 정보 전부 DB에 저장
    path('fetch-movies/', views.fetch_popular_movies_and_credits, name='fetch_movies'),
    # 배우 및 감독의 biography만 업데이트 (ko-KR 우선, 없는 거는 en-US로 한 번 더)
    path('update-biography/', views.update_biography_for_all_movies, name='update_biography'),
    # 영화 overview 필드 업데이트 (ko-KR 우선, 없는 거는 en-US로 한 번 더)
    path('update-overview/', views.update_overview_for_all_movies, name='update_overview'),
    # 모든 뉴스 정보 저장
    path('fetch-all-news/', views.fetch_news_for_all_movies, name='fetch_all_news'),
    # 모든 이미지 path에 대해 전체 경로로 변경 - > 나중에 한 번에 합시다.
    
    # --------------------------------------------------------------------------------------------
    
    # 영화 리스트 조회(검색, 필터링 다 프론트)
    path('', views.movie_list_view, name='movie_list_view'),
    # 통합검색(배우, 감독, 유저)
    path('search/', views.SearchDataView.as_view(), name='search_data'),
    
    # 영화 추천 엔드포인트 : 11-24 AHS
    path('recommendations_view', views.recommendations_view, name='recommendations_view'),
    

    # --------------------------------------------------------------------------------------------
    # Cast & Crews 탭
    path('<int:movie_id>/', views.unified_movie_detail_view, name='unified_movie_detail'),

    # 영화 좋아요/좋아요 취소 경로
    path('<int:movie_id>/like/', views.like_movie_view, name='like_movie'),
    
    # Trailer 탭
    # path('<int:movie_id>/trailer/', views.movie_trailer_view, name='movie_trailer'),

    # Related 탭
    # path('<int:movie_id>/related/', views.movie_related_view, name='movie_related'),

    # 영화 댓글 작성
    path('<int:movie_id>/comments/', views.movie_comment_create_view, name='movie_comment_create'),
    
    # 영화 댓글 수정
    path('<int:movie_id>/comments/<int:comment_id>/update/', views.movie_comment_update_view, name='movie_comment_update'),
    
    # 영화 댓글 삭제
    path('<int:movie_id>/comments/<int:comment_id>/delete/', views.movie_comment_delete_view, name='movie_comment_delete'),
# -------------------------------------------------------------------------------------------

    # 배우 상세 정보 조회
    path('actors/<int:actor_id>/', views.actor_detail_view, name='actor_detail'),
    
    # 배우 좋아요 토글
    path('actors/<int:actor_id>/like/', views.actor_toggle_like_view, name='actor_toggle_like'),

    # 배우 댓글 작성
    path('actors/<int:actor_id>/comments/', views.actor_comment_create_view, name='actor_comment_create'),

    # 배우 댓글 수정
    path('actors/<int:actor_id>/comments/<int:comment_id>/update/', views.actor_comment_update_view, name='actor_comment_update'),
    
    # 배우 댓글 삭제
    path('actors/<int:actor_id>/comments/<int:comment_id>/delete/', views.actor_comment_delete_view, name='actor_comment_delete'),

    # -------------------------------------------------------------------------------------------

   # 감독 상세 페이지
    path('directors/<int:director_id>/', views.director_detail_view, name='director_detail'),

    # 감독 좋아요 토글
    path('directors/<int:director_id>/like/', views.director_toggle_like_view, name='director_toggle_like'),

    # 감독 댓글 작성
    path('directors/<int:director_id>/comments/', views.director_comment_create_view, name='director_comment_create'),

    # 감독 댓글 수정
    path('directors/<int:director_id>/comments/<int:comment_id>/update/', views.director_comment_update_view, name='director_comment_update'),
    
    # 감독 댓글 삭제
    path('directors/<int:director_id>/comments/<int:comment_id>/delete/', views.director_comment_delete_view, name='director_comment_delete'),

    
]
