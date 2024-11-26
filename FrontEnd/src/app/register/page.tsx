"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import axios from "../../lib/api";
import { useRouter } from "next/navigation";

type FormData = {
  username: string;
  email: string;
  password1: string;
  password2: string;
  phone_number: string;
  date_of_birth: string;
  bio: string;
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

const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string }> = ({
  label,
  error,
  ...props
}) => (
  <div className="space-y-2">
    <label htmlFor={props.id} className="block text-sm font-medium text-gray-200">
      {label}
    </label>
    <textarea
      {...props}
      className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-md text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
    />
    {error && <p className="text-sm text-red-500">{error}</p>}
  </div>
);

const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = (props) => (
  <button
    {...props}
    className="w-full px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800"
  />
);

export default function RegistrationPage() {
  const router = useRouter();

  const [formData, setFormData] = useState<FormData>({
    username: "",
    email: "",
    password1: "",
    password2: "",
    phone_number: "",
    date_of_birth: "",
    bio: "",
  });

  const [errors, setErrors] = useState<FormErrors>({});

  const validateForm = () => {
    const newErrors: FormErrors = {};

    if (!formData.username) {
      newErrors.username = "Username is required";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters long";
    }

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }

    if (!formData.password1) {
      newErrors.password1 = "Password is required";
    } else if (formData.password1.length < 8) {
      newErrors.password1 = "Password must be at least 8 characters long";
    }

    if (!formData.password2) {
      newErrors.password2 = "Please confirm your password";
    } else if (formData.password1 !== formData.password2) {
      newErrors.password2 = "Passwords do not match";
    }

    if (formData.phone_number && !/^\+?[1-9]\d{1,14}$/.test(formData.phone_number)) {
      newErrors.phone_number = "Invalid phone number";
    }

    if (!formData.date_of_birth) {
      newErrors.date_of_birth = "Date of birth is required";
    } else {
      const date = new Date(formData.date_of_birth);
      const now = new Date();
      if (isNaN(date.getTime()) || date > now) {
        newErrors.date_of_birth = "Invalid date of birth";
      }
    }

    if (formData.bio && formData.bio.length > 500) {
      newErrors.bio = "Bio must be 500 characters or less";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  useEffect(() => {
    validateForm();
  }, [formData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      try {
        // 빈 문자열 처리: 빈 값일 경우 null로 변경
        const dataToSend = {
          ...formData,
          date_of_birth: formData.date_of_birth || null, // 빈 문자열을 null로 처리
        };

        console.log("Sending data:", dataToSend);
        const response = await axios.post("/auth/registration/", formData);

        console.log("Registration successful:", response.data);

        // 로그인 처리: 백엔드에서 발급받은 토큰을 저장
        const loginResponse = await axios.post("/auth/login/", {
          email: formData.email,
          password: formData.password1,
        });

        // 로그인 응답에서 토큰 추출
        const { access_token, refresh_token } = loginResponse.data;

        // 토큰 저장
        localStorage.setItem("accessToken", access_token);
        localStorage.setItem("refreshToken", refresh_token);

        alert("Registration and login successful!");
        router.push("/"); // 메인 페이지로 리다이렉트
      } catch (error: any) {
        console.error("Error during registration:", error);
        if (error.response && error.response.data) {
          setErrors(error.response.data);
        } else {
          alert("An error occurred. Please try again.");
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-gray-800 text-gray-100 rounded-lg shadow-xl overflow-hidden">
        <div className="p-6 sm:p-8">
          <h2 className="text-2xl font-bold text-center mb-6">Join MovieRec Community</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <Input
                label="Username"
                id="username"
                name="username"
                placeholder="Enter your username"
                value={formData.username}
                onChange={handleChange}
                error={errors.username}
                required
              />
              <Input
                label="Email"
                id="email"
                name="email"
                type="email"
                placeholder="Enter your email address"
                value={formData.email}
                onChange={handleChange}
                error={errors.email}
                required
              />
              <Input
                label="Password"
                id="password1"
                name="password1"
                type="password"
                placeholder="Create a password"
                value={formData.password1}
                onChange={handleChange}
                error={errors.password1}
                required
              />
              <Input
                label="Confirm Password"
                id="password2"
                name="password2"
                type="password"
                placeholder="Re-enter your password"
                value={formData.password2}
                onChange={handleChange}
                error={errors.password2}
                required
              />
              <Input
                label="Date of Birth"
                id="date_of_birth"
                name="date_of_birth"
                type="date"
                value={formData.date_of_birth}
                onChange={handleChange}
                error={errors.date_of_birth}
              />
              <Input
                label="Phone Number (Optional)"
                id="phone_number"
                name="phone_number"
                placeholder="Enter your phone number"
                value={formData.phone_number}
                onChange={handleChange}
                error={errors.phone_number}
              />
            </div>
            <Textarea
              label="Bio (Optional)"
              id="bio"
              name="bio"
              placeholder="Write a brief bio about yourself"
              rows={4}
              value={formData.bio}
              onChange={handleChange}
              error={errors.bio}
            />
            <Button type="submit">Create Account</Button>
          </form>
        </div>
        <div className="px-6 py-4 bg-gray-700 text-center">
          <p className="text-sm text-gray-400">
            Already have an account?{" "}
            <Link href="/login" className="text-purple-400 hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
