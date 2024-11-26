import React from 'react';
import Image from 'next/image';
import { Star } from 'lucide-react';

interface MovieCardProps {
  id: number;
  title: string;
  posterPath: string;
  releaseDate: string;
  genres: { id: number; name: string }[];
  normalizedPopularity: number;
  onClick: (id: number) => void;
}

export const MovieCard: React.FC<MovieCardProps> = ({
  id,
  title,
  posterPath,
  releaseDate,
  genres,
  normalizedPopularity,
  onClick,
}) => {
  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer transition-transform hover:scale-105"
      onClick={() => onClick(id)}
    >
      <div className="relative aspect-[2/3] w-full">
        <Image
          src={posterPath}
          alt={title}
          fill
          className="object-cover"
          unoptimized
        />
        <div className="absolute top-0 right-0 bg-black bg-opacity-70 text-white p-1 m-1 rounded-md flex items-center">
          <Star className="w-3 h-3 mr-1 text-yellow-400" />
          <span className="text-xs font-bold">{normalizedPopularity.toFixed(1)}</span>
        </div>
      </div>
      <div className="p-2 sm:p-3">
        <h4 className="text-sm sm:text-base font-bold mb-1 truncate dark:text-white">{title}</h4>
        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mb-0.5">
          {releaseDate}
        </p>
        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate">
          {genres.map((genre) => genre.name).join(', ')}
        </p>
      </div>
    </div>
  );
};
