"use client";

import React, { useState } from "react";
import axios from "../../lib/api"; // Axios 인스턴스

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await axios.post("/auth/password/reset/", { email }); // Django 엔드포인트 호출
      setIsSubmitted(true);
    } catch (error: any) {
      console.error("Error resetting password:", error);
      if (error.response?.status === 400) {
        setError("Email is not registered.");
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-gray-800 text-gray-100 rounded-lg shadow-xl overflow-hidden">
        <div className="p-6 sm:p-8">
          <h2 className="text-2xl font-bold text-center mb-6">
            Reset Your Password
          </h2>
          {isSubmitted ? (
            <p className="text-sm text-gray-400">
              If the email you entered is registered, you'll receive a password
              reset link shortly.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-200"
                >
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-md text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                className="w-full px-4 py-2 text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-purple-500"
              >
                Send Reset Link
              </button>
              {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
