"use client";

import axios from "../../lib/api"; // Axios 인스턴스 import
import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation"; // useRouter 가져오기

type FormData = {
  email: string;
  password: string;
};

type FormErrors = {
  [K in keyof FormData]?: string;
};

const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }> = ({
  label,
  error,
  ...props
}) => (
  <div className="space-y-2">
    <label htmlFor={props.id} className="block text-sm font-medium text-gray-200">
      {label}
    </label>
    <input
      {...props}
      className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-md text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
    />
    {error && <p className="text-sm text-red-500">{error}</p>}
  </div>
);

const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "outline" }> = ({
  variant = "primary",
  children,
  ...props
}) => (
  <button
    {...props}
    className={`px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 ${
      variant === "primary"
        ? "w-full text-white bg-purple-600 hover:bg-purple-700 focus:ring-purple-500"
        : "bg-gray-700 text-gray-200 hover:bg-gray-600 focus:ring-gray-500"
    }`}
  >
    {children}
  </button>
);

const handleGoogleLogin = () => {
  window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/accounts/google/login/`;
};

const SocialLoginButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { icon: string; label: string }> = ({
  icon,
  label,
  ...props
}) => (
  <Button variant="outline" {...props}>
    <span className="sr-only">Login with {label}</span>
    <span className="flex items-center justify-center">{icon}</span>
  </Button>
);

export default function LoginPage() {
  const [formData, setFormData] = useState<FormData>({
    email: "",
    password: "",
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false); // 로딩 상태 추가
  const router = useRouter(); // useRouter 사용

  // 폼 유효성 검사 함수
  const validateForm = useCallback(() => {
    const newErrors: FormErrors = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters long";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  useEffect(() => {
    validateForm();
  }, [formData, validateForm]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      setIsLoading(true); // 로딩 상태 활성화
      try {
        const response = await axios.post("/auth/login/", formData); // Django Auth Login 엔드포인트 호출
        console.log("로그인 응답 데이터:", response.data); // 응답 데이터 확인

        // 백엔드에서 반환된 데이터를 구조분해 할당으로 추출
        const { access_token, refresh_token, user } = response.data;

        // 토큰을 로컬 스토리지에 저장
        localStorage.setItem("accessToken", access_token);
        localStorage.setItem("refreshToken", refresh_token);

        // 유저 정보 출력 (선택)
        console.log("로그인한 유저 정보:", user);

        // 메인 페이지로 이동
        router.push("/");
      } catch (error: unknown) {
        console.error("Login failed:", error);
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 401) {
            setErrors({ email: "Invalid email or password" });
          } else {
            alert("An error occurred. Please try again.");
          }
        } else {
          alert("An unexpected error occurred. Please try again.");
        }
      } finally {
        setIsLoading(false); // 로딩 상태 비활성화
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-gray-800 text-gray-100 rounded-lg shadow-xl overflow-hidden">
        <div className="p-6 sm:p-8">
          <h2 className="text-2xl font-bold text-center mb-6">Login to MovieRec</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              label="Email"
              id="email"
              name="email"
              type="email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              required
            />
            <Input
              label="Password"
              id="password"
              name="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              required
            />
            <Button type="submit">{isLoading ? "Logging in..." : "Login"}</Button>
          </form>
          <div className="mt-4 flex items-center justify-between">
            <span className="border-b w-1/5 md:w-1/4"></span>
            <span className="text-xs text-gray-400 uppercase">or login with</span>
            <span className="border-b w-1/5 md:w-1/4"></span>
          </div>
          <div className="flex justify-center space-x-4 mt-4">
            <SocialLoginButton 
            icon="G"
            label="Google"
            onClick={handleGoogleLogin}
             />
            <SocialLoginButton icon="f" label="Facebook" />
            <SocialLoginButton icon="K" label="Kakao" />
            <SocialLoginButton icon="N" label="Naver" />
          </div>
        </div>
        <div className="px-6 py-4 bg-gray-700 flex justify-between">
          <Link href="/forgot-password" className="text-sm text-purple-400 hover:underline">
            Forgot password?
          </Link>
          <Link href="/register" className="text-sm text-purple-400 hover:underline">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
}
