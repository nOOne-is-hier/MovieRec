'use client'

import { useState, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { PostDetail, ReviewDetail } from "@/types/community";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ThumbsUp, Star, Film, Edit, Trash } from 'lucide-react';
import { CommentList } from "./CommentList";
import { CommentForm } from "./CommentForm";
import { updatePost, deletePost, updateReview, deleteReview } from "@/lib/api";
import jwt_decode from "jwt-decode";
import DOMPurify from 'dompurify';
import UserProfileModal from '@/components/UserProfileModal';

interface ItemDetailProps {
  item: PostDetail | ReviewDetail;
  onLikeToggle: () => void;
  onCommentSubmit: (content: string, parent: number | null) => void;
  fetchItemDetail: (id: number, type: 'post' | 'review') => void;
  onClose: () => void;
  onOpenModal: () => void;
}

export const ItemDetail: React.FC<ItemDetailProps> = ({
  item,
  onLikeToggle,
  onCommentSubmit,
  fetchItemDetail,
  onClose,
  onOpenModal,
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(item.title);
  const [editedContent, setEditedContent] = useState(item.content);
  const [editedRating, setEditedRating] = useState(isReviewDetail(item) ? item.rating : undefined);

  const currentUserId = getCurrentUserId();
  const isAuthor = currentUserId === item.user.id;

  const handleMovieClick = useCallback((id: string) => {
    if (id) {
      const newParams = new URLSearchParams(searchParams?.toString() || "");
      newParams.set('movieId', id);
      router.push(`${pathname}?${newParams.toString()}`, { scroll: false });
      if (onOpenModal) onOpenModal();
    }
  }, [router, searchParams, pathname, onOpenModal]);

  const handlePersonClick = useCallback((id: string, type: 'actor' | 'director') => {
    if (id && type) {
      const newParams = new URLSearchParams(searchParams?.toString() || "");
      newParams.set('personId', id);
      newParams.set('personType', type);
      router.push(`${pathname}?${newParams.toString()}`, { scroll: false });
      if (onOpenModal) onOpenModal();
    }
  }, [router, searchParams, pathname, onOpenModal]);

  const handleEdit = () => setIsEditing(true);

  const handleUpdate = async () => {
    try {
      const updatedData: { title?: string; content?: string; rating?: number } = {};
      if (editedTitle !== item.title) updatedData.title = editedTitle;
      if (editedContent !== item.content) updatedData.content = editedContent;

      if (isReviewDetail(item)) {
        if (editedRating !== item.rating) updatedData.rating = editedRating;
        await updateReview(item.id, updatedData);
      } else {
        await updatePost(item.id, updatedData);
      }

      await fetchItemDetail(item.id, isReviewDetail(item) ? 'review' : 'post');
      setIsEditing(false);
    } catch (error) {
      console.error('수정 실패:', error);
    }
  };

  const handleDelete = async () => {
    if (confirm('정말로 삭제하시겠습니까?')) {
      try {
        if (isReviewDetail(item)) {
          await deleteReview(item.id);
        } else {
          await deletePost(item.id);
        }
        onClose();
      } catch (error) {
        console.error('삭제 실패:', error);
      }
    }
  };

  const profileImagePath = item.user.profile_image
    ? item.user.profile_image.startsWith('http') || item.user.profile_image.startsWith('/')
      ? item.user.profile_image
      : `/${item.user.profile_image}`
    : '/default_profile.png';

  const posterPath = isReviewDetail(item) && item.movie.poster_path
    ? item.movie.poster_path.startsWith('http') || item.movie.poster_path.startsWith('/')
      ? item.movie.poster_path
      : `/${item.movie.poster_path}`
    : '/default_poster.png';

  const handleProfileClick = () => {
    setIsProfileModalOpen(true);
  };

  return (
    <div className="space-y-6 bg-white dark:bg-[#121212] text-[#333333] dark:text-white transition-colors duration-300">
      <div className="flex items-center space-x-4">
        <Avatar className="h-12 w-12 border-2 border-[#007BFF] dark:border-[#FF5733] cursor-pointer" onClick={handleProfileClick}>
          <img
            src={profileImagePath}
            alt={`${item.user.username}'s profile`}
            className="rounded-full object-cover"
            width={48}
            height={48}
          />
          <AvatarFallback className="bg-[#007BFF] dark:bg-[#FF5733] text-white">
            {item.user.username[0]}
          </AvatarFallback>
        </Avatar>
        <div>
          <p className="font-semibold cursor-pointer" onClick={handleProfileClick}>{item.user.username}</p>
          <p className="text-sm text-[#666666] dark:text-[#B0B0B0]">
            {new Intl.DateTimeFormat('ko-KR', {
              year: 'numeric', month: 'long', day: 'numeric',
              hour: '2-digit', minute: '2-digit', hour12: false
            }).format(new Date(item.created_at))}
          </p>
        </div>
      </div>

      {isReviewDetail(item) && (
        <div className="flex items-center space-x-4 bg-[#F9F9F9] dark:bg-[#1E1E1E] p-4 rounded-lg">
          <img
            src={posterPath}
            alt={item.movie.title}
            width={100}
            height={150}
            className="rounded-md object-cover"
          />
          <div>
            <h3 className="text-lg font-semibold">{item.movie.title}</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleMovieClick(item.movie.id.toString())}
              className="text-[#007BFF] dark:text-[#FF5733] hover:text-[#0056B3] dark:hover:text-[#FF7043] p-0 h-auto"
            >
              <Film className="mr-2 h-4 w-4" />
              영화 상세 페이지 보기
            </Button>
          </div>
        </div>
      )}

      {isEditing ? (
        <form onSubmit={(e) => { e.preventDefault(); handleUpdate(); }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">제목</label>
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              required
              className="w-full border border-gray-300 p-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">내용</label>
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              required
              className="w-full border border-gray-300 p-2 rounded h-32"
            />
          </div>
          {isReviewDetail(item) && (
            <div>
              <label className="block text-sm font-medium mb-1">평점</label>
              <input
                type="number"
                value={editedRating}
                onChange={(e) => setEditedRating(Number(e.target.value))}
                min={1}
                max={5}
                required
                className="w-full border border-gray-300 p-2 rounded"
              />
            </div>
          )}
          <div className="flex space-x-2">
            <Button type="submit">수정 완료</Button>
            <Button variant="secondary" onClick={() => setIsEditing(false)}>취소</Button>
          </div>
        </form>
      ) : (
        <>
          <div className="bg-[#F9F9F9] dark:bg-[#1E1E1E] p-4 rounded-lg">
            <h2 className="text-xl font-bold mb-2">{item.title}</h2>
            <div
              className="text-[#666666] dark:text-[#B0B0B0]"
              dangerouslySetInnerHTML={renderHTML(item.content)}
            />
          </div>

          {isReviewDetail(item) && (
            <div className="flex items-center space-x-2 bg-[#F9F9F9] dark:bg-[#1E1E1E] p-2 rounded-lg">
              {Array.from({ length: 5 }).map((_, index) => (
                <Star
                  key={index}
                  className={`h-5 w-5 ${index < item.rating
                    ? "text-[#FFC300] fill-[#FFC300]"
                    : "text-[#E0E0E0] dark:text-[#333333]"
                    }`}
                />
              ))}
              <span className="text-lg font-semibold ml-2">{item.rating}/5</span>
            </div>
          )}
        </>
      )}

      {isAuthor && (
        <div className="flex space-x-2">
          <Button onClick={handleEdit}>
            <Edit className="mr-2 h-4 w-4" /> 수정
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash className="mr-2 h-4 w-4" /> 삭제
          </Button>
        </div>
      )}

      <div className="flex items-center space-x-4">
        <Button
          variant="outline"
          size="sm"
          onClick={onLikeToggle}
          className="bg-white dark:bg-[#1E1E1E] text-[#007BFF] dark:text-[#FF5733] border-[#007BFF] dark:border-[#FF5733] hover:bg-[#007BFF] dark:hover:bg-[#FF5733] hover:text-white"
        >
          <ThumbsUp className="mr-2 h-4 w-4" /> 좋아요 {item.like_count}
        </Button>
        <span className="text-sm text-[#666666] dark:text-[#B0B0B0]">
          {item.comments.length}개의 댓글
        </span>
      </div>

      {item.comments.length > 0 ? (
        <CommentList
          comments={item.comments}
          onCommentSubmit={onCommentSubmit}
          fetchItemDetail={() => fetchItemDetail(item.id, isReviewDetail(item) ? 'review' : 'post')}
        />
      ) : (
        <p className="text-[#666666] dark:text-[#B0B0B0]">댓글이 없습니다.</p>
      )}

      <CommentForm onSubmit={(content) => onCommentSubmit(content, null)} />

      {isProfileModalOpen && (
        <UserProfileModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          userId={item.user.id}
        />
      )}
    </div>
  );
};

function isReviewDetail(item: PostDetail | ReviewDetail): item is ReviewDetail {
  return 'movie' in item && item.movie !== null;
}

function getCurrentUserId() {
  const token = localStorage.getItem('accessToken');
  if (token) {
    const decodedToken: any = jwt_decode(token);
    return decodedToken.user_id;
  }
  return null;
}

function renderHTML(content: string) {
  return { __html: DOMPurify.sanitize(content) };
}

