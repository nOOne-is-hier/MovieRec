# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """
    사용자 생성 로직을 커스터마이징하여 이메일 필수화 및 초기값 설정.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    CustomUser 모델:
    - AbstractUser를 상속받아 기본 인증 필드(username, email, password)를 유지하면서 커스텀 필드 추가.
    """
    # 사용자 프로필 정보
    phone_number = models.CharField(
        max_length=15, unique=False, blank=True, null=True,
        help_text="사용자의 전화번호" # 전화번호 unique=False 설정
    )
    verification_code = models.IntegerField(
        null=True, blank=True, help_text="전화번호 인증 코드"
    )
    is_phone_verified = models.BooleanField(
        default=False, help_text="전화번호 인증 여부"
    )
    date_of_birth = models.DateField(
        blank=True, null=True, help_text="사용자의 생년월일"
    )
    bio = models.TextField(
        blank=True, null=True, help_text="사용자의 자기소개"
    )
    profile_image = models.ImageField(
        upload_to='media/', max_length=300, blank=True, null=True,
        default='default_profile.png',  # 기본 프로필 이미지 경로
        help_text="사용자 프로필 이미지"
    )

    # 시스템 필드
    deleted_at = models.DateTimeField(
        blank=True, null=True, help_text="소프트 삭제된 날짜"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="계정 생성 날짜"
    )
    unread_notifications_count = models.PositiveIntegerField(
        default=0, help_text="읽지 않은 알림 수"
    )

    # 관계 필드 (Many-to-Many)
    favorite_genres = models.ManyToManyField(
        'movies.Genre', related_name='favorite_genres_by_users', blank=True,
        help_text="사용자의 선호 장르 목록"
    )
    liked_movies = models.ManyToManyField(
        'movies.Movie', related_name='liked_movies_by_users', blank=True,
        help_text="사용자가 좋아요를 누른 영화 목록"
    )
    watched_movies = models.ManyToManyField(
        'movies.Movie', related_name='watched_by_users', blank=True,
        verbose_name="본 영화 목록", help_text="사용자가 시청한 영화 목록"
    )
    liked_posts = models.ManyToManyField(
        'community.Post', related_name='liked_posts_by_users', blank=True,
        help_text="사용자가 좋아요를 누른 게시글 목록"
    )
    liked_reviews = models.ManyToManyField(
        'community.Review', related_name='liked_reviews_by_users', blank=True,
        help_text="사용자가 좋아요를 누른 리뷰 목록"
    )
    following = models.ManyToManyField(
        'self', symmetrical=False, related_name='followers', blank=True,
        help_text="사용자가 팔로우하는 다른 사용자 목록"
    )
    favorite_actors = models.ManyToManyField(
        'movies.Actor', related_name='favorited_actors_by_users', blank=True,
        help_text="사용자가 즐겨찾기한 배우 목록"
    )
    favorite_directors = models.ManyToManyField(
        'movies.Director', related_name='favorited_directors_by_users', blank=True,
        help_text="사용자가 즐겨찾기한 감독 목록"
    )

    # 매니저
    objects = CustomUserManager()

    # 기본 인증 필드 설정
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    # 소프트 삭제 메서드
    def delete(self, *args, **kwargs):
        """
        소프트 삭제: deleted_at 필드에 현재 시간 기록.
        """
        self.deleted_at = timezone.now()
        self.save()

    @property
    def is_active(self):
        """
        계정 활성화 상태: deleted_at이 None이면 활성화 상태로 간주.
        """
        return self.deleted_at is None

    def __str__(self):
        return self.username



class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'Comment'),
        ('reply', 'Reply'),  # 대댓글
        ('like', 'Like'),
        ('follow', 'Follow'),
    ]
    
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='notifications',
        help_text="알림을 받을 사용자"
    )
    content = models.TextField(help_text="알림 내용")
    is_read = models.BooleanField(default=False, help_text="알림 읽음 여부")
    created_at = models.DateTimeField(auto_now_add=True, help_text="알림 생성 날짜")
    type = models.CharField(
        max_length=50, choices=NOTIFICATION_TYPES, help_text="알림 유형"
    )
    link = models.CharField(
        max_length=255, null=True, blank=True, help_text="알림 클릭 시 이동할 링크"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.content}"











































# # 1. User 모델 정의
# class CustomUserManager(BaseUserManager):
#     def create_user(self, username, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError('The Email field must be set')
#         email = self.normalize_email(email)
#         user = self.model(username=username, email=email, **extra_fields)
#         if password:
#             user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, username, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         return self.create_user(username, email, password, **extra_fields)


# class CustomUser(AbstractBaseUser, PermissionsMixin):
    
#     id = models.AutoField(primary_key=True)
#     username = models.CharField(max_length=32, unique=True)
#     email = models.EmailField(max_length=254, unique=True)
#     password = models.CharField(max_length=64)
#     date_of_birth = models.DateField(blank=True, null=True)
#     profile_image = models.ImageField(upload_to='media/', max_length=300, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     bio = models.TextField(blank=True, null=True)
#     deleted_at = models.DateTimeField(null=True, blank=True)
    
#     phone_number = models.CharField(max_length=15, unique=True)
#     verification_code = models.IntegerField(null=True, blank=True)  # 인증 코드 저장
#     is_phone_verified = models.BooleanField(default=False)  # 인증 여부
    
#     following = models.ManyToManyField('self', symmetrical=False, related_name='followers')


#     is_staff = models.BooleanField(default=False)  # 관리자 여부 설정

#     objects = CustomUserManager()

#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['email']

#     def delete(self, *args, **kwargs):
#         # Soft Delete: 실제로 삭제하지 않고 deleted_at을 기록
#         self.deleted_at = timezone.now()
#         self.save()

#     @property
#     def is_active(self):
#         return self.deleted_at is None

#     def __str__(self):
#         return self.username

#     profile_image = models.CharField(
#         max_length=255, null=True, blank=True, 
#         help_text="사용자 프로필 이미지 URL"
#     )
#     favorite_genres = models.ManyToManyField(
#         'movies.Genre', related_name='users', blank=True, 
#         help_text="선호 장르 목록"
#     )
#     liked_movies = models.ManyToManyField(
#         'movies.Movie', related_name='liked_movies_by_users', blank=True, 
#         help_text="좋아요한 영화 목록"
#     )
#     watched_movies = models.ManyToManyField(
#         'movies.Movie', related_name='watched_movies_by_users', blank=True, 
#         verbose_name="본 영화 목록",
#         help_text="사용자가 이미 본 영화 목록"
#     )
#     liked_posts = models.ManyToManyField(
#         'community.Post', related_name='liked_posts_by_users', blank=True, 
#         help_text="좋아요한 게시글 목록"
#     )
#     liked_reviews = models.ManyToManyField(
#         'community.Review', related_name='liked_by_users', blank=True, 
#         help_text="좋아요한 리뷰 목록"
#     )  # 리뷰 좋아요 추가
#     following = models.ManyToManyField(
#         'self', symmetrical=False, related_name='followers', blank=True, 
#         help_text="팔로우하는 사용자 목록"
#     )
#     favorite_actors = models.ManyToManyField(
#         'movies.Actor', related_name='favorited_actor_by_users', blank=True, 
#         help_text="즐겨찾기한 배우 목록"
#     )
#     favorite_directors = models.ManyToManyField(
#         'movies.Director', related_name='favorited_director_by_users', blank=True, 
#         help_text="즐겨찾기한 감독 목록"
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True, help_text="계정 생성 날짜"
#     )
#     bio = models.TextField(
#         null=True, blank=True, 
#         help_text="사용자의 자기소개"
#     )
#     unread_notifications_count = models.PositiveIntegerField(
#         default=0, 
#         help_text="읽지 않은 알림 수"
#     )  
    
#     def __str__(self):
#         return self.username


