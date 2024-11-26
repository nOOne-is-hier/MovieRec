import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MovieCard } from './MovieCard';
import MovieDetailModal from './MovieDetailModal';

interface Movie {
  id: number;
  title: string;
  poster_path: string;
  release_date: string;
  genres: { id: number; name: string }[];
  normalized_popularity: number;
}

interface RecommendationModalProps {
  isOpen: boolean;
  onClose: () => void;
  recommendations: {
    personalized_recommendations: Movie[];
    keyword_based_recommendations: Movie[];
  };
  onSearch: (keyword: string) => void;
}

export const RecommendationModal: React.FC<RecommendationModalProps> = ({
  isOpen,
  onClose,
  recommendations,
  onSearch,
}) => {
  const [keyword, setKeyword] = useState('');
  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null);

  const handleSearch = () => {
    onSearch(keyword);
  };

  const handleMovieClick = (id: number) => {
    setSelectedMovieId(id);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[95vw] w-full md:max-w-[90vw] lg:max-w-[85vw] xl:max-w-[80vw] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg sm:text-xl font-bold mb-2">추천 결과</DialogTitle>
        </DialogHeader>
        <div className="mb-4 flex space-x-2">
          <Input
            type="text"
            placeholder="키워드 입력"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="flex-grow text-sm"
          />
          <Button onClick={handleSearch} size="sm">검색</Button>
        </div>
        <div className="space-y-6">
          <section>
            <h3 className="text-base sm:text-lg font-semibold mb-3">개인화 추천</h3>
            {recommendations.personalized_recommendations.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3">
                {recommendations.personalized_recommendations.map((movie) => (
                  <MovieCard
                    key={movie.id}
                    id={movie.id}
                    title={movie.title}
                    posterPath={movie.poster_path}
                    releaseDate={movie.release_date}
                    genres={movie.genres}
                    normalizedPopularity={movie.normalized_popularity}
                    onClick={handleMovieClick}
                  />
                ))}
              </div>
            ) : (
              <p className="text-sm">개인화 추천 결과가 없습니다.</p>
            )}
          </section>
          <section>
            <h3 className="text-base sm:text-lg font-semibold mb-3">키워드 기반 추천</h3>
            {recommendations.keyword_based_recommendations.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3">
                {recommendations.keyword_based_recommendations.map((movie) => (
                  <MovieCard
                    key={movie.id}
                    id={movie.id}
                    title={movie.title}
                    posterPath={movie.poster_path}
                    releaseDate={movie.release_date}
                    genres={movie.genres}
                    normalizedPopularity={movie.normalized_popularity}
                    onClick={handleMovieClick}
                  />
                ))}
              </div>
            ) : (
              <p className="text-sm">키워드 기반 추천 결과가 없습니다.</p>
            )}
          </section>
        </div>
        {selectedMovieId && <MovieDetailModal movieId={selectedMovieId} />}
      </DialogContent>
    </Dialog>
  );
};
