import { useState, useEffect } from "react";
import { Post } from '@/types/community';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThumbsUp, MessageSquare, User, Calendar } from 'lucide-react';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface PostItemProps {
  post: Post;
  onClick: () => void;
}

export const PostItem: React.FC<PostItemProps> = ({ post, onClick }) => {
  const [formattedDate, setFormattedDate] = useState<string>(post.created_at);

  // 클라이언트에서만 날짜 포맷팅
  useEffect(() => {
    const date = new Date(post.created_at);
    const formatted = new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour12: false,
    }).format(date);
    setFormattedDate(formatted);
  }, [post.created_at]);

  // 프로필 이미지 경로 처리
  const profileImageSrc = (() => {
    if (post.user.profile_image) {
      if (post.user.profile_image.startsWith('http')) {
        // 절대 URL인 경우 그대로 사용
        return post.user.profile_image;
      } else if (post.user.profile_image.startsWith('/')) {
        // 상대 경로인 경우 그대로 사용
        return post.user.profile_image;
      } else {
        // 상대 경로로 수정
        return `/${post.user.profile_image}`;
      }
    } else {
      // 프로필 이미지가 없을 경우 기본 이미지 사용
      return '/default_profile.png';
    }
  })();

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-all duration-300 bg-white dark:bg-[#1E1E1E] border-[#E0E0E0] dark:border-[#333333]"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-semibold text-[#333333] dark:text-white line-clamp-1">
          {post.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center space-x-2 mb-2">
          <Avatar className="h-6 w-6">
            <img
              src={profileImageSrc}
              alt={post.user.username}
              className="rounded-full"
              width={24}
              height={24}
            />
            <AvatarFallback className="bg-[#007BFF] dark:bg-[#FF5733] text-white text-xs">
              {post.user.username[0]}
            </AvatarFallback>
          </Avatar>
          <p className="text-sm text-[#666666] dark:text-[#B0B0B0] flex items-center">
            <User className="h-3 w-3 mr-1" /> {post.user.username}
          </p>
        </div>
        <p className="text-xs text-[#666666] dark:text-[#B0B0B0] mb-2 flex items-center">
          <Calendar className="h-3 w-3 mr-1" /> {formattedDate}
        </p>
        <div className="flex items-center space-x-4 text-sm text-[#666666] dark:text-[#B0B0B0]">
          <div className="flex items-center">
            <ThumbsUp className="h-4 w-4 mr-1 text-[#007BFF] dark:text-[#FF5733]" />
            <span>{post.like_count}</span>
          </div>
          <div className="flex items-center">
            <MessageSquare className="h-4 w-4 mr-1 text-[#007BFF] dark:text-[#FF5733]" />
            <span>{post.comment_count}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
