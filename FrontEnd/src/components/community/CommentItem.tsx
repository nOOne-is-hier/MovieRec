'use client'

import { useState, useEffect } from 'react';
import { Comment } from '@/types/community';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ThumbsUp, ThumbsDown, MessageSquare, Edit, Trash } from 'lucide-react';
import { CommentForm } from './CommentForm';
import { updateComment, deleteComment, getCurrentUserId, toggleCommentLike, toggleCommentDislike } from '@/lib/api';
import UserProfileModal from '@/components/UserProfileModal';

interface CommentItemProps {
  comment: Comment;
  onReply: (content: string, parent: number | null) => void;
  fetchItemDetail: () => void;
  level?: number;
  allComments?: Comment[]; // 추가된 속성

}

export const CommentItem: React.FC<CommentItemProps> = ({ comment, onReply, fetchItemDetail, level = 0 }) => {
  const [isReplying, setIsReplying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(comment.content);
  const [formattedDate, setFormattedDate] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [likeCount, setLikeCount] = useState(comment.like_count);
  const [dislikeCount, setDislikeCount] = useState(comment.dislike_count);
  const [isLiked, setIsLiked] = useState(false);
  const [isDisliked, setIsDisliked] = useState(false);

  useEffect(() => {
    setFormattedDate(
      new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(new Date(comment.created_at))
    );
    
    setIsLiked(comment.is_liked || false);
    setIsDisliked(comment.is_disliked || false);
  }, [comment.created_at, comment.is_liked, comment.is_disliked]);

  const profileImageSrc = (() => {
    if (comment.user.profile_image) {
      if (comment.user.profile_image.startsWith('http://127.0.0.1:8000')) {
        return comment.user.profile_image.replace('http://127.0.0.1:8000', '');
      } else if (comment.user.profile_image.startsWith('http') || comment.user.profile_image.startsWith('https')) {
        return comment.user.profile_image;
      } else {
        return comment.user.profile_image;
      }
    } else {
      return '/default_profile.png';
    }
  })();

  const currentUserId = getCurrentUserId();
  const isAuthor = currentUserId === comment.user.id;

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleUpdate = async () => {
    try {
      if (editedContent.trim() === '') {
        alert('댓글 내용을 입력해주세요.');
        return;
      }
      const response = await updateComment(comment.id, { content: editedContent });
      if (response.status === 200) {
        fetchItemDetail();
        setIsEditing(false);
      }
    } catch (error) {
      console.error('댓글 수정 실패:', error);
    }
  };

  const handleDelete = async () => {
    if (confirm('댓글을 삭제하시겠습니까?')) {
      try {
        const response = await deleteComment(comment.id);
        if (response.status === 200) {
          fetchItemDetail();
        }
      } catch (error) {
        console.error('댓글 삭제 실패:', error);
      }
    }
  };

  const handleReplySubmit = (content: string) => {
    onReply(content, comment.id);
    setIsReplying(false);
  };

  const handleProfileClick = () => {
    setIsProfileModalOpen(true);
  };

  const handleLike = async () => {
    try {
      const response = await toggleCommentLike(comment.id);
      if (response.status === 200) {
        setIsLiked(!isLiked);
        setLikeCount(prevCount => isLiked ? prevCount - 1 : prevCount + 1);
        if (isDisliked) {
          setIsDisliked(false);
          setDislikeCount(prevCount => prevCount - 1);
        }
      }
    } catch (error) {
      console.error('좋아요 토글 실패:', error);
    }
  };

  const handleDislike = async () => {
    try {
      const response = await toggleCommentDislike(comment.id);
      if (response.status === 200) {
        setIsDisliked(!isDisliked);
        setDislikeCount(prevCount => isDisliked ? prevCount - 1 : prevCount + 1);
        if (isLiked) {
          setIsLiked(false);
          setLikeCount(prevCount => prevCount - 1);
        }
      }
    } catch (error) {
      console.error('싫어요 토글 실패:', error);
    }
  };

  return (
    <div
      className={`border-l-2 border-gray-200 dark:border-gray-700 py-4 transition-colors duration-300`}
      style={{ marginLeft: `${level * 20}px` }}
    >
      <div className="flex items-center space-x-3">
        <Avatar className="h-10 w-10 cursor-pointer" onClick={handleProfileClick}>
          <img
            src={profileImageSrc}
            alt={comment.user.username}
            width={40}
            height={40}
            className="rounded-full"
          />
          <AvatarFallback className="bg-[#007BFF] dark:bg-[#FF5733] text-white">
            {comment.user.username[0]}
          </AvatarFallback>
        </Avatar>
        <div>
          <p className="font-semibold text-[#333333] dark:text-white cursor-pointer" onClick={handleProfileClick}>
            {comment.user.username}
          </p>
          <p className="text-xs text-[#666666] dark:text-[#B0B0B0]">
            {formattedDate || '날짜 로딩 중...'}
          </p>
        </div>
      </div>

      {isEditing ? (
        <div className="mt-3">
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="w-full border border-gray-300 p-2 rounded h-20"
          />
          <div className="flex space-x-2 mt-2">
            <Button onClick={handleUpdate}>수정 완료</Button>
            <Button variant="secondary" onClick={() => setIsEditing(false)}>취소</Button>
          </div>
        </div>
      ) : (
        <p className="mt-3 text-[#333333] dark:text-white">{comment.content}</p>
      )}

      <div className="flex items-center space-x-4 mt-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLike}
          className={`text-[#666666] dark:text-[#B0B0B0] hover:text-[#007BFF] dark:hover:text-[#FF5733] transition-colors duration-300 ${
            isLiked ? 'text-[#007BFF] dark:text-[#FF5733]' : ''
          }`}
        >
          <ThumbsUp className="mr-2 h-4 w-4" /> {likeCount}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDislike}
          className={`text-[#666666] dark:text-[#B0B0B0] hover:text-[#007BFF] dark:hover:text-[#FF5733] transition-colors duration-300 ${
            isDisliked ? 'text-[#007BFF] dark:text-[#FF5733]' : ''
          }`}
        >
          <ThumbsDown className="mr-2 h-4 w-4" /> {dislikeCount}
        </Button>
        {level === 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsReplying(!isReplying)}
            className="text-[#666666] dark:text-[#B0B0B0] hover:text-[#007BFF] dark:hover:text-[#FF5733] transition-colors duration-300"
          >
            <MessageSquare className="mr-2 h-4 w-4" /> 답글
          </Button>
        )}

        {isAuthor && (
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEdit}
              className="text-[#666666] dark:text-[#B0B0B0] hover:text-green-500 dark:hover:text-green-400 transition-colors duration-300"
            >
              <Edit className="mr-2 h-4 w-4" /> 수정
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              className="text-[#666666] dark:text-[#B0B0B0] hover:text-red-500 dark:hover:text-red-400 transition-colors duration-300"
            >
              <Trash className="mr-2 h-4 w-4" /> 삭제
            </Button>
          </>
        )}
      </div>

      {isReplying && level === 0 && (
        <div className="mt-4">
          <CommentForm onSubmit={handleReplySubmit} />
        </div>
      )}

      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-4">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              onReply={onReply}
              fetchItemDetail={fetchItemDetail}
              level={level + 1}
              
            />
          ))}
        </div>
      )}

      <UserProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        userId={comment.user.id}
      />
    </div>
  );
};

