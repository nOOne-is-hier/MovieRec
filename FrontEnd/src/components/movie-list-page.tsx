'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RangeSlider } from "@/components/ui/range-slider";
import { StarIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
import MovieDetailModal from './MovieDetailModal';
import PersonProfileModal from './PersonProfileModal';
import api from '@/lib/api'; // Axios 인스턴스
import UserProfileModal from './UserProfileModal';

interface Genre {
  id: number;
  name: string;
}

interface Movie {
  id: number;
  title: string;
  poster_path: string;
  release_date: string;
  popularity: number;
  normalized_popularity: number;
  genres: Genre[];
  overview: string;
}

const GenreSwiper: React.FC<{ genres: Genre[] }> = ({ genres }) => {
  const swiperRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);

  useEffect(() => {
    const checkArrows = () => {
      if (swiperRef.current) {
        setShowLeftArrow(swiperRef.current.scrollLeft > 0);
        setShowRightArrow(
          swiperRef.current.scrollLeft <
          swiperRef.current.scrollWidth - swiperRef.current.clientWidth
        );
      }
    };

    checkArrows();
    if (swiperRef.current) {
      swiperRef.current.addEventListener('scroll', checkArrows);
    }

    return () => {
      if (swiperRef.current) {
        swiperRef.current.removeEventListener('scroll', checkArrows);
      }
    };
  }, []);

  const scroll = (direction: 'left' | 'right') => {
    if (swiperRef.current) {
      const scrollAmount = 100;
      swiperRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
    }
  };

  return (
    <div className="relative">
      <div
        ref={swiperRef}
        className="flex overflow-x-auto whitespace-nowrap scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {genres.map((genre) => (
          <Badge
            key={genre.id}
            variant="secondary"
            className="bg-purple-600 text-white mr-1 text-[10px] py-0 px-1.5 inline-block"
          >
            {genre.name}
          </Badge>
        ))}
      </div>
      {showLeftArrow && (
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 transform -translate-y-1/2 bg-gray-800 bg-opacity-50 rounded-full p-1"
          aria-label="Scroll left"
        >
          <ChevronLeftIcon className="w-4 h-4 text-white" />
        </button>
      )}
      {showRightArrow && (
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-gray-800 bg-opacity-50 rounded-full p-1"
          aria-label="Scroll right"
        >
          <ChevronRightIcon className="w-4 h-4 text-white" />
        </button>
      )}
    </div>
  );
};

export default function MovieListPage() {
  const [allMovies, setAllMovies] = useState<Movie[]>([]);
  const [visibleMovies, setVisibleMovies] = useState<Movie[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('전체');
  const [yearRange, setYearRange] = useState([1900, 2024]);
  const [ratingRange, setRatingRange] = useState([0, 10]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const handleModalClose = () => setIsModalOpen(false);
  const [isUserProfileModalOpen, setIsUserProfileModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);


  const router = useRouter();
  const searchParams = useSearchParams();
  const movieId = searchParams.get('movieId');
  const personId = searchParams.get('personId');
  const personType = searchParams.get('personType') as 'actor' | 'director' | null;

  const observer = useRef<IntersectionObserver | null>(null);
  const lastMovieElementRef = useCallback((node: HTMLDivElement | null) => {
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        setPage(prevPage => prevPage + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, []);

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const response = await api.get('/movies/');
        setAllMovies(response.data);
      } catch (err) {
        setError('영화를 불러오는데 실패했습니다. 나중에 다시 시도해주세요.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMovies();
  }, []);

  useEffect(() => {
    const filteredMovies = allMovies.filter(movie => {
      if (!movie.release_date) return false;

      const movieYear = parseInt(movie.release_date.substring(0, 4));

      return movie.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
        (selectedGenre === '전체' || movie.genres.some(genre => genre.name === selectedGenre)) &&
        movieYear >= yearRange[0] &&
        movieYear <= yearRange[1] &&
        movie.normalized_popularity >= ratingRange[0] &&
        movie.normalized_popularity <= ratingRange[1];
    });

    setVisibleMovies(filteredMovies.slice(0, page * 20)); // 20 movies per page
  }, [allMovies, searchTerm, selectedGenre, yearRange, ratingRange, page]);

  const handleMovieClick = (movieId: number) => {
    router.push(`/?movieId=${movieId}`, { scroll: false });
  };

  const handlePersonClick = (personId: number, personType: 'actor' | 'director') => {
    router.push(`?personId=${personId}&personType=${personType}`, { scroll: false })
  }

  const handleUserClick = (userId: number) => {
    setSelectedUserId(userId.toString());
    setIsUserProfileModalOpen(true);
  }

  const handleUserProfileModalClose = () => {
    setIsUserProfileModalOpen(false);
    setSelectedUserId(null);
  };

  const handleCloseModal = () => {
    router.push('/', { scroll: false });
  };

  if (isLoading) {
    return <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">로딩 중...</div>;
  }

  if (error) {
    return <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 pt-16">
      <div className="sticky top-16 bg-gray-900/80 backdrop-blur-sm z-10 p-2 shadow-md">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-4 gap-2 items-center">
            <div className="col-span-2 grid grid-cols-3 gap-2">
              <Input
                placeholder="영화 검색..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setPage(1)
                }}
                className="bg-gray-800/60 border-gray-700 col-span-2"
              />
              <Select
                value={selectedGenre}
                onValueChange={(value) => {
                  setSelectedGenre(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-full bg-gray-800/60 border-gray-700">
                  <SelectValue placeholder="장르 선택" />
                </SelectTrigger>
                <SelectContent>
                  {['전체', '액션', '모험', '애니메이션', '코미디', '범죄', '다큐멘터리', '드라마', '가족', '판타지', '역사', '공포', '음악', '미스터리', '로맨스', 'SF', 'TV 영화', '스릴러', '전쟁', '서부'].map((genre) => (
                    <SelectItem key={genre} value={genre}>{genre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-400 mb-1">개봉연도</span>
              <RangeSlider
                min={1900}
                max={2024}
                step={1}
                value={yearRange}
                onValueChange={(value) => {
                  setYearRange(value)
                  setPage(1)
                }}
                className="w-full bg-gray-800/60"
              />
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-400">{yearRange[0]}</span>
                <span className="text-xs text-gray-400">{yearRange[1]}</span>
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-400 mb-1">평점</span>
              <RangeSlider
                min={0}
                max={10}
                step={0.1}
                value={ratingRange}
                onValueChange={(value) => {
                  setRatingRange(value)
                  setPage(1)
                }}
                className="w-full bg-gray-800/60"
              />
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-400">{ratingRange[0].toFixed(1)}</span>
                <span className="text-xs text-gray-400">{ratingRange[1].toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <main className="p-4 pb-16"> {/* Added pb-16 for footer space */}
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {visibleMovies.map((movie, index) => (
              <Card
                key={movie.id}
                className="bg-gray-800 overflow-hidden cursor-pointer"
                ref={index === visibleMovies.length - 1 ? lastMovieElementRef : null}
              >
                <div
                  className="aspect-[2/3] relative"
                  onClick={() => handleMovieClick(movie.id)}
                >
                  <img
                    src={movie.poster_path}
                    alt={movie.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black to-transparent opacity-90"></div>
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-gray-900 to-transparent p-2">
                    <h3 className="font-semibold truncate text-white text-sm">{movie.title}</h3>
                  </div>
                </div>
                <CardContent className="p-3">
                  <div className="mb-2 h-6 overflow-hidden">
                    <GenreSwiper genres={movie.genres} />
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <StarIcon className="w-4 h-4 text-yellow-400 fill-current" />
                      <span className="text-sm text-white ml-1">{movie.normalized_popularity.toFixed(1)}</span>
                    </div>
                    <div className="text-sm text-gray-400">
                      {movie.release_date ? movie.release_date.substring(0, 4) : 'N/A'}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>
      {isUserProfileModalOpen && selectedUserId && (
        <UserProfileModal
          isOpen={isUserProfileModalOpen}
          onClose={handleUserProfileModalClose}
          userId={selectedUserId}
        />
      )}
      {movieId && <MovieDetailModal movieId={movieId} onClose={handleCloseModal} />}
      {personId && personType && (
        <PersonProfileModal
          personId={personId}
          personType={personType}
          onClose={handleCloseModal}
        />
      )}
      
    </div>
  )
}