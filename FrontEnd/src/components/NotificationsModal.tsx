'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Bell, MessageSquare, Heart, UserPlus, MessageCircle, Trash2, Check, Filter } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

interface Notification {
  id: number
  type: 'comment' | 'reply' | 'like' | 'follow'
  content: string
  created_at: string
  is_read: boolean
  link: string | null
}

interface NotificationsModalProps {
  trigger?: React.ReactNode;
}

export function NotificationsModal({ trigger }: NotificationsModalProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    fetchNotifications()
  }, [filter])

  const fetchNotifications = async () => {
    try {
      // 로그인 상태 확인: 로컬 스토리지에서 JWT 토큰이 있는지 확인
      const token = localStorage.getItem('accessToken'); // 'token'은 저장된 JWT 키 이름
  
      if (!token) {
        // 토큰이 없으면 실행하지 않고 경고 로그 출력
        console.warn('User is not logged in. Notifications cannot be fetched.');
        return;
      }
  
      // API 요청에 토큰을 헤더에 추가
      let url = '/accounts/notifications/';
      if (filter && filter !== 'all') {  // filter가 'all'이 아닐 때만 필터링
        url += `?type=${filter}`;
      }
  
      const response = await api.get(url, {
        headers: {
          Authorization: `Bearer ${token}`, // 헤더에 토큰 추가
        },
      });
  
      console.log(response.config.headers);
  
      // 응답 데이터 처리
      setNotifications(response.data);
      setUnreadCount(response.data.filter((n: Notification) => !n.is_read).length);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };
  

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'like':
        return <Heart className="h-4 w-4 text-red-500" />
      case 'comment':
        return <MessageSquare className="h-4 w-4 text-blue-500" />
      case 'reply':
        return <MessageCircle className="h-4 w-4 text-green-500" />
      case 'follow':
        return <UserPlus className="h-4 w-4 text-purple-500" />
    }
  }

  const markAllAsRead = async () => {
    try {
      await api.post('/accounts/notifications/mark-all-read/')
      await fetchNotifications()
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  const toggleReadStatus = async (id: number) => {
    try {
      await api.post(`/accounts/notifications/toggle_notification_read_status/${id}/`)
      await fetchNotifications()
    } catch (error) {
      console.error('Failed to toggle read status:', error)
    }
  }

  const deleteNotification = async (id: number) => {
    try {
      await api.delete(`/accounts/notifications/${id}/delete/`)
      await fetchNotifications()
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  }

  const deleteAllNotifications = async () => {
    try {
      await api.delete('/accounts/notifications/delete-all/')
      await fetchNotifications()
    } catch (error) {
      console.error('Failed to delete all notifications:', error)
    }
  }

  const handleNotificationClick = (link: string | null) => {
    if (link) {
      window.location.href = link
    }
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        {trigger || (
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <Badge variant="destructive" className="absolute -top-1 -right-1 px-1 min-w-[1.25rem] h-5">
                {unreadCount}
              </Badge>
            )}
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-[380px] p-0" align="end">
        <Card className="border-0">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl font-bold">알림</CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={markAllAsRead}
                  className="h-8 px-2 text-xs font-medium"
                >
                  <Check className="mr-1 h-4 w-4" />
                  모두 읽음
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={deleteAllNotifications}
                  className="h-8 px-2 text-xs font-medium"
                >
                  <Trash2 className="mr-1 h-4 w-4" />
                  모든 알림 삭제
                </Button>
              </div>
            </div>
            <Separator className="my-2" />
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select onValueChange={setFilter} value={filter}>
                <SelectTrigger className="h-8 w-[140px] border-2">
                  <SelectValue placeholder="모든 알림" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">모든 알림</SelectItem>
                  <SelectItem value="comment">댓글</SelectItem>
                  <SelectItem value="reply">답글</SelectItem>
                  <SelectItem value="like">좋아요</SelectItem>
                  <SelectItem value="follow">팔로우</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[400px]">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 gap-2">
                  <Bell className="h-8 w-8 text-muted-foreground" />
                  <p className="text-muted-foreground font-medium">알림이 없습니다</p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`group flex items-start space-x-4 p-4 hover:bg-muted/50 transition-colors cursor-pointer border-b last:border-b-0 ${notification.is_read ? 'bg-muted/30' : 'bg-background'
                      }`}
                    onClick={() => handleNotificationClick(notification.link)}
                  >
                    <Avatar className="h-10 w-10 border">
                      <AvatarImage src={`/placeholder.svg?height=40&width=40`} alt="User Avatar" />
                      <AvatarFallback>UN</AvatarFallback>
                    </Avatar>

                    <div className="flex-1 space-y-1">
                      <p className="text-sm leading-relaxed">{notification.content}</p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="flex items-center space-x-1">
                          {getIcon(notification.type)}
                          <span>{new Date(notification.created_at).toLocaleString()}</span>
                        </span>
                        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              toggleReadStatus(notification.id)
                            }}
                            className="h-7 px-2 text-xs font-medium"
                          >
                            {notification.is_read ? '읽지 않음으로 표시' : '읽음으로 표시'}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteNotification(notification.id)
                            }}
                            className="h-7 px-2 text-xs font-medium text-destructive hover:text-destructive"
                          >
                            삭제
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </PopoverContent>
    </Popover>
  )
}

