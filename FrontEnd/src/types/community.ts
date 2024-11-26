export interface User {
    id: number;
    username: string;
    profile_image: string;
    profile_url: string;
  }
  
  export interface Comment {
    id: number;
    user: User;
    content: string;
    created_at: string;
    parent: number | null;
    like_count: number;
    dislike_count: number;
    is_liked: boolean;
    is_disliked: boolean;
    replies: Comment[]; // 추가된 부분
  }
  
  export interface Post {
    id: number;
    title: string;
    content: string;
    created_at: string;
    user: User;
    like_count: number;
    comment_count: number;
  }
  
  export interface Review extends Post {
    rating: number;
    movie: {
      id: number;
      title: string;
      poster_path: string;
      movie_url: string;
    };
  }
  
  export interface PostDetail extends Post {
    updated_at: string;
    is_liked: boolean;
    comments: Comment[];
  }
  
  export interface ReviewDetail extends Review {
    updated_at: string;
    is_liked: boolean;
    comments: Comment[];
  }
  
  