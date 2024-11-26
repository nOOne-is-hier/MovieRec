'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { Home, Users, LogOut, User, Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import api, { logout } from '@/lib/api'
import { NotificationsModal } from './NotificationsModal'
import UserProfileModal from './UserProfileModal' // UserProfileModal import 추가


interface Notification {
  id: number
  type: 'comment' | 'reply' | 'like' | 'follow'
  content: string
  created_at: string
  is_read: boolean
  link: string | null
}

const Navbar = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [nickname, setNickname] = useState('')
  const [userId, setUserId] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false) // 프로필 모달 상태 추가


  // 사용자 데이터 가져오기
  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        console.log('토큰이 없습니다. 로그아웃 처리합니다.');
        handleLogout();
        return;
      }
  
      console.log('사용자 데이터를 가져오는 중...');
      const response = await api.get('/auth/user/', {
        headers: { Authorization: `Bearer ${token}` },
      });
  
      console.log('API 응답:', response.data);
      const { username, pk, email } = response.data;
      
      if (username) {
        console.log(`닉네임 설정: ${username}`);
        setNickname(username);
        sessionStorage.setItem('nickname', username);
        localStorage.setItem('nickname', username);
      } else {
        console.warn('API 응답에 username이 없습니다.');
      }
      
      if (pk) {
        console.log(`userId 설정: ${pk}`);
        setUserId(String(pk));
        sessionStorage.setItem('userId', String(pk));
        localStorage.setItem('userId', String(pk));
      } else {
        console.warn('API 응답에 pk가 없습니다.');
      }

      if (email) {
        console.log(`이메일 설정: ${email}`);
        sessionStorage.setItem('userEmail', email);
        localStorage.setItem('userEmail', email);
      } else {
        console.warn('API 응답에 email이 없습니다.');
      }
    } catch (error) {
      console.error('사용자 데이터 가져오기 실패:', error);
      alert('사용자 정보를 가져오는데 실패했습니다. 다시 로그인해주세요.');
      handleLogout();
    }
  };
  
  const initializeUserData = () => {
    console.log('사용자 데이터 초기화 중...');
    const storedNickname = sessionStorage.getItem('nickname') || localStorage.getItem('nickname');
    const storedUserId = sessionStorage.getItem('userId') || localStorage.getItem('userId');

    console.log('저장된 데이터:', {
      nickname: storedNickname,
      userId: storedUserId,
      email: localStorage.getItem('userEmail') || sessionStorage.getItem('userEmail')
    });

    if (storedNickname) {
      console.log(`저장된 닉네임 사용: ${storedNickname}`);
      setNickname(storedNickname);
    }
    if (storedUserId) {
      console.log(`저장된 userId 사용: ${storedUserId}`);
      setUserId(storedUserId);
    }

    if (!storedNickname || !storedUserId) {
      console.log('저장된 데이터가 없거나 불완전합니다. API 호출을 시도합니다.');
      fetchUserData();
    }
  };

  // 특정 경로를 제외하고 사용자 데이터 초기화
  useEffect(() => {
    const excludedPaths = ['/login', '/forgot-password', '/register'];

    if (!excludedPaths.includes(pathname)) {
      console.log(`현재 경로: ${pathname}. 사용자 데이터 초기화를 시도합니다.`);
      initializeUserData();
    } else {
      console.log(`현재 경로: ${pathname}. 사용자 데이터 초기화를 건너뜁니다.`);
    }

    console.log('현재 상태:', { nickname, userId });
    setIsLoading(false);
  }, [pathname, router]);

  // 검색 폼 제출
  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const query = searchQuery.trim()
    const url = query ? `/search?q=${encodeURIComponent(query)}` : '/search'
    router.push(url)
  }

  // 로그아웃
  const handleLogout = () => {
    console.log('로그아웃 처리 중...');
    sessionStorage.clear()
    localStorage.removeItem('nickname')
    localStorage.removeItem('userId')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('accessToken')
    setNickname('')
    setUserId('')
    logout()
    console.log('로그아웃 완료. 로그인 페이지로 이동합니다.');
    router.push('/login')
  }

  return (
    <nav className="fixed top-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* 로고 */}
          <div className="flex-shrink-0">
            <button onClick={() => router.push('/')} className="flex items-center">
              <span className="text-xl font-bold text-purple-500">MovieRec</span>
            </button>
          </div>

          {/* 검색 폼 */}
          <div className="flex-1 max-w-xl mx-4">
            <form onSubmit={handleSearch} className="flex items-center">
              <Input
                type="search"
                placeholder="배우, 감독, 유저 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white/10 border-gray-700 text-white placeholder-gray-400 focus:ring-purple-500 focus:border-purple-500"
              />
            </form>
          </div>

          {/* 사용자 정보 */}
          <div className="w-48 text-gray-300 mr-4 text-sm font-medium overflow-hidden whitespace-nowrap text-right">
            {isLoading ? (
              <span className="opacity-0">로딩 중...</span>
            ) : nickname ? (
              <span className="truncate">{`안녕하세요, ${nickname}님`}</span>
            ) : (
              <span className="truncate">로그인이 필요합니다</span>
            )}
          </div>

          {/* 네비게이션 */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/')}
              className={`text-gray-300 hover:bg-gray-800/40 hover:text-white px-3 py-2 rounded-md text-sm font-medium ${pathname === '/' ? 'bg-gray-800/40 text-white' : ''
                }`}
            >
              <Home className="w-5 h-5 inline-block mr-1" />
              홈
            </button>
            <button
              onClick={() => router.push('/community/')}
              className={`text-gray-300 hover:bg-gray-800/40 hover:text-white px-3 py-2 rounded-md text-sm font-medium ${pathname === '/community' ? 'bg-gray-800/40 text-white' : ''
                }`}
            >
              <Users className="w-5 h-5 inline-block mr-1" />
              커뮤니티
            </button>
            <button
              onClick={() => setIsProfileModalOpen(true)} // 프로필 모달 열기
              className="text-gray-300 hover:bg-gray-800/40 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
            >
              <User className="w-5 h-5 inline-block mr-1" />
              프로필
            </button>

            {/* 알림 */}
            <NotificationsModal
              trigger={
                <button className="text-gray-300 hover:bg-gray-800/40 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  <Bell className="w-5 h-5 inline-block mr-1" />
                  알림
                </button>
              }
            />

            {/* 로그아웃 */}
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="text-gray-300 hover:bg-gray-800/40 hover:text-white px-3 py-2"
            >
              <LogOut className="w-5 h-5" />
              로그아웃
            </Button>
          </div>
        </div>
      </div>

      {/* User Profile Modal */}
      {isProfileModalOpen && userId && (
      <UserProfileModal
        isOpen={isProfileModalOpen}
        userId={Number(userId)} // 숫자로 변환
        onClose={() => setIsProfileModalOpen(false)}
      />
    )}
    </nav>
  )
}

export default Navbar

