'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { Dialog, DialogContent, DialogClose, DialogTitle } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area1";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Star, X, Heart, Calendar, MapPin, ChevronLeft, ChevronRight, ThumbsUp, ThumbsDown, MessageSquare, CornerDownRight, Edit, Trash2 } from 'lucide-react';
import api, { getCurrentUserId } from "@/lib/api";

// 인터페이스 정의
interface Movie {
  id: number;
  title: string;
  release_date: string;
  poster_path: string;
  normalized_popularity: number;
  character?: string;
  job?: string;
}

interface NotableRole {
  character_name?: string;
  movie_title: string;
  id: number;
  job?: string;
}

interface Comment {
  id: number;
  user: string;
  user_id: number;
  content: string;
  created_at: string;
  like_count: number;
  dislike_count: number;
  parent: number | null;
  actor: number | null;
  director: number | null;
  replies?: Comment[];
}

interface Person {
  id: number;
  profile_path: string;
  name: string;
  gender: string;
  birthdate: string;
  birthplace: string;
  biography: string;
  filmography: Movie[];
  comments: Comment[];
  notable_roles: NotableRole[];
  is_liked: boolean;
}

interface PersonProfileModalProps {
  personId: string;
  personType: 'actor' | 'director';
  onClose: () => void;  // onClose prop 추가
  onOpen?: () => void;
}

export default function PersonProfileModal({ personId, personType, onClose, onOpen }: PersonProfileModalProps) {
  const [person, setPerson] = useState<Person | null>(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [activeTab, setActiveTab] = useState('filmography');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<Comment | null>(null);
  const [editComment, setEditComment] = useState<{ id: number; content: string } | null>(null);
  const [loadingLikes, setLoadingLikes] = useState<{ [key: number]: boolean }>({});
  const [loadingDislikes, setLoadingDislikes] = useState<{ [key: number]: boolean }>({});
  const [topComments, setTopComments] = useState<Comment[]>([]);
  const [scrollToCommentId, setScrollToCommentId] = useState<number | null>(null);
  const currentUsername = localStorage.getItem('nickname') || sessionStorage.getItem('nickname')
  const commentRefs = useRef<{ [key: number]: HTMLDivElement }>({});
  const commentsSectionRef = useRef<HTMLDivElement | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const COMMENTS_PER_PAGE = 10;

  const fetchPersonDetails = useCallback(async () => {
    if (!personId) return;

    try {
      const response = await api.get(`/movies/${personType}s/${personId}/`);
      const data = response.data;

      setPerson(data);
      setIsFavorite(data.is_liked);
      setTotalPages(Math.ceil(data.comments.length / COMMENTS_PER_PAGE));
    } catch (error) {
      console.error(`Error fetching ${personType} details:`, error);
    }
  }, [personId, personType]);

  const toggleFavorite = async () => {
    if (!person) return;

    try {
      const response = await api.post(`/movies/${personType}s/${personId}/like/`);
      if (response.status === 200) {
        setIsFavorite(!isFavorite);
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

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

  // Modify the scrollToComment function to use smooth scrolling
  const scrollToComment = useCallback((commentId: number) => {
    if (!person) return;

    let targetComment: Comment | undefined;
    let parentComment: Comment | undefined;

    // 먼저 최상위 댓글에서 찾기
    targetComment = person.comments.find(comment => comment.id === commentId);

    // 최상위 댓글에서 찾지 못했다면 답글에서 찾기
    if (!targetComment) {
      for (const comment of person.comments) {
        if (comment.replies) {
          targetComment = comment.replies.find(reply => reply.id === commentId);
          if (targetComment) {
            parentComment = comment;
            break;
          }
        }
      }
    }

    if (!targetComment) {
      console.warn(`Comment with id ${commentId} not found`);
      return;
    }

    const commentIndex = parentComment
      ? person.comments.findIndex(comment => comment.id === parentComment.id)
      : person.comments.findIndex(comment => comment.id === targetComment.id);

    if (commentIndex === -1) {
      console.warn(`Comment index not found for id ${commentId}`);
      return;
    }

    const targetPage = Math.ceil((commentIndex + 1) / COMMENTS_PER_PAGE);
    setCurrentPage(targetPage);
    setScrollToCommentId(commentId);
  }, [person, COMMENTS_PER_PAGE]);

  const handleMovieClick = useCallback((movieId: number) => {
    const currentParams = new URLSearchParams(searchParams.toString())
    currentParams.set('movieId', movieId.toString())
    currentParams.delete('personId')
    currentParams.delete('personType')

    router.push(`${pathname}?${currentParams.toString()}`, { scroll: false })
    if (typeof onOpen === 'function') {
      onOpen()
    }
  }, [router, searchParams, pathname, onOpen])

  const handleClose = useCallback(() => {
    const currentParams = new URLSearchParams(searchParams.toString())
    currentParams.delete('personId')
    currentParams.delete('personType')

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
  }, [router, searchParams, pathname, onClose]);

  // Modify the handlePageChange function to ensure proper scrolling
  const handlePageChange = useCallback((newPage: number) => {
    const maxPage = person ? Math.max(1, Math.ceil(person.comments.length / COMMENTS_PER_PAGE)) : 1;
    const validatedPage = Math.max(1, Math.min(newPage, maxPage));
    setCurrentPage(validatedPage);
    setTimeout(() => {
      if (commentsSectionRef.current) {
        commentsSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, 200);
  }, [person]);

  const handleAddComment = async () => {
    if (!newComment.trim() || !personId) return;

    try {
      const response = await api.post(`/movies/${personType}s/${personId}/comments/`, {
        content: newComment,
        parent: null,
      });

      if (response.status === 201) {
        const createdComment = response.data;
        setPerson((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            comments: [createdComment, ...prev.comments],
          };
        });
        setNewComment("");
        setCurrentPage(1);
        setScrollToCommentId(createdComment.id);
      }
    } catch (error) {
      console.error("댓글 생성 실패:", error);
    }
  };

  const handleAddReply = async (event: React.MouseEvent<HTMLButtonElement>, parent: number) => {
    event.preventDefault();
    if (!newComment.trim() || !personId) return;

    try {
      const response = await api.post(`/movies/${personType}s/${personId}/comments/`, {
        content: newComment,
        parent,
      });

      if (response.status === 201) {
        const createdReply = response.data;

        setPerson((prev) => {
          if (!prev) return prev;

          // 재귀적으로 댓글과 답글을 업데이트하는 함수
          const addReplyToComments = (comments: Comment[]): Comment[] =>
            comments.map((comment) => {
              if (comment.id === parent) {
                return {
                  ...comment,
                  replies: [...(comment.replies || []), createdReply],
                };
              }
              if (comment.replies) {
                return { ...comment, replies: addReplyToComments(comment.replies) };
              }
              return comment;
            });

          return {
            ...prev,
            comments: addReplyToComments(prev.comments),
          };
        });

        setNewComment(""); // 입력 필드 초기화
        setReplyingTo(null); // 답글 작성 종료
        setScrollToCommentId(createdReply.id); // 새로 추가된 답글로 스크롤
      }
    } catch (error) {
      console.error("답글 추가 중 오류 발생:", error);
    }
  };


  // 스크롤 효과를 위한 useEffect 추가
  useEffect(() => {
    if (scrollToCommentId !== null) {
      const commentElement = commentRefs.current[scrollToCommentId];
      if (commentElement) {
        commentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        setScrollToCommentId(null);
      }
    }
  }, [scrollToCommentId, currentPage]);

  const handleEditComment = async () => {
    if (!editComment || !editComment.content.trim()) return;

    try {
      const response = await api.put(`/movies/${personType}s/${personId}/comments/${editComment.id}/update/`, {
        content: editComment.content,
      });

      if (response.status === 200) {
        const updatedComment = response.data;

        setPerson((prev) => {
          if (!prev) return prev;

          // 재귀적으로 댓글과 답글을 업데이트하는 함수
          const updateComments = (comments: Comment[]): Comment[] =>
            comments.map((comment) => {
              if (comment.id === updatedComment.id) {
                return { ...comment, content: updatedComment.content };
              }
              if (comment.replies) {
                return { ...comment, replies: updateComments(comment.replies) };
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


  const handleDeleteComment = async (commentId: number) => {
    try {
      const response = await api.delete(`/movies/${personType}s/${personId}/comments/${commentId}/delete/`);

      if (response.status === 204) {
        setPerson((prev) => {
          if (!prev) return prev;
          const deleteComments = (comments: Comment[]): Comment[] =>
            comments
              .filter((comment) => comment.id !== commentId)
              .map((comment) => ({
                ...comment,
                replies: comment.replies ? deleteComments(comment.replies) : [],
              }));
          return {
            ...prev,
            comments: deleteComments(prev.comments),
          };
        });
      }
    } catch (error) {
      console.error("댓글 삭제 실패:", error);
    }
  };

  // 좋아요 토글 함수 수정
  const handleLikeToggle = async (event: React.MouseEvent, commentId: number) => {
    event.preventDefault();
    event.stopPropagation();
    if (loadingLikes[commentId] || loadingDislikes[commentId]) return;

    setLoadingLikes((prev) => ({ ...prev, [commentId]: true }));
    try {
      const response = await api.post(`/community/comments/${commentId}/like-toggle/`);
      if (response.status === 200) {
        setPerson((prev) => {
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

  // 싫어요 토글 함수 수정
  const handleDislikeToggle = async (event: React.MouseEvent, commentId: number) => {
    event.preventDefault();
    event.stopPropagation();
    if (loadingLikes[commentId] || loadingDislikes[commentId]) return;

    setLoadingDislikes((prev) => ({ ...prev, [commentId]: true }));
    try {
      const response = await api.post(`/community/comments/${commentId}/dislike-toggle/`);
      if (response.status === 200) {
        setPerson((prev) => {
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

  useEffect(() => {
    fetchPersonDetails();
  }, [fetchPersonDetails]);

  useEffect(() => {
    if (person) {
      setTotalPages(Math.max(1, Math.ceil(person.comments.length / COMMENTS_PER_PAGE)));

      // 인기 댓글 계산 로직 수정
      const allComments = person.comments.reduce<Comment[]>((acc, comment) => {
        if (comment.like_count > 0) {
          acc.push(comment);
        }
        if (comment.replies) {
          acc.push(...comment.replies.filter(reply => reply.like_count > 0));
        }
        return acc;
      }, []);

      setTopComments(allComments.sort((a, b) => b.like_count - a.like_count).slice(0, 5));
    }
  }, [person]);

  const paginatedFilmography = useMemo(() => {
    if (!person) return [];
    const startIndex = (currentPage - 1) * 4;
    const endIndex = startIndex + 4;
    return person.filmography.slice(startIndex, endIndex);
  }, [person, currentPage]);

  const paginatedComments = useMemo(() => {
    if (!person) return [];
    const startIndex = (currentPage - 1) * COMMENTS_PER_PAGE;
    const endIndex = startIndex + COMMENTS_PER_PAGE;
    return person.comments.slice(startIndex, endIndex);
  }, [person, currentPage]);

  // ... (이전 코드는 그대로 유지)

  const renderTopComment = useCallback((comment: Comment) => (
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
                  handleLikeToggle(e, comment.id);
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
                  handleDislikeToggle(e, comment.id);
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
  ), [scrollToComment, handleLikeToggle, handleDislikeToggle, loadingLikes, loadingDislikes]);

  const renderComment = useCallback((comment: Comment) => (
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
              <button
                onClick={(e) => handleLikeToggle(e, comment.id)}
                disabled={loadingLikes[comment.id]}
                className="flex items-center gap-1 text-gray-400 hover:text-blue-400 transition-colors disabled:opacity-50"
              >
                <ThumbsUp className={`h-4 w-4 ${loadingLikes[comment.id] ? "animate-pulse" : ""}`} />
                <span>{comment.like_count}</span>
              </button>
              <button
                onClick={(e) => handleDislikeToggle(e, comment.id)}
                disabled={loadingDislikes[comment.id]}
                className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
              >
                <ThumbsDown className={`h-4 w-4 ${loadingDislikes[comment.id] ? "animate-pulse" : ""}`} />
                <span>{comment.dislike_count}</span>
              </button>
              {!comment.parent && (
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
      {replyingTo?.id === comment.id && renderReplyForm(comment)}
      {comment.replies &&
        comment.replies.map((reply) => (
          <div key={reply.id} className="ml-8">
            {renderComment(reply)}
          </div>
        ))}
    </div>
  ), [editComment, handleEditComment, handleLikeToggle, handleDislikeToggle, loadingLikes, loadingDislikes, currentUsername, topComments, handleDeleteComment, renderReplyForm]);

  // ... (나머지 코드는 그대로 유지)



  if (!person) {
    return null;
  }

  return (
    <Dialog open={!!personId} onOpenChange={(isOpen) => {
      if (!isOpen) {
        handleClose();
      } else if (typeof onOpen === 'function') {
        onOpen();
      }
    }}>
      <DialogContent
        className="max-w-[80vw] w-[90vw] max-h-[90vh] overflow-hidden bg-gray-900/95 backdrop-blur-sm text-gray-100 border-gray-800"
        aria-describedby="person-profile-description"
      >
        <div id="person-profile-description" className="sr-only">
          {personType === 'actor' ? '배우' : '감독'}의 프로필 정보를 보여주는 모달입니다. 프로필 사진, 약력, 작품, 관련 정보를 확인할 수 있습니다.
        </div>
        <DialogTitle className="sr-only">{personType === 'actor' ? 'Actor' : 'Director'} Profile: {person.name}</DialogTitle>
        <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DialogClose>
        <ScrollArea className="h-[calc(90vh-4rem)] pr-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1">
              <div className="aspect-[2/3] w-full mb-4">
                <img src={person.profile_path} alt={person.name} className="w-full h-full object-cover rounded-lg shadow-lg" />
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
                  <h2 className="text-lg font-bold mb-3 text-white">주요 정보</h2>
                  <div className="space-y-2 text-sm text-gray-300">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                      <span>출생: {person.birthdate}</span>
                    </div>
                    <div className="flex items-center">
                      <MapPin className="w-4 h-4 mr-2 text-gray-400" />
                      <span>{person.birthplace}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            <div className="md:col-span-2">
              <h1 className="text-3xl font-bold mb-4 text-white">{person.name}</h1>
              <ScrollArea className="h-[200px] mb-6">
                <p className="text-gray-300">{person.biography}</p>
              </ScrollArea>
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2 text-white">주요 {personType === 'actor' ? '출연작' : '작품'}</h2>
                <div className="flex flex-wrap gap-2">
                  {person.notable_roles && person.notable_roles.map((role) => (
                    <Badge key={role.id} variant="secondary" className="bg-gray-700 text-gray-200">
                      {personType === 'actor' ? `${role.character_name} (${role.movie_title})` : `${role.job} (${role.movie_title})`}
                    </Badge>
                  ))}
                </div>
              </div>
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 bg-gray-800/50 backdrop-blur-sm">
                  <TabsTrigger value="filmography" className="data-[state=active]:bg-purple-600">필모그래피</TabsTrigger>
                  <TabsTrigger value="comments" className="data-[state=active]:bg-purple-600">댓글</TabsTrigger>
                </TabsList>
                <TabsContent value="filmography" className="mt-4">
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                    {paginatedFilmography.map((movie) => (
                      <Card
                        key={movie.id}
                        className="bg-gray-800/50 backdrop-blur-sm border-gray-700 overflow-hidden hover:bg-gray-700/50 transition-all cursor-pointer"
                        onClick={() => handleMovieClick(movie.id)}
                      >
                        <div className="aspect-[2/3] w-full">
                          <img src={movie.poster_path} alt={movie.title} className="w-full h-full object-cover" />
                        </div>
                        <CardContent className="p-2">
                          <h3 className="font-semibold truncate text-sm text-gray-200">{movie.title}</h3>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-xs text-gray-400">{new Date(movie.release_date).getFullYear()}</span>
                            <div className="flex items-center">
                              <Star className="w-3 h-3 text-yellow-400 fill-current mr-1" />
                              <span className="text-xs text-gray-200">{movie.normalized_popularity.toFixed(1)}</span>
                            </div>
                          </div>
                          {personType === 'actor' && movie.character && (
                            <p className="text-xs text-gray-400 mt-1 truncate">역할: {movie.character}</p>
                          )}
                          {personType === 'director' && movie.job && (
                            <p className="text-xs text-gray-400 mt-1 truncate">직책: {movie.job}</p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
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
                </TabsContent>
                <TabsContent value="comments" className="mt-4">
                  <div className="space-y-4">
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
                    <div ref={commentsSectionRef} className="space-y-2">
                      <h2 className="text-xl font-bold text-white">인기 댓글</h2>
                      <div className="space-y-2">
                        {topComments.map((comment) => renderTopComment(comment))}
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
                        {currentPage} / {Math.max(1, totalPages)}
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
              </Tabs>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
