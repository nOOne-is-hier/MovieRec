from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from django.conf import settings
from django.conf.urls.static import static
# Swagger 문서화 설정
schema_view = get_schema_view(
    openapi.Info(
        title="MovieRec API",
        default_version='v1',
        description="MovieRec 프로젝트의 API 문서",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 앱별 URL 연결
    path('accounts/', include('accounts.urls')),  # Custom accounts app
    path('community/', include('community.urls')),  # 커뮤니티 기능
    path('movies/', include('movies.urls')),  # 영화 관련 기능

    # dj-rest-auth 관련 경로
    path('auth/', include('dj_rest_auth.urls')),  # 로그인, 로그아웃 등
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # 회원가입
    path('accounts/', include('allauth.urls')),  # Django Allauth URL 포함
    path('auth/password/reset/', include('dj_rest_auth.urls')),  # 비밀번호 재설정
    
    
    
    
    # JWT 관련 추가 엔드포인트
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # 토큰 발급
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # 토큰 갱신
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),  # 토큰 검증
    path('auth/token/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),  # 로그아웃 처리

    # Swagger 및 ReDoc 관련 엔드포인트
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
