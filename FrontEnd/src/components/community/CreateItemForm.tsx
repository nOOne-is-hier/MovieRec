'use client';

import { useState, useEffect, useMemo } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Star, Bold, Italic, UnderlineIcon, List, ListOrdered, AlignLeft, AlignCenter, AlignRight, LinkIcon, ImageIcon } from 'lucide-react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';

interface Movie {
  id: number;
  title: string;
  poster_path: string | null;
}

interface CreateItemFormProps {
  type: 'post' | 'review';
  onSubmit: (item: { title: string; content: string; movie?: number; rating?: number }) => void;
}

export const CreateItemForm: React.FC<CreateItemFormProps> = ({ type, onSubmit }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [movies, setMovies] = useState<Movie[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [rating, setRating] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const fetchMovies = async () => {
    try {
      const response = await fetch(`http://localhost:8000/community/review-movies/`);
      const data = await response.json();
      setMovies(data);
    } catch (error) {
      console.error('영화 목록 로드 실패:', error);
    }
  };

  useEffect(() => {
    if (type === 'review') {
      fetchMovies();
    }
  }, [type]);

  const filteredMovies = useMemo(() => {
    return movies.filter(movie =>
      movie.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [movies, searchTerm]);

  const handleMovieSelect = (movie: Movie) => {
    setSelectedMovie(movie);
    setSearchTerm(movie.title);
    setShowDropdown(false);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setShowDropdown(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 영화가 선택되었는데 평점이 없는 경우 방지
    if (type === 'review' && selectedMovie && !rating) {
      alert('영화를 선택한 경우, 반드시 평점을 입력해야 합니다.');
      return;
    }

    // 요청 데이터 타입 정의
    interface RequestData {
      title: string;
      content: string;
      movie?: number;
      rating: number;
    }

    // 요청 데이터 구성
    const requestData: RequestData = {
      title,
      content,
      rating: rating || 0,  // 평점이 없으면 0으로 설정
    };

    // 영화와 평점이 있는 경우만 추가
    if (type === 'review' && selectedMovie) {
      requestData.movie = selectedMovie.id;
    }
  
    try {
      await onSubmit(requestData);
    } catch (error) {
      console.error('요청 오류:', error);
      alert('리뷰 작성 중 문제가 발생했습니다.');
    }
  };

  
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Link.configure({
        openOnClick: false,
      }),
      Image,
    ],
    content: content,
    onUpdate: ({ editor }) => {
      setContent(editor.getHTML());
    },
  });

  const addLink = () => {
    const url = window.prompt('URL을 입력하세요:');
    if (url) {
      editor?.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
    }
  };

  const addImage = () => {
    const url = window.prompt('이미지 URL을 입력하세요:');
    if (url) {
      editor?.chain().focus().setImage({ src: url }).run();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 w-full max-w-4xl mx-auto p-6">
      <div className="space-y-2">
        <Label htmlFor="title" className="text-[#333333] dark:text-white">제목</Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="제목을 입력하세요"
          required
          className="bg-white dark:bg-[#1E1E1E] text-[#333333] dark:text-white border-[#E0E0E0] dark:border-[#333333] focus:ring-[#007BFF] dark:focus:ring-[#FF5733]"
        />
      </div>

      {type === 'review' && (
        <div className="space-y-2 relative">
          <Label htmlFor="movie" className="text-[#333333] dark:text-white">영화 검색(선택)</Label>
          <Input
            id="movie"
            value={searchTerm}
            onChange={handleSearchChange}
            placeholder="영화를 검색하세요"
            onFocus={() => setShowDropdown(true)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 100)}
            className="mb-2 bg-white dark:bg-[#1E1E1E] text-[#333333] dark:text-white border-[#E0E0E0] dark:border-[#333333] focus:ring-[#007BFF] dark:focus:ring-[#FF5733]"
          />
          {showDropdown && (
            <div className="absolute bg-white shadow-md border border-gray-200 max-h-60 overflow-y-auto w-full z-10">
              {filteredMovies.length > 0 ? (
                filteredMovies.map((movie) => (
                  <div
                    key={movie.id}
                    onClick={() => handleMovieSelect(movie)}
                    className="cursor-pointer p-2 hover:bg-gray-100 text-black"
                  >
                    {movie.title}
                  </div>
                ))
              ) : (
                <div className="p-2 text-gray-500">검색 결과가 없습니다.</div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="content" className="text-[#333333] dark:text-white">내용</Label>
        <div className="border border-[#E0E0E0] dark:border-[#333333] rounded-md overflow-hidden">
          <div className="bg-gray-100 dark:bg-gray-800 p-2 flex flex-wrap gap-2">
            <Button
              type="button"
              onClick={() => editor?.chain().focus().toggleBold().run()}
              className={`p-2 ${editor?.isActive('bold') ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <Bold className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().toggleItalic().run()}
              className={`p-2 ${editor?.isActive('italic') ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <Italic className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().toggleUnderline().run()}
              className={`p-2 ${editor?.isActive('underline') ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <UnderlineIcon className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().toggleBulletList().run()}
              className={`p-2 ${editor?.isActive('bulletList') ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <List className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().toggleOrderedList().run()}
              className={`p-2 ${editor?.isActive('orderedList') ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <ListOrdered className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().setTextAlign('left').run()}
              className={`p-2 ${editor?.isActive({ textAlign: 'left' }) ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <AlignLeft className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().setTextAlign('center').run()}
              className={`p-2 ${editor?.isActive({ textAlign: 'center' }) ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <AlignCenter className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={() => editor?.chain().focus().setTextAlign('right').run()}
              className={`p-2 ${editor?.isActive({ textAlign: 'right' }) ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <AlignRight className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={addLink}
              className={`p-2 ${editor?.isActive('link') ? 'bg-gray-300 dark:bg-gray-600' : ''}`}
            >
              <LinkIcon className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              onClick={addImage}
              className="p-2"
            >
              <ImageIcon className="w-4 h-4" />
            </Button>
          </div>
          <EditorContent editor={editor} className="bg-white dark:bg-[#1E1E1E] text-[#333333] dark:text-white p-4 min-h-[400px]" />
        </div>
      </div>

      {type === 'review' && (
        <div className="space-y-2">
          <Label className="text-[#333333] dark:text-white">별점 (1-5)</Label>
          <div className="flex space-x-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <Star
                key={star}
                onClick={() => setRating(star)}
                className={`w-6 h-6 cursor-pointer transition-colors duration-200 ${
                  rating >= star ? 'text-[#FFC300] fill-[#FFC300]' : 'text-[#E0E0E0] dark:text-[#333333]'
                }`}
              />
            ))}
          </div>
        </div>
      )}

      <Button
        type="submit"
        className="w-full bg-[#007BFF] dark:bg-[#FF5733] text-white hover:bg-[#0056B3] dark:hover:bg-[#FF7043] transition-colors duration-200"
      >
        {type === 'post' ? '게시글 작성' : '리뷰 작성'}
      </Button>
    </form>
  );
};
