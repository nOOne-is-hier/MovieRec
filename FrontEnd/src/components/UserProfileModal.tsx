'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import { useState, useEffect, useCallback } from 'react'
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Edit, UserPlus, UserMinus, Star, ThumbsUp, ThumbsDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import api, { toggleFollow, deleteSocialData, getCurrentUserId } from '@/lib/api'
import { ProfileSettingsModal } from './ProfileSettingsModal'
import MovieDetailModal from './MovieDetailModal'
import PersonProfileModal from './PersonProfileModal'


interface UserProfileModalProps {
  isOpen: boolean
  onClose: () => void
  userId: string | number | null; // null도 허용
}

interface UserProfileData {
  id: number
  profile_image: string
  username: string
  bio: string
  favorite_genres: string[]
  is_following: boolean
  level: number
  liked_movies: MovieCard[]
  favorite_actors: ActorCard[]
  favorite_directors: DirectorCard[]
  recent_reviews: RecentReview[]
  recent_comments: RecentComment[]
  recent_posts: RecentPost[]
  followers: SimpleUserCard[]
  followers_count: number
  following: SimpleUserCard[]
  following_count: number
  mutual_followers: SimpleUserCard[]
}

interface MovieCard {
  id: number
  title: string
  poster_path: string
  release_date: string
  normalized_popularity: number
  genres: string[]
}

interface ActorCard {
  id: number
  name: string
  profile_path: string
  movies: string[]
}

interface DirectorCard {
  id: number
  name: string
  profile_path: string
  movies: string[]
}

interface RecentReview {
  id: number
  movie_title: string
  movie_id: number
  content: string
  rating: number
  created_at: string
  updated_at: string
}

interface RecentComment {
  id: number
  object_id: number
  content: string
  like_count: number
  dislike_count: number
  created_at: string
}

interface RecentPost {
  id: number
  title: string
  content: string
  created_at: string
  updated_at: string
}

interface SimpleUserCard {
  id: number
  username: string
  profile_image: string
  bio: string
}

export default function UserProfileModal({ isOpen, onClose, userId }: UserProfileModalProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  // const userId = searchParams.get('userId')

  const [userData, setUserData] = useState<UserProfileData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isProfileSettingsOpen, setIsProfileSettingsOpen] = useState(false)
  const [nestedModalStack, setNestedModalStack] = useState<number[]>([])
  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null)
  const [selectedPerson, setSelectedPerson] = useState<{ id: number, type: 'actor' | 'director' } | null>(null)

  useEffect(() => {
    const fetchUserData = async () => {
      if (!userId) return
      setIsLoading(true)
      try {
        const response = await api.get(`/accounts/users/${userId}/profile/`)
        setUserData(response.data)
      } catch (error) {
        console.error('Error fetching user data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    if (isOpen) {
      fetchUserData()
    }
  }, [userId, isOpen])

  useEffect(() => {
    const movieId = searchParams.get('movieId')
    const personId = searchParams.get('personId')
    const personType = searchParams.get('personType') as 'actor' | 'director'

    setSelectedMovieId(movieId ? Number(movieId) : null)
    setSelectedPerson(personId && personType ? { id: Number(personId), type: personType } : null)
  }, [searchParams])

  const handleToggleFollow = async () => {
    if (!userData) return

    try {
      await toggleFollow(userData.id)
      setUserData(prevData => prevData ? {...prevData, is_following: !prevData.is_following} : null)
    } catch (error) {
      console.error('Error toggling follow:', error)
    }
  }

  const handleNestedModalOpen = (newUserId: number) => {
    setNestedModalStack(prev => [...prev, newUserId])
  }

  const handleNestedModalClose = () => {
    setNestedModalStack(prev => prev.slice(0, -1))
  }

  const handleClose = () => {
    router.push('.', { scroll: false })
  }

  const handleMovieClick = (movieId: number) => {
    router.push(`?movieId=${movieId}`, { scroll: false })
  }

  const handlePersonClick = (personId: number, personType: 'actor' | 'director') => {
    router.push(`?personId=${personId}&personType=${personType}`, { scroll: false })
  }

  if (!isOpen || !userId) return null

  const handleModalClose = useCallback(() => {
    router.push('.', { scroll: false })
  }, [router])

  const handleEditProfileClick = () => {
    setIsProfileSettingsOpen(true)
  }

  const handleProfileSettingsClose = () => {
    setIsProfileSettingsOpen(false)
  }

  if (isLoading) {
    return <div>로딩 중...</div>
  }

  if (!userData) {
    return <div>사용자 데이터를 불러올 수 없습니다.</div>
  }

  const currentUserId = getCurrentUserId();
  if (!currentUserId) {
    console.error('Current User ID is not available!');
  } else {
    console.log('Current User ID:', currentUserId);
  }  
  const isOwnProfile = Number(currentUserId) === Number(userId);

  return (
    <>
    <Dialog open={isOpen} onOpenChange={onClose}>
    <DialogContent className="sm:max-w-[1000px] bg-[#1a1f2e] border-none text-white p-0">
          <DialogTitle className="sr-only">User Profile</DialogTitle> 
          <div className="p-6">
            <div className="flex flex-col items-center space-y-4 mb-6">
              <Avatar className="w-24 h-24">
                <AvatarImage src={userData.profile_image} alt={userData.username} />
                <AvatarFallback className="bg-purple-600">{userData.username[0]}</AvatarFallback>
              </Avatar>
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-1">{userData.username}</h2>
                <p className="text-gray-400 mb-3 text-sm">{userData.bio}</p>
                <div className="flex gap-4 justify-center">
                  {isOwnProfile ? (
                    <Button 
                      className="bg-purple-600 hover:bg-purple-700"
                      onClick={handleEditProfileClick}
                    >
                      <Edit className="mr-2 h-4 w-4" /> Edit Profile
                    </Button>
                  ) : (
                    <Button
                      variant={userData.is_following ? "outline" : "default"}
                      className={userData.is_following ? "border-purple-600 text-purple-600 hover:bg-purple-600/10" : "bg-purple-600 hover:bg-purple-700"}
                      onClick={handleToggleFollow}
                    >
                      {userData.is_following ? (
                        <>
                          <UserMinus className="mr-2 h-4 w-4" /> Unfollow
                        </>
                      ) : (
                        <>
                          <UserPlus className="mr-2 h-4 w-4" /> Follow
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold mb-2">Favorite Genres</h3>
              <div className="flex flex-wrap gap-1">
                {userData.favorite_genres.length > 0 ? (
                  userData.favorite_genres.map((genre: string) => (
                    <Badge key={genre} className="bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 text-xs">{genre}</Badge>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm">No favorite genres yet</p>
                )}
              </div>
            </div>

            <Tabs defaultValue="movies" className="w-full">
              <TabsList className="w-full bg-[#252b3d] p-1 rounded-lg">
                <TabsTrigger 
                  value="movies" 
                  className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
                >
                  Movies
                </TabsTrigger>
                <TabsTrigger 
                  value="people"
                  className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
                >
                  People
                </TabsTrigger>
                <TabsTrigger 
                  value="activity"
                  className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
                >
                  Activity
                </TabsTrigger>
                <TabsTrigger 
                  value="social"
                  className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
                >
                  Social
                </TabsTrigger>
              </TabsList>

              <TabsContent value="movies">
                <MovieTab likedMovies={userData?.liked_movies || []} onMovieClick={handleMovieClick} />
              </TabsContent>

              <TabsContent value="people">
                <PeopleTab 
                  favoriteActors={userData?.favorite_actors || []} 
                  favoriteDirectors={userData?.favorite_directors || []} 
                  onPersonClick={handlePersonClick}
                />
              </TabsContent>

              <TabsContent value="activity">
                <ActivityTab 
                  reviews={userData?.recent_reviews || []}
                  comments={userData?.recent_comments || []}
                  posts={userData?.recent_posts || []}
                />
              </TabsContent>

              <TabsContent value="social">
                <SocialTab 
                  followers={userData?.followers || []}
                  following={userData?.following || []}
                  mutualFollowers={userData?.mutual_followers || []}
                  onUserClick={handleNestedModalOpen}
                />
              </TabsContent>
            </Tabs>
          </div>
        </DialogContent>
      </Dialog>
      {nestedModalStack.map((nestedUserId, index) => (
        <UserProfileModal
          key={`${nestedUserId}-${index}`}
          isOpen={true}
          onClose={handleNestedModalClose}
          userId={nestedUserId}
        />
      ))}
      {isProfileSettingsOpen && (
        <ProfileSettingsModal
          isOpen={isProfileSettingsOpen}
          onClose={() => setIsProfileSettingsOpen(false)}
          userId={Number(userId)}
        />
      )}
    </>
  )
}

function MovieTab({ likedMovies, onMovieClick }: { likedMovies: MovieCard[], onMovieClick: (movieId: number) => void }) {
  const [currentPage, setCurrentPage] = useState(0);
  const moviesPerPage = 6;
  const totalPages = Math.ceil(likedMovies.length / moviesPerPage);

  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 0));
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages - 1));

  const paginatedMovies = likedMovies.slice(currentPage * moviesPerPage, (currentPage + 1) * moviesPerPage);

  return (
    <div>
      <ScrollArea className="h-[500px] pr-4">
        <div className="grid grid-cols-3 gap-4">
          {paginatedMovies.map((movie) => (
            <Card 
              key={movie.id} 
              className="bg-[#252b3d] border-none overflow-hidden cursor-pointer transition-transform hover:scale-105"
              onClick={() => onMovieClick(movie.id)}
            >
              <CardContent className="p-0">
                <img 
                  src={movie.poster_path} 
                  alt={movie.title} 
                  className="w-full h-60 object-cover"
                />
                <div className="p-3">
                  <h3 className="font-medium text-xs mb-1 line-clamp-1">{movie.title}</h3>
                  <p className="text-[10px] text-gray-400">{movie.release_date}</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {movie.genres.slice(0, 2).map((genre: string) => (
                      <span key={genre} className="text-[8px] bg-purple-600/20 text-purple-300 px-1 py-0.5 rounded">
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
      <div className="flex justify-between mt-4">
        <Button onClick={handlePrevPage} disabled={currentPage === 0} size="sm">
          <ChevronLeft className="w-4 h-4 mr-1" /> Previous
        </Button>
        <Button onClick={handleNextPage} disabled={currentPage === totalPages - 1} size="sm">
          Next <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}

function PeopleTab({ 
  favoriteActors, 
  favoriteDirectors, 
  onPersonClick 
}: { 
  favoriteActors: ActorCard[], 
  favoriteDirectors: DirectorCard[],
  onPersonClick: (personId: number, personType: 'actor' | 'director') => void
}) {
  const [currentActorPage, setCurrentActorPage] = useState(0);
  const [currentDirectorPage, setCurrentDirectorPage] = useState(0);
  const peoplePerPage = 6;

  const totalActorPages = Math.ceil(favoriteActors.length / peoplePerPage);
  const totalDirectorPages = Math.ceil(favoriteDirectors.length / peoplePerPage);

  const handlePrevPage = (type: 'actor' | 'director') => {
    if (type === 'actor') {
      setCurrentActorPage(prev => Math.max(prev - 1, 0));
    } else {
      setCurrentDirectorPage(prev => Math.max(prev - 1, 0));
    }
  };

  const handleNextPage = (type: 'actor' | 'director') => {
    if (type === 'actor') {
      setCurrentActorPage(prev => Math.min(prev + 1, totalActorPages - 1));
    } else {
      setCurrentDirectorPage(prev => Math.min(prev + 1, totalDirectorPages - 1));
    }
  };

  const paginatedActors = favoriteActors.slice(currentActorPage * peoplePerPage, (currentActorPage + 1) * peoplePerPage);
  const paginatedDirectors = favoriteDirectors.slice(currentDirectorPage * peoplePerPage, (currentDirectorPage + 1) * peoplePerPage);

  if (!favoriteActors.length && !favoriteDirectors.length) {
    return (
      <ScrollArea className="h-[500px]">
        <p className="text-center text-gray-400">No favorite actors or directors yet.</p>
      </ScrollArea>
    );
  }

  return (
    <Tabs defaultValue="actors" className="w-full">
      <TabsList className="w-full bg-[#252b3d] p-1 rounded-lg mb-3">
        <TabsTrigger 
          value="actors" 
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Actors
        </TabsTrigger>
        <TabsTrigger 
          value="directors"
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Directors
        </TabsTrigger>
      </TabsList>
      <TabsContent value="actors">
        <ScrollArea className="h-[500px] pr-4">
          {favoriteActors.length > 0 ? (
            <div className="grid grid-cols-3 gap-4">
              {paginatedActors.map((actor) => (
                <Card 
                  key={actor.id} 
                  className="bg-[#252b3d] border-none overflow-hidden cursor-pointer transition-transform hover:scale-105"
                  onClick={() => onPersonClick(actor.id, 'actor')}
                >
                  <CardContent className="p-0">
                    <img src={actor.profile_path} alt={actor.name} className="w-full h-60 object-cover" />
                    <div className="p-3">
                      <h3 className="font-medium text-xs mb-1">{actor.name}</h3>
                      <p className="text-[10px] text-gray-400 line-clamp-1">Known for: {actor.movies.slice(0, 2).join(', ')}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-400">No favorite actors yet.</p>
          )}
        </ScrollArea>
        <div className="flex justify-between mt-4">
          <Button onClick={() => handlePrevPage('actor')} disabled={currentActorPage === 0} size="sm">
            <ChevronLeft className="w-4 h-4 mr-1" /> Previous
          </Button>
          <Button onClick={() => handleNextPage('actor')} disabled={currentActorPage === totalActorPages - 1} size="sm">
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </TabsContent>
      <TabsContent value="directors">
        <ScrollArea className="h-[500px] pr-4">
          {favoriteDirectors.length > 0 ? (
            <div className="grid grid-cols-3 gap-4">
              {paginatedDirectors.map((director) => (
                <Card 
                  key={director.id} 
                  className="bg-[#252b3d] border-none overflow-hidden cursor-pointer transition-transform hover:scale-105"
                  onClick={() => onPersonClick(director.id, 'director')}
                >
                  <CardContent className="p-0">
                    <img src={director.profile_path} alt={director.name} className="w-full h-60 object-cover" />
                    <div className="p-3">
                      <h3 className="font-medium text-xs mb-1">{director.name}</h3>
                      <p className="text-[10px] text-gray-400 line-clamp-1">Directed: {director.movies.slice(0, 2).join(', ')}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-400">No favorite directors yet.</p>
          )}
        </ScrollArea>
        <div className="flex justify-between mt-4">
          <Button onClick={() => handlePrevPage('director')} disabled={currentDirectorPage === 0} size="sm">
            <ChevronLeft className="w-4 h-4 mr-1" /> Previous
          </Button>
          <Button onClick={() => handleNextPage('director')} disabled={currentDirectorPage === totalDirectorPages - 1} size="sm">
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </TabsContent>
    </Tabs>
  )
}

function ActivityTab({ reviews, comments, posts }: { reviews: RecentReview[], comments: RecentComment[], posts: RecentPost[] }) {
  return (
    <Tabs defaultValue="reviews" className="w-full">
      <TabsList className="w-full bg-[#252b3d] p-1 rounded-lg mb-3">
        <TabsTrigger 
          value="reviews" 
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Reviews
        </TabsTrigger>
        <TabsTrigger 
          value="comments"
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Comments
        </TabsTrigger>
        <TabsTrigger 
          value="posts"
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Posts
        </TabsTrigger>
      </TabsList>
      <TabsContent value="reviews">
        <ScrollArea className="h-[500px] pr-4">
          {reviews && reviews.length > 0 ? (
            reviews.map((review) => (
              <Card key={review.id} className="mb-3 bg-[#252b3d] border-none">
                <CardHeader className="p-3">
                  <CardTitle className="text-sm">{review.movie_title}</CardTitle>
                </CardHeader>
                <CardContent className="p-3 pt-0">
                  <p className="text-xs text-gray-300 mb-2 line-clamp-2">{review.content}</p>
                  <div className="flex items-center text-xs text-gray-400">
                    <Star className="w-3 h-3 mr-1 text-yellow-500" />
                    <span>{review.rating}/5</span>
                    <span className="ml-3">{new Date(review.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="text-center text-gray-400">No reviews yet.</p>
          )}
        </ScrollArea>
      </TabsContent>

      <TabsContent value="comments">
        <ScrollArea className="h-[500px] pr-4">
          {comments && comments.length > 0 ? (
            comments.map((comment) => (
              <Card key={comment.id} className="mb-3 bg-[#252b3d] border-none">
                <CardContent className="p-3">
                  <p className="text-xs text-gray-300 mb-2 line-clamp-2">{comment.content}</p>
                  <div className="flex items-center text-xs text-gray-400">
                    <ThumbsUp className="w-3 h-3 mr-1" />
                    <span>{comment.like_count}</span>
                    <ThumbsDown className="w-3 h-3 ml-3 mr-1" />
                    <span>{comment.dislike_count}</span>
                    <span className="ml-3">{new Date(comment.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="text-center text-gray-400">No comments yet.</p>
          )}
        </ScrollArea>
      </TabsContent>

      <TabsContent value="posts">
        <ScrollArea className="h-[500px] pr-4">
          {posts && posts.length > 0 ? (
            posts.map((post) => (
              <Card key={post.id} className="mb-3 bg-[#252b3d] border-none">
                <CardHeader className="p-3">
                  <CardTitle className="text-sm">{post.title}</CardTitle>
                </CardHeader>
                <CardContent className="p-3 pt-0">
                  <p className="text-xs text-gray-300 mb-2 line-clamp-2">{post.content}</p>
                  <p className="text-xs text-gray-400">{new Date(post.created_at).toLocaleDateString()}</p>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="text-center text-gray-400">No posts yet.</p>
          )}
        </ScrollArea>
      </TabsContent>
    </Tabs>
  )
}

function SocialTab({ 
  followers, 
  following, 
  mutualFollowers, 
  onUserClick 
}: { 
  followers: SimpleUserCard[], 
  following: SimpleUserCard[], 
  mutualFollowers: SimpleUserCard[],
  onUserClick: (userId: number) => void
}) {
  const [activeFollowers, setActiveFollowers] = useState(followers)
  const [activeFollowing, setActiveFollowing] = useState(following)
  const [activeMutual, setActiveMutual] = useState(mutualFollowers)

  const handleDelete = async (targetUserId: number, type: 'followers' | 'following' | 'mutual') => {
    const currentUserId = getCurrentUserId();
    if (!currentUserId) {
      console.error('Current user ID not found');
      return;
    }
  
    try {
      // API 요청에 type(action)을 포함
      await deleteSocialData(currentUserId, { 
        target_user_id: targetUserId, 
        action: type === 'mutual' ? 'follower' : type === 'following' ? 'following' : 'follower'
    });
    
  
      // 상태 업데이트: 동적 처리로 중복 제거
      const stateMapping = {
        followers: activeFollowers,
        following: activeFollowing,
        mutual: activeMutual,
      };
  
      const setStateMapping = {
        followers: setActiveFollowers,
        following: setActiveFollowing,
        mutual: setActiveMutual,
      };
  
      const updatedState = stateMapping[type].filter(user => user.id !== targetUserId);
      setStateMapping[type](updatedState);
    } catch (error) {
      console.error('Error deleting social connection:', error);
      alert('소셜 연결을 삭제하는 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };
  

  const UserCard = ({ user, type }: { user: SimpleUserCard; type: 'followers' | 'following' | 'mutual' }) => (
    <Card className="mb-3 bg-[#252b3d] border-none">
      <CardContent className="p-3 flex items-center justify-between">
        <div 
          className="flex items-center space-x-3 cursor-pointer" 
          onClick={() => onUserClick(user.id)}
        >
          <Avatar className="w-8 h-8">
            <AvatarImage src={user.profile_image} alt={user.username} />
            <AvatarFallback className="bg-purple-600">{user.username[0]}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium text-sm">{user.username}</p>
            <p className="text-xs text-gray-400 line-clamp-1">{user.bio}</p>
          </div>
        </div>
        <Button 
          variant="destructive" 
          size="sm" 
          onClick={(e) => {
            e.stopPropagation();
            handleDelete(user.id, type);
          }}
          className="bg-red-600 hover:bg-red-700 text-xs h-7"
        >
          Delete
        </Button>
      </CardContent>
    </Card>
  )

  return (
    <Tabs defaultValue="followers" className="w-full">
      <TabsList className="w-full bg-[#252b3d] p-1 rounded-lg mb-3">
        <TabsTrigger 
          value="followers" 
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Followers
        </TabsTrigger>
        <TabsTrigger 
          value="following"
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Following
        </TabsTrigger>
        <TabsTrigger 
          value="mutual"
          className="flex-1 data-[state=active]:bg-purple-600 data-[state=active]:text-white text-sm"
        >
          Mutual
        </TabsTrigger>
      </TabsList>
      <TabsContent value="followers">
        <ScrollArea className="h-[500px] pr-4">
          {activeFollowers.length > 0 ? (
            activeFollowers.map((follower) => (
              <UserCard key={follower.id} user={follower} type="followers" />
            ))
          ) : (
            <p className="text-center text-gray-400">No followers yet.</p>
          )}
        </ScrollArea>
      </TabsContent>
      <TabsContent value="following">
        <ScrollArea className="h-[500px] pr-4">
          {activeFollowing.length > 0 ? (
            activeFollowing.map((followedUser) => (
              <UserCard key={followedUser.id} user={followedUser} type="following" />
            ))
          ) : (
            <p className="text-center text-gray-400">Not following anyone yet.</p>
          )}
        </ScrollArea>
      </TabsContent>
      <TabsContent value="mutual">
        <ScrollArea className="h-[500px] pr-4">
          {activeMutual.length > 0 ? (
            activeMutual.map((mutualUser) => (
              <UserCard key={mutualUser.id} user={mutualUser} type="mutual" />
            ))
          ) : (
            <p className="text-center text-gray-400">No mutual followers yet.</p>
          )}
        </ScrollArea>
      </TabsContent>
    </Tabs>
  )
}