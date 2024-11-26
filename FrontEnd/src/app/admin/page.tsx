'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Film, Users, MessageSquare, TrendingUp, Search, Edit, Trash2, BarChart2, RefreshCw  } from 'lucide-react'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'

const BACKEND_URL = 'http://localhost:8000/accounts';

const API_URLS = {
  dashboard: `${BACKEND_URL}/admin/dashboard/`,
  movies: `${BACKEND_URL}/admin/movies/`,
  users: `${BACKEND_URL}/admin/users/`,
  reviews: `${BACKEND_URL}/admin/reviews/`,
  deleteMovie: `${BACKEND_URL}/admin/movies/delete/`,
  deleteUser: `${BACKEND_URL}/admin/users/delete/`,
  deleteReview: `${BACKEND_URL}/admin/reviews/delete/`,
  restoreUser: `${BACKEND_URL}/admin/users/restore/`,
};

interface DashboardData {
  user_growth: { month: string; user_count: number }[];
  movies_by_genre: { genre: string; movie_count: number }[];
}

interface Movie {
  id: number;
  title: string;
  release_date: string;
  poster_path: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  deleted_at: string | null;
}

interface Review {
  id: number;
  movie_title: string;
  user_username: string;
  rating: number;
  content: string;
  created_at: string;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [movies, setMovies] = useState<Movie[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [reviews, setReviews] = useState<Review[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  useEffect(() => {
    if (activeTab === 'movies') fetchMovies()
    if (activeTab === 'users') fetchUsers()
    if (activeTab === 'reviews') fetchReviews()
  }, [activeTab, searchQuery, currentPage])

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(API_URLS.dashboard)
      const data = await response.json()
      setDashboardData(data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }

  const fetchMovies = async () => {
    try {
      const response = await fetch(`${API_URLS.movies}?title=${searchQuery}&page=${currentPage}`)
      const data = await response.json()
      setMovies(data.results)
      setTotalPages(Math.ceil(data.count / 10))
    } catch (error) {
      console.error('Failed to load movies:', error)
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_URLS.users}?username=${searchQuery}&page=${currentPage}`)
      const data = await response.json()
      setUsers(data.results)
      setTotalPages(Math.ceil(data.count / 10))
    } catch (error) {
      console.error('Failed to load users:', error)
    }
  }

  const fetchReviews = async () => {
    try {
      const response = await fetch(`${API_URLS.reviews}?movie_title=${searchQuery}&page=${currentPage}`)
      const data = await response.json()
      setReviews(data.results)
      setTotalPages(Math.ceil(data.count / 10))
    } catch (error) {
      console.error('Failed to load reviews:', error)
    }
  }

  const handleDelete = async (type: 'movie' | 'user' | 'review', id: number) => {
    const url =
      type === 'movie'
        ? API_URLS.deleteMovie
        : type === 'user'
        ? API_URLS.deleteUser
        : API_URLS.deleteReview;

    try {
      const response = await fetch(`${url}?id=${id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Failed to delete');

      alert(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully.`);
      if (type === 'movie') fetchMovies();
      if (type === 'user') fetchUsers();
      if (type === 'review') fetchReviews();
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete item.');
    }
  };

  const handleRestore = async (userId: number) => {
    try {
      const response = await fetch(`${API_URLS.restoreUser}?id=${userId}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to restore user');

      alert('User restored successfully.');
      fetchUsers();
    } catch (error) {
      console.error('Restore error:', error);
      alert('Failed to restore user.');
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-gray-100">
      <Navbar />
      <div className="container mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">Admin Dashboard</h1>
        <Tabs value={activeTab} onValueChange={(tab) => { setActiveTab(tab); setCurrentPage(1); }} className="space-y-6">
        <TabsList className="flex justify-center mb-8 bg-gray-800 p-1 rounded-lg">
            <TabsTrigger value="dashboard" className="flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 ease-in-out">
              <TrendingUp className="h-5 w-5" /> Dashboard
            </TabsTrigger>
            <TabsTrigger value="movies" className="flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 ease-in-out">
              <Film className="h-5 w-5" /> Movies
            </TabsTrigger>
            <TabsTrigger value="users" className="flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 ease-in-out">
              <Users className="h-5 w-5" /> Users
            </TabsTrigger>
            <TabsTrigger value="reviews" className="flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 ease-in-out">
              <MessageSquare className="h-5 w-5" /> Reviews
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            {dashboardData && (
              <div className="space-y-8">
                <Card className="bg-gray-800 border-gray-700 shadow-lg">
                  <CardHeader className="border-b border-gray-700 pb-4">
                    <CardTitle className="text-xl font-semibold flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-purple-400" />
                      User Growth
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ResponsiveContainer width="100%" height={350}>
                      <BarChart data={dashboardData.user_growth} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="month" stroke="#9CA3AF" angle={-45} textAnchor="end" height={60} />
                        <YAxis stroke="#9CA3AF" />
                        <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
                        <Bar dataKey="user_count" fill="#8B5CF6" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card className="bg-gray-800 border-gray-700 shadow-lg">
                  <CardHeader className="border-b border-gray-700 pb-4">
                    <CardTitle className="text-xl font-semibold flex items-center gap-2">
                      <BarChart2 className="h-5 w-5 text-pink-400" />
                      Movies by Genre
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={dashboardData.movies_by_genre} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="genre" stroke="#9CA3AF" angle={-45} textAnchor="end" height={60} />
                        <YAxis stroke="#9CA3AF" />
                        <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
                        <Bar dataKey="movie_count" fill="#EC4899" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="movies">
            <Card className="bg-gray-800 border-gray-700 shadow-lg">
              <CardHeader className="border-b border-gray-700 pb-4">
                <CardTitle className="text-xl font-semibold">Movies</CardTitle>
                <div className="mt-4">
                  <Label htmlFor="movie-search">Search Movies</Label>
                  <div className="relative mt-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      id="movie-search"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Enter movie title..."
                      className="bg-gray-700 text-white pl-10 border-gray-600 focus:border-purple-400 focus:ring-purple-400"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-gray-200">Title</TableHead>
                      <TableHead className="text-gray-200">Release Date</TableHead>
                      <TableHead className="text-gray-200">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {movies.map((movie) => (
                      <TableRow key={movie.id} className="border-b border-gray-700">
                        <TableCell className="text-gray-50 font-medium">{movie.title}</TableCell>
                        <TableCell className="text-gray-50">{movie.release_date}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" className="text-purple-400 hover:text-purple-300"><Edit className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="text-pink-400 hover:text-pink-300" onClick={() => handleDelete('movie', movie.id)}><Trash2 className="h-4 w-4" /></Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 flex justify-between items-center">
                  <Button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className="bg-purple-500 hover:bg-purple-600">Previous</Button>
                  <span>{currentPage} / {totalPages}</span>
                  <Button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} className="bg-purple-500 hover:bg-purple-600">Next</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <Card className="bg-gray-800 border-gray-700 shadow-lg">
              <CardHeader className="border-b border-gray-700 pb-4">
                <CardTitle className="text-xl font-semibold">Users</CardTitle>
                <div className="mt-4">
                  <Label htmlFor="user-search">Search Users</Label>
                  <div className="relative mt-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      id="user-search"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Enter username..."
                      className="bg-gray-700 text-white pl-10 border-gray-600 focus:border-purple-400 focus:ring-purple-400"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-gray-200">Username</TableHead>
                      <TableHead className="text-gray-200">Email</TableHead>
                      <TableHead className="text-gray-200">Join Date</TableHead>
                      <TableHead className="text-gray-200">Status</TableHead>
                      <TableHead className="text-gray-200">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow 
                        key={user.id} 
                        className={`border-b border-gray-700 ${user.deleted_at ? 'opacity-50' : ''}`}
                      >
                        <TableCell className="text-gray-50 font-medium">{user.username}</TableCell>
                        <TableCell className="text-gray-50">{user.email}</TableCell>
                        <TableCell className="text-gray-50">{user.created_at}</TableCell>
                        <TableCell className="text-gray-50">
                          {user.deleted_at ? 'Deleted' : 'Active'}
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" className="text-purple-400 hover:text-purple-300"><Edit className="h-4 w-4" /></Button>
                          {user.deleted_at ? (
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="text-green-400 hover:text-green-300"
                              onClick={() => handleRestore(user.id)}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="text-pink-400 hover:text-pink-300" 
                              onClick={() => handleDelete('user', user.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 flex justify-between items-center">
                  <Button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className="bg-purple-500 hover:bg-purple-600">Previous</Button>
                  <span>{currentPage} / {totalPages}</span>
                  <Button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} className="bg-purple-500 hover:bg-purple-600">Next</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reviews">
            <Card className="bg-gray-800 border-gray-700 shadow-lg">
              <CardHeader className="border-b border-gray-700 pb-4">
                <CardTitle className="text-xl font-semibold">Reviews</CardTitle>
                <div className="mt-4">
                  <Label htmlFor="review-search">Search Reviews</Label>
                  <div className="relative mt-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      id="review-search"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Enter movie title..."
                      className="bg-gray-700 text-white pl-10 border-gray-600 focus:border-purple-400 focus:ring-purple-400"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-gray-200">Movie</TableHead>
                      <TableHead className="text-gray-200">User</TableHead>
                      <TableHead className="text-gray-200">Rating</TableHead>
                      <TableHead className="text-gray-200">Content</TableHead>
                      <TableHead className="text-gray-200">Date</TableHead>
                      <TableHead className="text-gray-200">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reviews.map((review) => (
                      <TableRow key={review.id} className="border-b border-gray-700">
                        <TableCell className="text-gray-50 font-medium">{review.movie_title}</TableCell>
                        <TableCell className="text-gray-50">{review.user_username}</TableCell>
                        <TableCell className="text-gray-50">{review.rating}</TableCell>
                        <TableCell className="text-gray-50">{review.content}</TableCell>
                        <TableCell className="text-gray-50">{review.created_at}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" className="text-purple-400 hover:text-purple-300"><Edit className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="text-pink-400 hover:text-pink-300" onClick={() => handleDelete('review', review.id)}><Trash2 className="h-4 w-4" /></Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 flex justify-between items-center">
                  <Button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className="bg-purple-500 hover:bg-purple-600">Previous</Button>
                  <span>{currentPage} / {totalPages}</span>
                  <Button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages} className="bg-purple-500 hover:bg-purple-600">Next</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      <Footer />
    </div>
  )
}

