from django.urls import reverse
from django.utils.timezone import now, timedelta
from accounts.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def create_notification(user, content, type, link=None, instance=None):
    """
    사용자에게 알림을 생성하는 함수

    Parameters:
        user: 알림을 받을 사용자 객체
        content: 알림 내용 문자열
        type: 알림 유형 (comment, reply, like, follow 등)
        link: 알림 클릭 시 이동할 URL (선택적)
        instance: 알림과 관련된 객체 (댓글, 게시글 등) (선택적)

    Returns:
        생성된 Notification 객체
    """
    
    # instance와 type을 기반으로 link 생성
    if not link and instance:
        if type == 'comment':
            # 댓글이 게시글(post)와 연결된 경우
            if hasattr(instance, 'post') and instance.post:
                link = reverse('community:post-detail', args=[instance.post.id])
            # 댓글이 리뷰(review)와 연결된 경우
            elif hasattr(instance, 'review') and instance.review:
                link = reverse('community:review-detail', args=[instance.review.id])
        elif type == 'like':
            # 좋아요 알림인 경우
            if hasattr(instance, 'post') and instance.post:
                link = reverse('community:post-detail', args=[instance.post.id])
            elif hasattr(instance, 'review') and instance.review:
                link = reverse('community:review-detail', args=[instance.review.id])
        elif type == 'follow' and hasattr(instance, 'id'):
            # 팔로우 알림
            link = reverse('accounts:user-liked-movies', args=[instance.id])

    # 알림 생성
    notification = Notification.objects.create(
        user=user,          # 알림 받을 사용자
        content=content,    # 알림 내용
        type=type,          # 알림 유형
        link=link           # 알림 클릭 시 이동할 링크
    )

    # 사용자의 읽지 않은 알림 개수 업데이트
    user.unread_notifications_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    user.save()

    return notification