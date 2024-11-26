'use client'

import React, { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Star } from 'lucide-react';

interface Review {
  id: number;
  rating: number;
  content: string;
  user: string;
  created_at: string;
  updated_at: string;
}

interface ReviewsTabProps {
  reviews: Review[];
}

const REVIEWS_PER_PAGE = 6;

// 현재 로그인한 유저의 리뷰를 찾아서 배열의 맨 앞으로 이동시키는 함수
const sortReviewsWithUserFirst = (reviews: Review[]): Review[] => {
  const currentUsername = localStorage.getItem('nickname') || sessionStorage.getItem('nickname');
  
  if (!currentUsername || reviews.length === 0) return reviews;

  const userReviewIndex = reviews.findIndex(review => review.user === currentUsername);
  
  if (userReviewIndex === -1) return reviews;
  
  // 배열 복사 후 유저의 리뷰를 맨 앞으로 이동
  const sortedReviews = [...reviews];
  const [userReview] = sortedReviews.splice(userReviewIndex, 1);
  return [userReview, ...sortedReviews];
};

const ReviewsTab: React.FC<ReviewsTabProps> = ({ reviews }) => {
  const [currentPage, setCurrentPage] = useState(1);

  // 정렬된 리뷰 배열 생성
  const sortedReviews = useCallback(() => sortReviewsWithUserFirst(reviews), [reviews]);

  if (reviews.length === 0) {
    return <p className="text-gray-400 text-center">아직 리뷰가 없습니다. 첫 리뷰를 작성해 보세요!</p>;
  }

  const totalPages = Math.ceil(sortedReviews().length / REVIEWS_PER_PAGE);
  const startIndex = (currentPage - 1) * REVIEWS_PER_PAGE;
  const endIndex = startIndex + REVIEWS_PER_PAGE;
  const currentReviews = sortedReviews().slice(startIndex, endIndex);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {currentReviews.map((review) => (
          <Card 
            key={review.id} 
            className={`bg-purple-800/70 hover:bg-purple-700/80 shadow-lg hover:shadow-xl transition-all duration-300 border border-purple-500/50 ${
              review.user === (localStorage.getItem('nickname') || sessionStorage.getItem('nickname'))
                ? 'ring-2 ring-yellow-400'
                : ''
            }`}
          >
            <CardContent className="p-4 aspect-[2/1] flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-white font-semibold truncate text-xl">
                    {review.user}
                    {review.user === (localStorage.getItem('nickname') || sessionStorage.getItem('nickname')) && 
                      <span className="ml-2 text-yellow-400 text-sm">(내 리뷰)</span>
                    }
                  </p>
                  <div className="flex items-center">
                    <Star className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                    <span className="text-yellow-400 font-bold text-xl">{review.rating.toFixed(1)}</span>
                  </div>
                </div>
                <p className="text-gray-200 text-lg mb-2 line-clamp-3">{review.content}</p>
              </div>
              <p className="text-gray-300 text-base mt-2">
                작성일: {new Date(review.created_at).toLocaleDateString()}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-center items-center mt-4 space-x-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
          disabled={currentPage === 1}
          className="w-8 h-8 p-0"
        >
          <ChevronLeft className="h-4 w-4 text-gray-400" />
          <span className="sr-only">이전 페이지</span>
        </Button>
        <span className="text-sm text-gray-400">
          {currentPage} / {totalPages}
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
          disabled={currentPage === totalPages}
          className="w-8 h-8 p-0"
        >
          <ChevronRight className="h-4 w-4 text-gray-400" />
          <span className="sr-only">다음 페이지</span>
        </Button>
      </div>
    </div>
  );
};

export default ReviewsTab;

