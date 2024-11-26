'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { DarkModeToggle } from '@/components/DarkModeToggle';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Search, PlusCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { Post, Review, PostDetail, ReviewDetail } from '@/types/community';
import { PostList } from '@/components/community/PostList';
import { ReviewList } from '@/components/community/ReviewList';
import { ItemDetail } from '@/components/community/ItemDetail';
import { CreateItemForm } from '@/components/community/CreateItemForm';
import { RecommendationModal } from '@/components/RecommendationModal';
import api from '@/lib/api';
import MovieDetailModal from '@/components/MovieDetailModal';
import PersonProfileModal from '@/components/PersonProfileModal';

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState('posts');
  const [searchType, setSearchType] = useState('title');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortType, setSortType] = useState('created_at_desc');
  const [posts, setPosts] = useState<Post[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedItem, setSelectedItem] = useState<PostDetail | ReviewDetail | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isRecommendationModalOpen, setIsRecommendationModalOpen] = useState(false);
  const [recommendations, setRecommendations] = useState({
    personalized_recommendations: [],
    keyword_based_recommendations: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter()
  const searchParams = useSearchParams()
  const movieId = searchParams.get('movieId')
  const personId = searchParams.get('personId')
  const personType = searchParams.get('personType') as 'actor' | 'director' | null
  const [scrollPosition, setScrollPosition] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollPosition(window.pageYOffset);
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleOpenModal = useCallback(() => {
    setScrollPosition(window.pageYOffset);
  }, []);

  const handleCloseModal = useCallback(() => {
    const newSearchParams = new URLSearchParams(searchParams.toString())
    newSearchParams.delete('movieId')
    newSearchParams.delete('personId')
    newSearchParams.delete('personType')
    router.push(`/community?${newSearchParams.toString()}`, { scroll: false })
    setTimeout(() => {
      window.scrollTo(0, scrollPosition);
    }, 0);
  }, [searchParams, router, scrollPosition])

  const fetchItems = useCallback(async () => {
    try {
      const endpoint = activeTab === 'posts' ? '/community/posts/' : '/community/reviews/';
      const params: Record<string, any> = {
        sort: sortType,
        page: currentPage,
        page_size: 9,
      };

      if (searchQuery) {
        params.query = searchQuery;
        params.search_type = searchType;
      }

      const response = await api.get(endpoint, { params });
      if (activeTab === 'posts') {
        setPosts(response.data.results);
      } else {
        setReviews(response.data.results);
      }
      setTotalPages(Math.ceil(response.data.count / 10));
    } catch (error) {
      console.error('데이터 로드 실패:', error);
    }
  }, [activeTab, sortType, currentPage, searchQuery, searchType]);

  useEffect(() => {
    fetchItems();
  }, [currentPage, activeTab, sortType, searchQuery, fetchItems]);

  const handleSearch = () => {
    setCurrentPage(1);
    fetchItems();
  };

  const handleSort = (type: string) => {
    setSortType(type);
    setCurrentPage(1);
  };

  const handleCreateItem = async (item: { title: string; content: string; rating?: number }) => {
    try {
      const endpoint = activeTab === 'posts' ? '/community/posts/create/' : '/community/reviews/create/';
      const response = await api.post(endpoint, item);
      if (response.status === 201) {
        setIsCreateDialogOpen(false);
        setCurrentPage(1);
        fetchItems();
      } else {
        throw new Error('아이템 생성에 실패했습니다!');
      }
    } catch (error) {
      console.error('아이템 생성 실패:', error);
    }
  };

  const handleLikeToggle = async (id: number, type: 'post' | 'review') => {
    try {
      const endpoint = `/community/${type}s/${id}/like-toggle/`;
      const response = await api.post(endpoint);
      if (response.status === 200) {
        const updatedLikeCount = response.data.like_count;
        if (type === 'post') {
          setPosts((prevPosts) =>
            prevPosts.map((post) =>
              post.id === id ? { ...post, like_count: updatedLikeCount } : post
            )
          );
        } else {
          setReviews((prevReviews) =>
            prevReviews.map((review) =>
              review.id === id ? { ...review, like_count: updatedLikeCount } : review
            )
          );
        }
        if (selectedItem && selectedItem.id === id) {
          setSelectedItem({ ...selectedItem, like_count: updatedLikeCount });
        }
      }
    } catch (error) {
      console.error('좋아요 토글 실패:', error);
    }
  };

  const handleCommentSubmit = async (itemId: number, content: string, parentId: number | null) => {
    try {
      const endpoint = activeTab === 'posts'
        ? `/community/posts/${itemId}/comments/`
        : `/community/reviews/${itemId}/comments/`;

      const response = await api.post(endpoint, {
        content,
        parent: parentId,
      });

      if (response.status === 201) {
        await fetchItemDetail(itemId, activeTab === 'posts' ? 'post' : 'review');
      }
    } catch (error) {
      console.error('댓글 작성 실패:', error);
    }
  };

  const fetchItemDetail = async (id: number, type: 'post' | 'review') => {
    try {
      const endpoint = `/community/${type}s/${id}/`;
      const response = await api.get(endpoint);
      setSelectedItem(response.data.results);
    } catch (error) {
      console.error('아이템 상세 로드 실패:', error);
    }
  };

  const fetchRecommendations = async (keyword: string) => {
    try {
      setIsLoading(true);
      const response = await api.post('/movies/recommendations_view', {
        keyword: keyword || '추천 키워드',
      });
      setRecommendations(response.data);
      setIsRecommendationModalOpen(true);
    } catch (error) {
      console.error('추천 데이터 로드 실패:', error);
      alert('추천 데이터를 불러오는 데 실패했습니다. 다시 시도해주세요!');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const renderPagination = () => {
    const pageNumbers = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(
        <Button
          key={i}
          onClick={() => handlePageChange(i)}
          variant={currentPage === i ? "default" : "outline"}
          className="mx-1"
        >
          {i}
        </Button>
      );
    }

    return (
      <div className="flex items-center justify-center mt-4 space-x-2">
        <Button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          variant="outline"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        {pageNumbers}
        <Button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          variant="outline"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    );
  };

  const sortOptions =
    activeTab === 'posts'
      ? ['created_at_desc', 'created_at_asc', 'comments_desc', 'likes_desc']
      : ['created_at_desc', 'created_at_asc', 'comments_desc', 'likes_desc', 'rating_desc', 'rating_asc'];

  return (
    <div className="bg-background text-foreground py-16">
      <div className="container mx-auto p-4 my-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">커뮤니티</h1>
          <DarkModeToggle />
        </div>
        <Tabs value={activeTab} onValueChange={(value) => { setActiveTab(value); setCurrentPage(1); }}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="posts">자유게시판</TabsTrigger>
            <TabsTrigger value="reviews">리뷰게시판</TabsTrigger>
          </TabsList>
          <TabsContent value="posts">
            <h2 className="text-2xl font-bold mb-4">자유게시판</h2>
          </TabsContent>
          <TabsContent value="reviews">
            <h2 className="text-2xl font-bold mb-4">리뷰게시판</h2>
          </TabsContent>
        </Tabs>

        <div className="flex space-x-2 mb-4">
          <Select value={searchType} onValueChange={setSearchType}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="검색 유형" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="author">작성자</SelectItem>
              <SelectItem value="title">제목</SelectItem>
              <SelectItem value="title_content">제목+내용</SelectItem>
              <SelectItem value="title_content_comment">제목+내용+댓글</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="text"
            placeholder="검색어를 입력하세요"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Button onClick={handleSearch}>
            <Search className="mr-2 h-4 w-4" /> 검색
          </Button>
        </div>

        <div className="mb-4 flex justify-between items-center">
          <Select value={sortType} onValueChange={handleSort}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="정렬 기준" />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {option === 'created_at_desc' && '최신순'}
                  {option === 'created_at_asc' && '오래된순'}
                  {option === 'comments_desc' && '댓글 많은순'}
                  {option === 'likes_desc' && '좋아요 많은순'}
                  {option === 'rating_desc' && '별점 높은순'}
                  {option === 'rating_asc' && '별점 낮은순'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <PlusCircle className="mr-2 h-4 w-4" /> 새 {activeTab === 'posts' ? '게시글' : '리뷰'} 작성
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>새 {activeTab === 'posts' ? '게시글' : '리뷰'} 작성</DialogTitle>
                <DialogDescription>
                  {activeTab === 'posts' ? '새로운 게시글을 작성하세요.' : '새로운 리뷰를 작성하세요.'}
                </DialogDescription>
              </DialogHeader>
              <CreateItemForm type={activeTab === 'posts' ? 'post' : 'review'} onSubmit={handleCreateItem} />
            </DialogContent>
          </Dialog>
        </div>

        <Button
          onClick={() => fetchRecommendations(searchQuery)}
          className="mb-4 w-full bg-blue-500 text-white hover:bg-blue-600"
        >
          {isLoading ? '불러오는 중...' : '추천 보기'}
        </Button>

        {activeTab === 'posts' ? (
          <PostList posts={posts} onPostClick={(id) => fetchItemDetail(id, 'post')} />
        ) : (
          <ReviewList reviews={reviews} onReviewClick={(id) => fetchItemDetail(id, 'review')} />
        )}

        {renderPagination()}

        {selectedItem && (
          <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
            <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                {/* 제목과 설명을 빈 문자열로 렌더링 */}
                <DialogTitle>{''}</DialogTitle>
                <DialogDescription>{''}</DialogDescription>
              </DialogHeader>
              <ItemDetail
                item={selectedItem}
                onLikeToggle={() =>
                  handleLikeToggle(selectedItem.id, activeTab === 'reviews' ? 'review' : 'post')
                }
                onCommentSubmit={(content, parent) =>
                  handleCommentSubmit(selectedItem.id, content, parent)
                }
                fetchItemDetail={fetchItemDetail}
                onClose={() => setSelectedItem(null)}
                onOpenModal={handleOpenModal} // 이 prop은 이미 올바르게 전달되고 있습니다.
              />
            </DialogContent>
          </Dialog>
        )}

        <RecommendationModal
          isOpen={isRecommendationModalOpen}
          onClose={() => setIsRecommendationModalOpen(false)}
          recommendations={recommendations}
          onSearch={fetchRecommendations}
        />
      </div>
      {movieId && (
        <MovieDetailModal
          movieId={movieId}
          onClose={handleCloseModal}
          onOpen={handleOpenModal}
        />
      )}

      {personId && personType && (
        <PersonProfileModal
          personId={personId}
          personType={personType}
          onClose={handleCloseModal}
          onOpen={handleOpenModal}
        />
      )}
    </div>
  );
}
