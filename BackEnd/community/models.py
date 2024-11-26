from django.db import models
from accounts.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator
from movies.models import Actor, Movie, Genre, News, Director
from accounts.models import CustomUser, Notification

class Post(models.Model):
    title = models.CharField(max_length=255, help_text="게시글 제목", default='제목 없음')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts', help_text="작성자 사용자")
    content = models.TextField(help_text="게시글 내용")
    created_at = models.DateTimeField(auto_now_add=True, help_text="게시글 작성 날짜")
    updated_at = models.DateTimeField(auto_now=True, help_text="게시글 수정 날짜")

    def __str__(self):
        return self.title  # 문자열 표현: 게시글 제목


class Review(models.Model):
    
    title = models.CharField(max_length=255, help_text="리뷰 제목", default='제목 없음')

    RATING_CHOICES = [
        (1, '★'),
        (2, '★★'),
        (3, '★★★'),
        (4, '★★★★'),
        (5, '★★★★★'),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='reviews', 
        help_text="작성자"
    )
    # 특정 영화에 대한 리뷰, 영화와 관련 없는 주제의 리뷰(예: "최신 영화 트렌드", "좋아하는 감독 소개") 
    # 모두 가능하게 하기 위해 -> 사실 구현이 편해서 null=True, blank=True 설정.
    movie = models.ForeignKey( 
        Movie, 
        on_delete=models.CASCADE, 
        related_name='reviews', 
        help_text="리뷰 대상 영화",
        null=True,
        blank=True,
    )
    content = models.TextField(help_text="리뷰 내용")
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="별점",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="리뷰 작성 날짜")
    updated_at = models.DateTimeField(auto_now=True, help_text="리뷰 수정 날짜")
    
    class Meta:
        unique_together = ['user', 'movie']  # 사용자당 영화 하나에 리뷰 하나만
        ordering = ['-created_at']  # 최신 리뷰부터 정렬
        indexes = [
            models.Index(fields=['movie', '-created_at']),  # 영화별 최신 리뷰 조회를 위한 인덱스
            models.Index(fields=['user', '-created_at']),   # 사용자별 최신 리뷰 조회를 위한 인덱스
        ]

    def __str__(self):
        return self.title  # 문자열 표현: 리뷰 제목

    @property
    def rating_display(self):
        """별점을 stars로 표시"""
        return '★' * self.rating

class Comment(models.Model):
    review = models.ForeignKey(
        Review, null=True, blank=True, on_delete=models.CASCADE,
        related_name='review_comments',  # 리뷰에 달린 댓글
        help_text="댓글을 작성한 리뷰"
    )
    post = models.ForeignKey(
        Post, null=True, blank=True, on_delete=models.CASCADE,
        related_name='post_comments',  # 게시글에 달린 댓글
        help_text="댓글을 작성한 게시글"
    )
    actor = models.ForeignKey(
        Actor, null=True, blank=True, on_delete=models.CASCADE,
        related_name='actor_comments',  # 배우에 달린 댓글
        help_text="댓글을 작성한 배우"
    )
    director = models.ForeignKey(
        Director, null=True, blank=True, on_delete=models.CASCADE,
        related_name='director_comments',  # 감독에 달린 댓글
        help_text="댓글을 작성한 감독"
    )
    movie = models.ForeignKey(
        Movie, null=True, blank=True, on_delete=models.CASCADE,
        related_name='movie_comments',  # 영화에 달린 댓글
        help_text="댓글을 작성한 영화"
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='user_comments',  # 작성자가 작성한 댓글
        help_text="댓글 작성자"
    )
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='replies',  # 대댓글
        help_text="대댓글의 부모 댓글"
    )
    content = models.TextField(help_text="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, help_text="댓글 작성 날짜")
    likes = models.ManyToManyField(
        CustomUser, related_name='liked_comments', blank=True,
        help_text="이 댓글을 좋아요 한 사용자들"
    )
    dislikes = models.ManyToManyField(
        CustomUser, related_name='disliked_comments', blank=True,
        help_text="이 댓글을 싫어요 한 사용자들"
    )

    def __str__(self):
        return f"Comment by {self.user.username}"

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def dislike_count(self):
        return self.dislikes.count()
