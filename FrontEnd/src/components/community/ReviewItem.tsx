import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThumbsUp, MessageSquare, Star, Film } from 'lucide-react';
import { motion } from "framer-motion";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

interface ReviewItemProps {
  review: {
    id: number;
    title: string;
    movie?: {
      id: number;
      title: string;
      poster_path: string | null;
      movie_url?: string | null;
    } | null;
    user: {
      id: number;
      username: string;
      profile_image: string | null;
    };
    created_at: string;
    like_count: number;
    rating: number;
    comments?: Array<{
      id: number;
      content: string;
      user: {
        id: number;
        username: string;
        profile_image: string | null;
      };
      created_at: string;
      like_count: number;
      dislike_count: number;
    }> | [];
  };
  onClick: () => void;
}

export const ReviewItem: React.FC<ReviewItemProps> = ({ review, onClick }) => {
  // 날짜 포맷팅을 클라이언트에서만 처리
  const [formattedDate, setFormattedDate] = useState<string>(review.created_at);

  useEffect(() => {
    const date = new Date(review.created_at);
    const formatted = new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date);
    setFormattedDate(formatted);
  }, [review.created_at]);

  // 포스터 이미지 경로 처리
  const posterPath = (() => {
    if (review.movie?.poster_path) {
      if (review.movie.poster_path.startsWith('http')) {
        // 절대 URL인 경우 그대로 사용
        return review.movie.poster_path;
      } else if (review.movie.poster_path.startsWith('/')) {
        // 상대 경로인 경우 그대로 사용
        return review.movie.poster_path;
      } else {
        // 상대 경로로 수정
        return `/${review.movie.poster_path}`;
      }
    } else {
      // 포스터 이미지가 없을 경우 기본 이미지 사용
      return '/default_poster.png';
    }
  })();

  // 프로필 이미지 경로 처리
  const profileImagePath = (() => {
    if (review.user.profile_image) {
      if (review.user.profile_image.startsWith('http')) {
        // 절대 URL인 경우 그대로 사용
        return review.user.profile_image;
      } else if (review.user.profile_image.startsWith('/')) {
        // 상대 경로인 경우 그대로 사용
        return review.user.profile_image;
      } else {
        // 상대 경로로 수정
        return `/${review.user.profile_image}`;
      }
    } else {
      // 프로필 이미지가 없을 경우 기본 이미지 사용
      return '/default_profile.png';
    }
  })();

  return (
    <motion.div
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Card
        className="cursor-pointer hover:shadow-lg transition-all duration-300 bg-white dark:bg-[#1E1E1E] border-[#E0E0E0] dark:border-[#333333]"
        onClick={onClick}
      >
        <CardHeader className="pb-2">
          <div className="flex items-start space-x-4">
            <div className="relative w-24 h-36 flex-shrink-0">
              {/* Image 컴포넌트를 <img> 태그로 변경 */}
              <img
                src={posterPath}
                alt={review.movie?.title || "No movie associated"}
                className="rounded-md object-cover w-full h-auto"
              />
            </div>
            <div className="flex-grow">
              <CardTitle className="text-lg font-semibold text-[#333333] dark:text-white line-clamp-2 mb-1">
                {review.title}
              </CardTitle>
              <p className="text-sm text-[#666666] dark:text-[#B0B0B0] mb-2 flex items-center">
                <Film className="mr-1 h-4 w-4" />
                {review.movie?.title || "No movie selected"}
              </p>
              <div className="flex items-center mb-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`h-4 w-4 ${
                      star <= review.rating
                        ? "text-yellow-400 fill-yellow-400"
                        : "text-gray-300 dark:text-gray-600"
                    }`}
                  />
                ))}
                <span className="ml-2 text-sm text-[#666666] dark:text-[#B0B0B0]">
                  {review.rating}/5
                </span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Avatar className="h-8 w-8">
                <img
                  src={profileImagePath}
                  alt={review.user.username}
                  className="rounded-full"
                  width={32}
                  height={32}
                />
                {/* AvatarFallback 컴포넌트를 그대로 두고, 이미지가 없는 경우 첫 글자를 보여줌 */}
                <AvatarFallback>{review.user.username[0]}</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm font-medium text-[#333333] dark:text-white">
                  {review.user.username}
                </p>
                <p className="text-xs text-[#666666] dark:text-[#B0B0B0]">
                  {formattedDate}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-[#007BFF] dark:text-[#FF5733] hover:text-[#0056B3] dark:hover:text-[#FF7043]"
            >
              <ThumbsUp className="mr-1 h-4 w-4" />
              {review.like_count}
            </Button>
          </div>
          <div className="flex items-center justify-between text-sm text-[#666666] dark:text-[#B0B0B0]">
            <span className="flex items-center">
              <MessageSquare className="mr-1 h-4 w-4" />
              {Array.isArray(review.comments) ? review.comments.length : 0} 댓글
            </span>
            <span className="text-xs">자세히 보기</span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
