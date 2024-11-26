"use client";

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import axios from '../../../lib/api';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const code = searchParams.get('code');
    if (code) {
      axios.post('/dj-rest-auth/google/', { code })
        .then(response => {
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('accessToken', access_token);
          localStorage.setItem('refreshToken', refresh_token);
          router.push('/');
        })
        .catch(error => {
          console.error('Google login error:', error);
          router.push('/login');
        });
    }
  }, [router, searchParams]);

  return <div>Processing login...</div>;
}