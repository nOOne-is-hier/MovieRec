import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface CommentFormProps {
  onSubmit: (content: string, parent?: number | null) => void; // parent로 수정
  parent?: number | null;
}

export const CommentForm: React.FC<CommentFormProps> = ({ onSubmit, parent }) => {
  const [content, setContent] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (content.trim()) {
      console.log("Submitting comment:", { content, parent }); // parent로 변경
      onSubmit(content, parent); // parent로 변경
      setContent('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="댓글을 입력하세요"
        className="w-full p-3 text-sm bg-white dark:bg-[#1E1E1E] text-[#333333] dark:text-white border border-[#E0E0E0] dark:border-[#333333] rounded-md focus:outline-none focus:ring-2 focus:ring-[#007BFF] dark:focus:ring-[#FF5733] transition duration-300 resize-none"
      />
      <Button 
        type="submit"
        className="w-full md:w-auto px-6 py-2 bg-[#007BFF] dark:bg-[#FF5733] text-white font-semibold rounded-md hover:bg-[#0056B3] dark:hover:bg-[#FF7043] transition duration-300 focus:outline-none focus:ring-2 focus:ring-[#007BFF] dark:focus:ring-[#FF5733] shadow-md"
      >
        댓글 작성
      </Button>
    </form>
  );
};
