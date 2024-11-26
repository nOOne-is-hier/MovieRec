'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { UserCircle, Video, Users, Star } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Pagination } from '@/components/paginations';
import MovieDetailModal from '@/components/MovieDetailModal';
import PersonProfileModal from '@/components/PersonProfileModal';
import PopularityToggle from "@/components/ui/PopularityToggle";
import api from '@/lib/api'; // Axios 인스턴스
import UserProfileModal from '@/components/UserProfileModal';


interface Actor {
  id: number;
  name: string;
  gender: string;
  profile_path: string;
  birthdate: string;
  biography: string;
  birthplace: string;
  favorited_count: number;
}

interface Director {
  id: number;
  name: string;
  gender: string;
  profile_path: string;
  birthdate: string;
  biography: string;
  birthplace: string;
  favorited_count: number;
}

interface User {
  id: number;
  username: string;
  email: string;
  profile_image: string;
  bio: string;
  followers_count: number;
}

type SearchItem = Actor | Director | User;

interface SearchResults {
  actors: Actor[];
  directors: Director[];
  users: User[];
}

const ITEMS_PER_PAGE = 24;
const MAX_VISIBLE_PAGES = 5;

export default function SearchPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [queryParams, setQueryParams] = useState<URLSearchParams>(new URLSearchParams());
  const [activeTab, setActiveTab] = useState<'actors' | 'directors' | 'users'>('actors');
  const [sortBy, setSortBy] = useState('popularity-desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [allData, setAllData] = useState<SearchResults>({
    actors: [],
    directors: [],
    users: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  const movieId = queryParams.get('movieId');
  const personId = queryParams.get('personId');
  const personType = queryParams.get('personType') as 'actor' | 'director' | null;
  const userId = queryParams.get('userId');
  const query = queryParams.get('q') || '';

  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString());
    setQueryParams(params);
    const page = parseInt(params.get('page') || '1', 10);
    setCurrentPage(page);
    const type = params.get('type') as 'actors' | 'directors' | 'users' || 'actors';
    setActiveTab(type);
  }, [searchParams]);

  useEffect(() => {
    const fetchAllData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.get('/movies/search/');
        setAllData(response.data);
      } catch (err) {
        setError('데이터를 불러오는 데 실패했습니다.');
        console.error('Data fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllData();
  }, []);

  const filteredAndSortedResults = useMemo(() => {
    let results = [...allData[activeTab]] as SearchItem[];

    if (query) {
      results = results.filter(item =>
        'name' in item
          ? item.name.toLowerCase().includes(query.toLowerCase())
          : item.username.toLowerCase().includes(query.toLowerCase())
      );
    }

    if (sortBy) {
      const [field, direction] = sortBy.split('-');
      results.sort((a, b) => {
        const valueA = 'followers_count' in a ? a.followers_count : a.favorited_count;
        const valueB = 'followers_count' in b ? b.followers_count : b.favorited_count;

        return direction === 'asc' ? valueA - valueB : valueB - valueA;
      });
    }

    return results;
  }, [allData, activeTab, query, sortBy]);

  const totalPages = Math.ceil(filteredAndSortedResults.length / ITEMS_PER_PAGE);
  const paginatedResults = filteredAndSortedResults.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const updatePage = (newPage: number) => {
    const currentParams = new URLSearchParams(queryParams.toString());
    currentParams.set('page', newPage.toString());
    router.push(`/search?${currentParams.toString()}`);
  };

  const handlePersonClick = (id: number, type: 'actor' | 'director') => {
    const currentParams = new URLSearchParams(queryParams.toString());
    currentParams.set('personId', id.toString());
    currentParams.set('personType', type);
    router.push(`/search?${currentParams.toString()}`, { scroll: false });
  };

  const handleUserClick = (id: number) => {
    const currentParams = new URLSearchParams(queryParams.toString());
    currentParams.set('userId', id.toString());
    router.push(`/search?${currentParams.toString()}`, { scroll: false });
    setIsProfileModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 pt-16 flex flex-col overflow-hidden">
      <div className="sticky top-0 bg-gray-900 z-10 p-4 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 flex justify-between items-center gap-4"> {/* gap 추가 */}
          <Tabs
            value={activeTab}
            onValueChange={(value: string) => {
              setActiveTab(value as 'actors' | 'directors' | 'users');
              setCurrentPage(1);
              const currentParams = new URLSearchParams(queryParams.toString());
              currentParams.set('type', value);
              currentParams.set('page', '1');
              router.push(`/search?${currentParams.toString()}`);
            }}
            className="w-full"
          >
            <TabsList className="bg-gray-800 w-full">
              <TabsTrigger value="actors" className="flex-1 data-[state=active]:bg-purple-600">
                <UserCircle className="w-4 h-4 mr-2" />
                배우
              </TabsTrigger>
              <TabsTrigger value="directors" className="flex-1 data-[state=active]:bg-purple-600">
                <Video className="w-4 h-4 mr-2" />
                감독
              </TabsTrigger>
              <TabsTrigger value="users" className="flex-1 data-[state=active]:bg-purple-600">
                <Users className="w-4 h-4 mr-2" />
                사용자
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <PopularityToggle
            onToggle={(isAscending: boolean) => {
              const field = activeTab === 'users' ? 'followers_count' : 'favorited_count';
              const direction = isAscending ? 'asc' : 'desc';
              setSortBy(`${field}-${direction}`);
            }}
            className="w-auto px-4 py-2"
          />
        </div>
      </div>


      <main className="flex-1 bg-gray-900 pt-8 pb-16"> {/* pb-16 추가 */}
        <div className="max-w-7xl mx-auto px-4">
          {isLoading && <p className="text-center">데이터를 불러오는 중...</p>}
          {error && <p className="text-center text-red-500">{error}</p>}

          {!isLoading && !error && (
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">
              {paginatedResults.map((item: SearchItem) => (
                <Card
                  key={item.id}
                  className="bg-gray-800/50 border-gray-700 hover:bg-gray-700/50 transition-colors cursor-pointer flex flex-col max-w-[140px] w-full"
                  onClick={() => {
                    if ('username' in item) {
                      handleUserClick(item.id);
                    } else {
                      handlePersonClick(item.id, activeTab === 'actors' ? 'actor' : 'director');
                    }
                  }}
                >
                  <CardContent className="p-2 flex flex-col h-full">
                    <div className="aspect-[3/4] h-[180px] relative mb-1">
                      <img
                        src={'profile_image' in item ? item.profile_image : item.profile_path}
                        alt={'username' in item ? item.username : item.name}
                        className="w-full h-full object-cover rounded"
                      />
                    </div>
                    <h3 className="font-semibold text-xs truncate text-purple-400">
                      {'username' in item ? item.username : item.name}
                    </h3>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-700">
                      <div className="flex items-center gap-1.5">
                        <Star className="w-3.5 h-3.5 text-yellow-500/80 fill-current" />
                        <span className="text-xs font-medium text-yellow-500/80">
                          {activeTab === 'users'
                            ? `${(item as User).followers_count}`
                            : `${(item as Actor | Director).favorited_count}`
                          }
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {activeTab === 'users' ? 'followers' : 'favorites'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={updatePage}
        />
      </main>
      {movieId && <MovieDetailModal movieId={movieId} />}
      {personId && personType && (
        <PersonProfileModal
          personId={personId}
          personType={personType}
        />
      )}
      {isProfileModalOpen && userId && (
        <UserProfileModal
          isOpen={isProfileModalOpen}
          userId={Number(userId)}
          onClose={() => setIsProfileModalOpen(false)}
        />
      )}
    </div>
  );
}
