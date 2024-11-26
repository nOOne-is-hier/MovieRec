'use client';

import { useEffect, useState } from 'react';
import { ThemeProvider } from "next-themes";

export default function CommunityLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true); // 클라이언트에서만 렌더링하도록 설정
  }, []);

  if (!mounted) {
    return <div className="min-h-screen bg-background text-foreground">로딩 중...</div>;
  }

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system" // 시스템 테마 기본 사용
      enableSystem // 시스템 다크 모드 사용 허용
      disableTransitionOnChange // 초기 전환 애니메이션 비활성화
    >
      <div className="min-h-screen">{children}</div>
    </ThemeProvider>
  );
}
