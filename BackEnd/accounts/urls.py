from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'follow', views.FollowViewSet, basename='follow')

app_name = 'accounts'


'''
24.11.23. 03:19 AHS
개별알림읽음 토글 url 패턴 -> 기존에 id를 파라미터로 안주던 문제 수정
정상 작동 확인

구글로그인
유저 프로필
수정
관리자
유저 부활
'''





urlpatterns = [
    
    
    # 구글 로그인
    path('google-login/', views.google_login_view, name='google-login'),  

    
    # 유저 프로필 - 통합 - 테스트 완료
    path('users/<int:user_id>/profile/', views.user_profile_view, name='user-profile'),
    
    # 유저 프로필 - 좋아하는 영화 탭
    path('users/<int:user_id>/liked-movies/', views.user_liked_movies_view, name='user-liked-movies'),

    # 유저 프로필 - 좋아하는 인물 탭 (배우/감독)
    path('users/<int:user_id>/liked-people/', views.user_liked_people_view, name='user-liked-people'),

    # 유저 프로필 - 활동 탭 (리뷰, 댓글, 게시글)
    path('users/<int:user_id>/activity/', views.user_profile_activity_view, name='user_profile_activity'),

    # 유저 프로필 - Social 탭 (팔로워/팔로잉/맞팔로우)
    path('users/<int:user_id>/social/', views.user_social_tab_view, name='user_social_tab'),



    # 유저 프로필 - Social 탭에서 팔로워/팔로잉/맞팔로우 삭제
    path('users/<int:user_id>/social/delete/', views.user_social_tab_delete_view, name='user_social_tab_delete'),

    # 유저 팔로우/언팔로우 토글
    path('users/<int:user_id>/follow/', views.toggle_follow_view, name='toggle-follow'),




    # 유저 프로필 수정 창 읽기 및 수정
    path('users/me/edit-profile/', views.edit_user_profile_view, name='user-profile-read'),
    path('users/me/edit-profile/update/', views.save_user_profile_and_redirect, name='user-profile-update'),




    # 관리자 대시보드
    path('admin/dashboard/', views.admin_dashboard_view, name='admin-dashboard'),
    path('admin/movies/', views.admin_movie_list_view, name='admin-movie-list'),
    path('admin/users/', views.admin_user_list_view, name='admin-user-list'),
    path('admin/reviews/', views.admin_review_list_view, name='admin-review-list'),

    # 관리자 객체 삭제
    
    path('admin/movies/delete/', views.admin_movie_delete_view, name='admin_movie_delete_view'),
    path('admin/users/delete/', views.admin_user_delete_view, name='admin_user_delete_view'),
    path('admin/reviews/delete/', views.admin_review_delete_view, name='admin_review_delete_view'),

    # 유저 부활
    path('admin/users/restore/', views.admin_user_restore_view, name='admin_user_restore_view'),




    # 알림 목록
    path('notifications/', views.get_notifications_view, name='get_notifications'),
    path('notifications/mark-all-read/', views.mark_all_as_read, name='mark-all-read'),
    path('notifications/mark-all-unread/', views.mark_all_as_unread, name='mark-all-unread'),
    path('notifications/toggle_notification_read_status/<int:notification_id>/', views.toggle_notification_read_status, name='toggle_notification_read_status'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete-all-notifications'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete-notification'),


]
