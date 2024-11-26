import MovieListPage from '@/components/movie-list-page'

export default function Home() {
  // MovieListPage 컴포넌트가 클라이언트 컴포넌트이므로 
  // 서버 컴포넌트인 페이지에서 직접 렌더링할 수 있습니다
  return <MovieListPage />
}