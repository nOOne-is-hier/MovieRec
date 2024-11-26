'use client'

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { Dialog, DialogContent, DialogClose, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area1"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Calendar, Star, X, Play, Heart, ChevronLeft, ChevronRight, ThumbsUp, ThumbsDown, MessageSquare, CornerDownRight } from 'lucide-react'
import api, { toggleCommentLike, toggleCommentDislike } from "@/lib/api"
import ReviewsTab from './reviews-tab'

// 인터페이스 정의
interface Movie {
  id: number;
  title: string;
  poster_path: string;
  genres: string[];
  overview: string;
  release_date: string;
  normalized_popularity: number;
  is_liked: boolean;
  news: {
    title: string;
    content: string;
    url: string;
    created_at: string;
  }[];
  cast: {
    actor_id: number;
    actor_name: string;
    actor_profile_path: string;
    character_name: string;
  }[];
  crews: {
    id: number;
    name: string;
    profile_path: string;
    job: string;
  }[];
  related_movies?: {
    id: number;
    title: string;
    poster_path: string;
    normalized_popularity: number;
    genres: string[];
  }[];
  trailer_link?: string;
  comments: Comment[];
  reviews: Review[]; // 새로 추가된 부분
}

interface Review {
  id: number;
  rating: number;
  content: string;
  user: string;
  created_at: string;
  updated_at: string;
}

interface Comment {
  id: number;
  user: string;
  user_id: number; // 사용자 ID 추가
  content: string;
  created_at: string;
  like_count: number;
  dislike_count: number;
  movie: number;
  parent: number | null;
  replies?: Comment[];
}

interface MovieDetailModalProps {
  movieId: string;
  onClose: () => void;  // onClose prop 추가
  onOpen?: () => void;
}

export default function MovieDetailModal({ movieId, onClose, onOpen }: MovieDetailModalProps) {

  // 상태 변수들
  const [movie, setMovie] = useState<Movie | null>(null)
  const [activeTab, setActiveTab] = useState('cast')
  const [showTrailer, setShowTrailer] = useState(false)
  const [isFavorite, setIsFavorite] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [newComment, setNewComment] = useState("")
  const [editComment, setEditComment] = useState<{ id: number; content: string } | null>(null)
  const [replyingTo, setReplyingTo] = useState<Comment | null>(null)
  const [loadingLikes, setLoadingLikes] = useState<{ [key: number]: boolean }>({})
  const [loadingDislikes, setLoadingDislikes] = useState<{ [key: number]: boolean }>({})
  const [castPage, setCastPage] = useState(1);
  const [castTotalPages, setCastTotalPages] = useState(1);
  const [scrollToCommentId, setScrollToCommentId] = useState<number | null>(null);
  const CAST_PER_PAGE = 4;
  const currentUsername = localStorage.getItem('nickname') || sessionStorage.getItem('nickname')
  const router = useRouter()
  const searchParams = useSearchParams()
  const pathname = usePathname()
  const commentRefs = useRef<{ [key: number]: HTMLDivElement }>({});
  const COMMENTS_PER_PAGE = 10
  const commentsSectionRef = useRef<HTMLDivElement | null>(null)

  // 페이지네이션을 위한 출연진 계산
  const paginatedCast = useMemo(() => {
    if (!movie) return [];
    const startIndex = (castPage - 1) * CAST_PER_PAGE;
    const endIndex = startIndex + CAST_PER_PAGE;
    return movie.cast.slice(startIndex, endIndex);
  }, [movie, castPage]);

  useEffect(() => {
    if (movie) {
      setCastTotalPages(Math.ceil(movie.cast.length / CAST_PER_PAGE));
    }
  }, [movie]);

  // 페이지 변경 핸들러
  const handleCastPageChange = (newPage: number) => {
    setCastPage(newPage);
  };

  // topComments 계산 로직 수정
  const topComments = useMemo<Comment[]>(() => {
    if (!movie) return [];

    const allComments = movie.comments.reduce<Comment[]>((acc, comment) => {
      if (comment.like_count > 0) {
        acc.push(comment);
      }
      if (comment.replies) {
        acc.push(...comment.replies.filter(reply => reply.like_count > 0));
      }
      return acc;
    }, []);

    return allComments
      .sort((a, b) => b.like_count - a.like_count)
      .slice(0, 5);
  }, [movie]);

  const paginatedComments = useMemo(() => {
    if (!movie) return [];
    const startIndex = (currentPage - 1) * COMMENTS_PER_PAGE;
    const endIndex = startIndex + COMMENTS_PER_PAGE;
    return movie.comments.slice(startIndex, endIndex);
  }, [movie, currentPage]);

  useEffect(() => {
    if (movie) {
      setTotalPages(Math.ceil((movie.comments.length || 0) / COMMENTS_PER_PAGE));
    }
  }, [movie]);

  // renderReplyForm 함수 수정
  const renderReplyForm = (parentComment: Comment) => (
    <div className="space-y-2 mt-4 ml-8">
      <p className="text-sm text-gray-400">{parentComment.user}님에게 답글 작성 중</p>
      <Textarea
        value={newComment}
        onChange={(e) => setNewComment(e.target.value)}
        placeholder="답글을 입력하세요"
        className="w-full border border-gray-700 p-2 rounded bg-gray-800 text-white"
      />
      <div className="flex space-x-2">
        <Button
          size="sm"
          onClick={(event) => handleAddReply(event, parentComment.id)}
          className="bg-purple-600 text-white hover:bg-purple-700 transition-colors"
        >
          답글 추가
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            setNewComment("");
            setReplyingTo(null);
          }}
          className="text-purple-800 hover:text-purple-300 border-purple-800 bg-slate-100 hover:bg-slate-50"
        >
          취소
        </Button>
      </div>
    </div>
  );

  // 모달 닫기 핸들러
  const handleClose = useCallback(() => {
    const currentParams = new URLSearchParams(searchParams.toString())
    currentParams.delete('movieId')

    if (pathname.startsWith('/community')) {
      router.push(`/community?${currentParams.toString()}`, { scroll: false })
    } else if (pathname.startsWith('/search')) {
      router.push(`/search?${currentParams.toString()}`, { scroll: false })
    } else {
      router.push(`/?${currentParams.toString()}`, { scroll: false })
    }
    if (typeof onClose === 'function') {
      onClose()
    }
  }, [router, searchParams, pathname, onClose])

  // 관련 영화 클릭 핸들러
  const handleRelatedMovieClick = (relatedMovieId: number) => {
    const currentParams = new URLSearchParams(searchParams.toString())
    currentParams.set('movieId', relatedMovieId.toString())

    if (pathname.startsWith('/search')) {
      router.push('/search?' + currentParams.toString(), { scroll: false })
    } else {
      router.push('/?' + currentParams.toString(), { scroll: false })
    }
  }

  // 인물 클릭 핸들러 수정
  const handlePersonClick = useCallback((personId: number, personType: 'actor' | 'director') => {
    const currentParams = new URLSearchParams(searchParams.toString())
    currentParams.set('personId', personId.toString())
    currentParams.set('personType', personType)
    currentParams.delete('movieId')

    router.push(`${pathname}?${currentParams.toString()}`, { scroll: false })
    if (typeof onOpen === 'function') {
      onOpen()
    }
  }, [router, searchParams, pathname, onOpen])

  // 즐겨찾기 토글 핸들러
  const toggleFavorite = async () => {
    if (!movie) return

    try {
      const response = await api.post(`/movies/${movieId}/like/`)
      if (response.status === 200) {
        setIsFavorite(!isFavorite)
      }
    } catch (error) {
      console.error('즐겨찾기 토글 중 오류 발생:', error)
    }
  }

  // 댓글 추가 핸들러
  const handleAddComment = async () => {
    if (!newComment.trim() || !movieId) return;

    try {
      const response = await api.post(`/movies/${movieId}/comments/`, {
        content: newComment,
        parent: null,
      });

      if (response.status === 201) {
        const createdComment = response.data;

        // Update the movie state with the new comment
        setMovie((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            comments: [createdComment, ...prev.comments],
          };
        });

        setNewComment(""); // Clear the input
        setCurrentPage(1); // Reset to the first page to show the new comment
        setScrollToCommentId(createdComment.id); // Scroll to the new comment

      }
    } catch (error) {
      console.error("댓글 생성 실패:", error);
    }
  };

  // 답글 추가 핸들러
  // 수정된 handleAddReply
  // 답글 추가 핸들러
  const handleAddReply = async (event: React.MouseEvent<HTMLButtonElement>, parent: number) => {
    event.preventDefault();
    if (!newComment.trim() || !movieId) return;

    try {
      const response = await api.post(`/movies/${movieId}/comments/`, {
        content: newComment,
        parent,
      });

      if (response.status === 201) {
        const createdReply = response.data;

        setMovie((prev) => {
          if (!prev) return prev;
          const updateComments = (comments: Comment[]): Comment[] =>
            comments.map((comment) =>
              comment.id === parent
                ? {
                  ...comment,
                  replies: [...(comment.replies || []), createdReply],
                }
                : comment
            );

          return {
            ...prev,
            comments: updateComments(prev.comments),
          };
        });

        setNewComment("");
        setReplyingTo(null);
        setScrollToCommentId(createdReply.id);
      }
    } catch (error) {
      console.error("답글 추가 중 오류 발생:", error);
    }
  };


  // 댓글 수정 핸들러
  const handleEditComment = async () => {
    if (!editComment || !editComment.content.trim()) return;

    try {
      // 엔드포인트 경로에 따라 요청 URL 수정
      const response = await api.put(`/movies/${movieId}/comments/${editComment.id}/update/`, {
        content: editComment.content,
      });

      if (response.status === 200) {
        const updatedComment = response.data;

        // 상태 업데이트 로직
        setMovie((prev) => {
          if (!prev) return prev;

          const updateComments = (comments: Comment[]): Comment[] =>
            comments.map((comment) => {
              if (comment.id === updatedComment.id) {
                // 최상위 댓글을 수정
                return { ...comment, content: updatedComment.content };
              }

              if (comment.replies) {
                // 답글을 수정
                return {
                  ...comment,
                  replies: comment.replies.map((reply) =>
                    reply.id === updatedComment.id
                      ? { ...reply, content: updatedComment.content }
                      : reply
                  ),
                };
              }

              return comment;
            });

          return {
            ...prev,
            comments: updateComments(prev.comments),
          };
        });

        setEditComment(null); // 수정 모드 종료
      }
    } catch (error) {
      console.error("댓글 수정 실패:", error);
    }
  };


  // 댓글 삭제 핸들러
  const handleDeleteComment = async (commentId: number) => {
    try {
      // 엔드포인트 경로에 따라 요청 URL 수정
      const response = await api.delete(`/movies/${movieId}/comments/${commentId}/delete/`);

      if (response.status === 204) {
        // 상태 업데이트: 삭제된 댓글을 제거
        setMovie((prev) => {
          if (!prev) return prev;

          const deleteComments = (comments: Comment[]): Comment[] =>
            comments
              .filter((comment) => comment.id !== commentId) // 삭제된 댓글 제외
              .map((comment) => ({
                ...comment,
                replies: comment.replies ? deleteComments(comment.replies) : [],
              }));

          return {
            ...prev,
            comments: deleteComments(prev.comments),
          };
        });

        console.log(`댓글 ID ${commentId} 삭제 완료`);
      }
    } catch (error) {
      console.error("댓글 삭제 실패:", error);
    }
  };


  // 좋아요 토글 핸들러
  const handleLikeToggle = async (commentId: number) => {
    if (loadingLikes[commentId] || loadingDislikes[commentId]) return;

    setLoadingLikes((prev) => ({ ...prev, [commentId]: true }));
    try {
      const response = await toggleCommentLike(commentId);
      if (response.status === 200) {
        setMovie((prev) => {
          if (!prev) return prev;
          const updateComments = (comments: Comment[]): Comment[] =>
            comments.map((comment) => {
              if (comment.id === commentId) {
                return { ...comment, like_count: response.data.like_count };
              }
              if (comment.replies) {
                return { ...comment, replies: updateComments(comment.replies) };
              }
              return comment;
            });
          return { ...prev, comments: updateComments(prev.comments) };
        });
      }
    } catch (error) {
      console.error("좋아요 토글 중 오류 발생:", error);
    } finally {
      setLoadingLikes((prev) => ({ ...prev, [commentId]: false }));
    }
  };


  // 싫어요 토글 핸들러
  const handleDislikeToggle = async (commentId: number) => {
    if (loadingLikes[commentId] || loadingDislikes[commentId]) return;

    setLoadingDislikes((prev) => ({ ...prev, [commentId]: true }));
    try {
      const response = await toggleCommentDislike(commentId);
      if (response.status === 200) {
        setMovie((prev) => {
          if (!prev) return prev;
          const updateComments = (comments: Comment[]): Comment[] =>
            comments.map((comment) => {
              if (comment.id === commentId) {
                return { ...comment, dislike_count: response.data.dislike_count };
              }
              if (comment.replies) {
                return { ...comment, replies: updateComments(comment.replies) };
              }
              return comment;
            });
          return { ...prev, comments: updateComments(prev.comments) };
        });
      }
    } catch (error) {
      console.error("싫어요 토글 중 오류 발생:", error);
    } finally {
      setLoadingDislikes((prev) => ({ ...prev, [commentId]: false }));
    }
  };


  // 페이지 변경 핸들러 (스크롤 보장 수정)
  const scrollToElement = (element: HTMLElement | null, behavior: ScrollBehavior = 'smooth') => {
    if (element) {
      element.scrollIntoView({ behavior, block: 'nearest' });
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    setTimeout(() => {
      scrollToElement(commentsSectionRef.current, 'smooth');
    }, 200);
  };

  // 댓글 렌더링 함수
  const renderComment = (comment: Comment) => (
    <div
      key={comment.id}
      ref={(el) => {
        if (el) {
          commentRefs.current[comment.id] = el;
        }
      }}
      className="flex flex-col bg-gray-800/50 p-4 rounded-lg mt-4"
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className="text-gray-300">{comment.user}</p>
          {editComment?.id === comment.id ? (
            <div className="space-y-2 my-2">
              <Textarea
                value={editComment.content}
                onChange={(e) => setEditComment({ ...editComment, content: e.target.value })}
                className="w-full border border-gray-700 p-2 rounded bg-gray-800 text-white"
              />
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  onClick={handleEditComment}
                  className="bg-purple-600 text-white hover:bg-purple-700 transition-colors"
                >
                  수정 완료
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditComment(null)}
                  className="text-purple-800 hover:text-purple-300 border-purple-800 bg-slate-100 hover:bg-slate-50"
                >
                  취소
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-gray-400 text-sm my-2">{comment.content}</p>
          )}
          <div className="flex items-center gap-4 text-sm">
            <p className="text-gray-500 text-xs">{new Date(comment.created_at).toLocaleString()}</p>
            <div className="flex items-center gap-6">
              {/* 좋아요, 싫어요 버튼 (변경 없음) */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleLikeToggle(comment.id);
                }} disabled={loadingLikes[comment.id]}
                className="flex items-center gap-1 text-gray-400 hover:text-blue-400 transition-colors disabled:opacity-50"
              >
                <ThumbsUp className={`h-4 w-4 ${loadingLikes[comment.id] ? "animate-pulse" : ""}`} />
                <span>{comment.like_count}</span>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDislikeToggle(comment.id);
                }} disabled={loadingDislikes[comment.id]}
                className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
              >
                <ThumbsDown className={`h-4 w-4 ${loadingDislikes[comment.id] ? "animate-pulse" : ""}`} />
                <span>{comment.dislike_count}</span>
              </button>
              <div className="flex items-center gap-6">
                {comment.parent === null && (
                  <button
                    onClick={() => setReplyingTo(comment)}
                    className="flex items-center gap-1 text-gray-400 hover:text-green-400 transition-colors"
                  >
                    <CornerDownRight className="h-4 w-4" />
                    <span>답글</span>
                  </button>
                )}
              </div>

            </div>
          </div>
        </div>
        {currentUsername === comment.user && (
          <div className="flex space-x-2 ml-4">
            <Button
              size="sm"
              variant="outline"
              className="text-purple-800 hover:text-purple-300 border-purple-800 bg-slate-100 hover:bg-slate-50"
              onClick={() => setEditComment({ id: comment.id, content: comment.content })}
            >
              수정
            </Button>
            <Button
              size="sm"
              className="bg-purple-600 text-white hover:bg-purple-700"
              onClick={() => handleDeleteComment(comment.id)}
            >
              삭제
            </Button>
          </div>
        )}
      </div>
      {replyingTo?.id === comment.id && !comment.parent && renderReplyForm(comment)}
      {comment.replies &&
        comment.replies.map((reply) => (
          <div key={reply.id} className="ml-8">
            {renderComment(reply)}
          </div>
        ))}
    </div>
  );


  // flattenComments 사용한 코드 제거
  const scrollToComment = useCallback((commentId: number) => {
    if (!movie) return;

    // 인기 댓글과 일반 댓글 모두 탐색
    let targetComment: Comment | undefined;
    let parentComment: Comment | undefined;

    // 최상위 댓글에서 검색
    targetComment = movie.comments.find((comment) => comment.id === commentId);

    // 최상위에서 찾지 못하면 답글에서 검색
    if (!targetComment) {
      for (const comment of movie.comments) {
        if (comment.replies) {
          targetComment = comment.replies.find((reply) => reply.id === commentId);
          if (targetComment) {
            parentComment = comment; // 부모 댓글 참조
            break;
          }
        }
      }
    }

    if (!targetComment) {
      console.warn(`댓글 ID ${commentId}를 찾을 수 없습니다.`);
      return;
    }

    const commentIndex = parentComment
      ? movie.comments.findIndex((comment) => comment.id === parentComment.id)
      : movie.comments.findIndex((comment) => comment.id === targetComment.id);

    const targetPage = Math.ceil((commentIndex + 1) / COMMENTS_PER_PAGE);
    setCurrentPage(targetPage); // 페이지 이동
    setScrollToCommentId(commentId); // 스크롤 대상 댓글 설정
  }, [movie, COMMENTS_PER_PAGE]);

  useEffect(() => {
    if (movie) {
      const commentCount = movie.comments.length || 0;
      setTotalPages(Math.max(1, Math.ceil(commentCount / COMMENTS_PER_PAGE)));
    }
  }, [movie]);

  // 스크롤 효과를 위한 useEffect
  useEffect(() => {
    if (scrollToCommentId !== null) {
      const commentElement = commentRefs.current[scrollToCommentId];
      if (commentElement) {
        commentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        setScrollToCommentId(null);
      }
    }
  }, [scrollToCommentId, currentPage]);

  useEffect(() => {
    if (scrollToCommentId !== null && currentPage) {
      const commentElement = commentRefs.current[scrollToCommentId];
      if (commentElement) {
        setTimeout(() => {
          commentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100); // DOM 업데이트 후 스크롤
        setScrollToCommentId(null); // 초기화
      }
    }
  }, [scrollToCommentId, currentPage, commentRefs]);

  // 영화 데이터 가져오기
  useEffect(() => {
    const fetchMovie = async () => {
      if (movieId) {
        try {
          // 단일 엔드포인트 호출
          const movieResponse = await api.get(`/movies/${movieId}/`);

          // 필요한 데이터를 직접 할당
          const movieData: Movie = {
            ...movieResponse.data,
            trailer_link: movieResponse.data.trailer_link, // 이미 포함된 트레일러 링크
            related_movies: movieResponse.data.related_movies, // 이미 포함된 관련 영화
            reviews: movieResponse.data.reviews // 이미 포함된 리뷰
          };

          setMovie(movieData);
          setIsFavorite(movieData.is_liked);
          setTotalPages(Math.ceil((movieData.comments.length || 0) / COMMENTS_PER_PAGE));
        } catch (error) {
          console.error('Error fetching movie:', error);
        }
      }
    };
    fetchMovie();
  }, [movieId]);

  function getYouTubeEmbedUrl(url: string) {
    const videoId = url.split('v=')[1];
    return `https://www.youtube.com/embed/${videoId}`;
  }

  if (!movie) {
    return null
  }

  return (
    <Dialog open={!!movieId} onOpenChange={(isOpen) => {
      if (!isOpen) {
        handleClose();
      } else if (typeof onOpen === 'function') {
        onOpen();
      }
    }}>
      <DialogContent className="max-w-[80vw] w-[90vw] h-[90vh] p-0 overflow-hidden bg-gray-900/95 backdrop-blur-sm text-gray-100 border-gray-800">
        <ScrollArea className="h-full">
          <div className="p-6">
            <div id="movie-detail-description" className="sr-only">
              영화의 상세 정보를 보여주는 모달입니다. 포스터, 줄거리, 출연진, 관련 영화 등의 정보를 확인할 수 있습니다.
            </div>
            <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
              <X className="h-4 w-4" />
              <span className="sr-only">닫기</span>
            </DialogClose>
            <DialogTitle className="sr-only">영화 상세 정보</DialogTitle>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 왼쪽 열 (포스터, 즐겨찾기 버튼, 관련 기사) */}
              <div className="md:col-span-1">
                <div className="aspect-[2/3] w-full mb-4">
                  <img src={movie.poster_path} alt={movie.title} className="w-full h-full object-cover rounded-lg shadow-lg" />
                </div>
                <Button
                  onClick={toggleFavorite}
                  variant={isFavorite ? "default" : "outline"}
                  className={`w-full mb-4 transition-colors ${isFavorite
                    ? "bg-purple-600 text-white hover:bg-purple-700"
                    : "bg-gray-800 text-gray-200 hover:bg-gray-700"
                    }`}
                >
                  <Heart className={`mr-2 h-4 w-4 ${isFavorite ? "fill-current" : ""}`} />
                  {isFavorite ? "즐겨찾기 해제" : "즐겨찾기 추가"}
                </Button>
                <Card className="bg-gray-800/50 backdrop-blur-sm border-gray-700 mb-4">
                  <CardContent className="p-4">
                    <h2 className="text-lg font-bold mb-3 text-white">관련 기사</h2>
                    <ScrollArea className="h-[200px]">
                      <ul className="space-y-2">
                        {movie.news && movie.news.map((article, index) => (
                          <li key={index} className="text-purple-300 hover:text-purple-200 transition-colors">
                            <a
                              href={article.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block truncate"
                            >
                              {article.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </div>

              {/* 오른쪽 열 (영화 정보, 탭) */}
              <div className="md:col-span-2">
                <h1 className="text-4xl font-bold mb-4 text-white">{movie.title}</h1>
                <div className="flex flex-wrap items-center gap-4 mb-6">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-200">{movie.release_date}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                    <span className="text-gray-200">{movie.normalized_popularity.toFixed(1)}</span>
                  </div>
                  {movie.trailer_link && (
                    <div className="flex items-center gap-4">
                      <div
                        className="flex items-center gap-2 text-red-400 hover:text-red-300 cursor-pointer transition-colors"
                        onClick={() => setShowTrailer(true)}
                      >
                        <Play className="w-4 h-4" />
                        <span>예고편 보기</span>
                      </div>
                      <a
                        href={movie.trailer_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        바로가기
                      </a>
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {movie.genres && movie.genres.map((genre) => (
                    <Badge key={genre} variant="secondary" className="bg-purple-600/90 backdrop-blur-sm text-white">
                      {genre}
                    </Badge>
                  ))}
                </div>
                <p className="text-gray-300 mb-6">{movie.overview}</p>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-4 bg-gray-800/50 backdrop-blur-sm">
                    <TabsTrigger
                      value="cast"
                      className="text-gray-300 data-[state=active]:bg-purple-600 data-[state=active]:text-white"
                    >
                      출연진 & 제작진
                    </TabsTrigger>
                    <TabsTrigger
                      value="related"
                      className="text-gray-300 data-[state=active]:bg-purple-600 data-[state=active]:text-white"
                    >
                      관련 영화
                    </TabsTrigger>
                    <TabsTrigger
                      value="comments"
                      className="text-gray-300 data-[state=active]:bg-purple-600 data-[state=active]:text-white"
                    >
                      댓글
                    </TabsTrigger>
                    <TabsTrigger
                      value="reviews"
                      className="text-gray-300 data-[state=active]:bg-purple-600 data-[state=active]:text-white"
                    >
                      리뷰
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="cast" className="mt-4">
                    <div className="space-y-6">
                      <div>
                        <h2 className="text-xl font-semibold mb-2 text-white">출연진</h2>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                          {paginatedCast.map((member) => (
                            <Card
                              key={member.actor_id}
                              className="bg-gray-800/50 backdrop-blur-sm border-gray-700 overflow-hidden hover:bg-gray-700/50 transition-all cursor-pointer"
                              onClick={() => handlePersonClick(member.actor_id, 'actor')}
                            >
                              <CardContent className="p-2">
                                <div className="aspect-[2/3] w-full mb-2">
                                  <img src={member.actor_profile_path} alt={member.actor_name} className="w-full h-full object-cover" />
                                </div>
                                <h3 className="font-semibold truncate text-sm text-gray-200">{member.actor_name}</h3>
                                <p className="text-xs text-gray-400 truncate">{member.character_name}</p>
                              </CardContent>
                            </Card>
                          ))}
                        </div>

                        {/* 페이지네이션 */}
                        <div className="flex justify-center items-center mt-4 space-x-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleCastPageChange(castPage - 1)}
                            disabled={castPage === 1}
                            className="w-8 h-8 p-0"
                          >
                            <ChevronLeft className="h-4 w-4 text-gray-400" />
                            <span className="sr-only">이전 페이지</span>
                          </Button>
                          <span className="text-sm text-gray-400">
                            {castPage} / {castTotalPages}
                          </span>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleCastPageChange(castPage + 1)}
                            disabled={castPage === castTotalPages}
                            className="w-8 h-8 p-0"
                          >
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                            <span className="sr-only">다음 페이지</span>
                          </Button>
                        </div>
                      </div>
                      {/* 기존 제작진 섹션 */}
                      <div>
                        <h2 className="text-xl font-semibold mb-2 text-white">제작진</h2>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                          {movie.crews && movie.crews.map((crew) => (
                            <Card
                              key={crew.id}
                              className="bg-gray-800/50 backdrop-blur-sm border-gray-700 overflow-hidden hover:bg-gray-700/50 transition-all cursor-pointer"
                              onClick={() => handlePersonClick(crew.id, 'director')}
                            >
                              <CardContent className="p-2">
                                <div className="aspect-[2/3] w-full mb-2">
                                  <img src={crew.profile_path} alt={crew.name} className="w-full h-full object-cover" />
                                </div>
                                <h3 className="font-semibold truncate text-sm text-gray-200">{crew.name}</h3>
                                <p className="text-xs text-gray-400 truncate">{crew.job}</p>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="related" className="mt-4">
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                      {movie.related_movies && movie.related_movies.map((relatedMovie) => (
                        <Card
                          key={relatedMovie.id}
                          className="bg-gray-800/50 backdrop-blur-sm border-gray-700 overflow-hidden hover:bg-gray-700/50 transition-all cursor-pointer"
                          onClick={() => handleRelatedMovieClick(relatedMovie.id)}
                        >
                          <CardContent className="p-2">
                            <div className="aspect-[2/3] w-full mb-2">
                              <img src={relatedMovie.poster_path} alt={relatedMovie.title} className="w-full h-full object-cover" />
                            </div>
                            <h3 className="font-semibold truncate text-sm text-gray-200">{relatedMovie.title}</h3>
                            <div className="flex items-center mt-1">
                              <Star className="w-3 h-3 text-yellow-400 fill-current mr-1" />
                              <span className="text-xs text-gray-300">{relatedMovie.normalized_popularity.toFixed(1)}</span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>
                  <TabsContent value="comments" className="mt-4">
                    <div className="space-y-4">
                      <h2 className="text-lg font-semibold">댓글</h2>

                      {/* 댓글 추가 폼 */}
                      <div className="space-y-2">
                        <Textarea
                          value={newComment}
                          onChange={(e) => setNewComment(e.target.value)}
                          placeholder="새 댓글을 입력하세요"
                          className="w-full border border-gray-700 p-2 rounded bg-gray-800 text-white"
                        />
                        <Button
                          onClick={handleAddComment}
                          className="bg-purple-600 text-white hover:bg-purple-700 transition-colors"
                        >
                          <MessageSquare className="w-4 h-4 mr-2" />
                          댓글 추가
                        </Button>
                      </div>

                      {/* 인기 댓글 섹션 */}
                      <div ref={commentsSectionRef} className="space-y-4">
                        <h2 className="text-xl font-bold text-white">인기 댓글</h2>
                        <div className="space-y-2">
                          {topComments.map((comment) => (
                            <div
                              key={comment.id}
                              onClick={() => scrollToComment(comment.id)}
                              className="cursor-pointer hover:bg-gray-700/50 p-2 rounded-lg transition-colors"
                            >
                              <div className="flex justify-between items-start bg-gray-800/50 p-4 rounded-lg">
                                <div className="flex-1">
                                  <p className="text-gray-300">{comment.user}</p>
                                  <p className="text-gray-400 text-sm my-2">{comment.content}</p>
                                  <div className="flex items-center gap-4 text-sm">
                                    <p className="text-gray-500 text-xs">{new Date(comment.created_at).toLocaleString()}</p>
                                    <div className="flex items-center gap-6">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleLikeToggle(comment.id);
                                        }}
                                        disabled={loadingLikes[comment.id]}
                                        className="flex items-center gap-1 text-gray-400 hover:text-blue-400 transition-colors disabled:opacity-50"
                                      >
                                        <ThumbsUp className={`h-4 w-4 ${loadingLikes[comment.id] ? "animate-pulse" : ""}`} />
                                        <span>{comment.like_count}</span>
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDislikeToggle(comment.id);
                                        }}
                                        disabled={loadingDislikes[comment.id]}
                                        className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
                                      >
                                        <ThumbsDown className={`h-4 w-4 ${loadingDislikes[comment.id] ? "animate-pulse" : ""}`} />
                                        <span>{comment.dislike_count}</span>
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 댓글 섹션 */}
                      <div className="space-y-4">
                        <h2 className="text-xl font-bold text-white">댓글</h2>
                        {paginatedComments.length === 0 ? (
                          <p className="text-gray-400 text-center my-4">아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!</p>
                        ) : (
                          <div className="space-y-4">
                            {paginatedComments.map((comment) => renderComment(comment))}
                          </div>
                        )}
                      </div>

                      {/* 페이지네이션 */}
                      <div className="flex justify-center items-center mt-4 space-x-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handlePageChange(currentPage - 1)}
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
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={currentPage === totalPages}
                          className="w-8 h-8 p-0"
                        >
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                          <span className="sr-only">다음 페이지</span>
                        </Button>
                      </div>
                    </div>
                  </TabsContent>
                  <TabsContent value="reviews" className="mt-4">
                    <ReviewsTab reviews={movie?.reviews || []} />
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>

      {/* Main Modal */}
      <Dialog open={!!movieId} onOpenChange={() => setShowTrailer(false)}>
        {/* Other modal content */}
        {movieId && (
          <>
            <button onClick={() => setShowTrailer(true)}>Open Trailer</button>
          </>
        )}
      </Dialog>

      {/* 트레일러 모달 */}
      <Dialog open={showTrailer} onOpenChange={setShowTrailer}>
        <DialogContent className="max-w-7xl bg-gray-900/95 backdrop-blur-sm text-gray-100 border-gray-800 p-6">
          <DialogTitle>예고편</DialogTitle>
          <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
            <X className="h-4 w-4" />
            <span className="sr-only">닫기</span>
          </DialogClose>
          <div className="aspect-video flex justify-center items-center">
            <iframe
              width="100%"
              height="100%"
              src={movie?.trailer_link ? getYouTubeEmbedUrl(movie.trailer_link) : ""}
              title="Movie Trailer"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </DialogContent>
      </Dialog>
    </Dialog>
  )
}

