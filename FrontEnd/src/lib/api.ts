import axios from "axios";
import jwt_decode from "jwt-decode"; // 토큰에서 사용자 ID를 추출하기 위한 라이브러리

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: "http://127.0.0.1:8000", // Django 서버 주소
  timeout: 40000, // 요청 제한 시간 (10초)
});

// 요청 인터셉터: Authorization 헤더에 액세스 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    console.log("Authorization Header:", token); // 콘솔에서 토큰 확인
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터: 토큰 만료 시 갱신 처리
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refreshToken");
        if (!refreshToken) {
          console.error("리프레시 토큰이 없습니다. 다시 로그인하세요.");
          alert("로그인이 만료되었습니다. 다시 로그인하세요.");
          window.location.href = "/login";
          return Promise.reject(error);
        }

        // 리프레시 토큰으로 새 액세스 토큰 발급
        const response = await axios.post(
          "http://127.0.0.1:8000/auth/token/refresh/",
          { refresh: refreshToken }
        );
        const newAccessToken = response.data.access;

        // 새로운 액세스 토큰 저장 및 요청 헤더 갱신
        localStorage.setItem("accessToken", newAccessToken);
        originalRequest.headers["Authorization"] = `Bearer ${newAccessToken}`;
        return api(originalRequest); // 원래 요청 재전송
      } catch (refreshError) {
        console.error("토큰 갱신 실패:", refreshError);
        alert("로그인 세션이 만료되었습니다. 다시 로그인하세요.");
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

// 로그아웃 함수
export const logout = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  alert("로그아웃 되었습니다.");
  window.location.href = "/login";
};

// 로그인 함수
export const login = async (formData: { email: string; password: string }) => {
  try {
    const response = await api.post("/auth/login/", formData);
    const { access: accessToken, refresh: refreshToken } = response.data;
    localStorage.setItem("accessToken", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
    alert("로그인 성공!");
    window.location.href = "/";
  } catch (error: any) {
    console.error("로그인 실패:", error.response?.data || error);
    alert("로그인 실패. 입력 정보를 확인하세요.");
  }
};

// 회원가입 함수
export const register = async (formData: {
  username: string;
  email: string;
  password1: string;
  password2: string;
  phone_number?: string;
  date_of_birth?: string;
  bio?: string;
}) => {
  try {
    const response = await api.post("/auth/registration/", formData);
    alert("회원가입 성공! 이제 로그인하세요.");
    window.location.href = "/login";
  } catch (error: any) {
    console.error("회원가입 실패:", error.response?.data || error);
    alert("회원가입 실패. 입력 정보를 확인하세요.");
  }
};

// 보호된 API 요청
export const fetchProtectedData = async () => {
  try {
    const response = await api.get("/protected-endpoint/");
    console.log("보호된 데이터:", response.data);
  } catch (error: any) {
    if (error.response?.status === 401) {
      alert("로그인이 필요합니다. 다시 로그인하세요.");
      logout();
    } else {
      console.error("보호된 데이터 요청 실패:", error);
    }
  }
};




// 현재 사용자 ID 가져오는 함수 추가
export const getCurrentUserId = () => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    const decodedToken: any = jwt_decode(token);
    return decodedToken.user_id;
  }
  return null;
};

// 게시글 수정 함수 (PATCH 요청)
export const updatePost = (postId: number, data: { title?: string; content?: string }) => {
  return api.patch(`/community/posts/${postId}/update/`, data);
};

// 게시글 삭제
export const deletePost = (postId: number) => {
  return api.delete(`/community/posts/${postId}/delete/`);
};

// 리뷰 수정 함수 (PATCH 요청)
export const updateReview = (reviewId: number, data: { title?: string; content?: string; rating?: number }) => {
  return api.patch(`/community/reviews/${reviewId}/update/`, data);
};

// 리뷰 삭제
export const deleteReview = (reviewId: number) => {
  return api.delete(`/community/reviews/${reviewId}/delete/`);
};

// 댓글 수정
export const updateComment = (commentId: number, data: { content: string }) => {
  return api.patch(`/community/comments/${commentId}/update/`, data);
};

// 댓글 삭제
export const deleteComment = (commentId: number) => {
  return api.delete(`/community/comments/${commentId}/delete/`);
};

// 댓글 좋아요 토글
export const toggleCommentLike = (commentId: number) => {
  return api.post(`/community/comments/${commentId}/like-toggle/`);
};

// 댓글 싫어요 토글
export const toggleCommentDislike = (commentId: number) => {
  return api.post(`/community/comments/${commentId}/dislike-toggle/`);
};


// 팔로우/언팔로우 토글
export const toggleFollow = (userId: number) => {
  return api.post(`/accounts/users/${userId}/follow/`);
};

// Social 탭 데이터 삭제 (팔로워/팔로잉/맞팔로우 삭제)
export const deleteSocialData = (
  userId: number,
  data: { action: string; target_user_id: number }
) => {
  return api.delete(`/accounts/users/${userId}/social/delete/`, {
    params: data, // 쿼리 매개변수로 전달
  });
};








export default api;
