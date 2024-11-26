// EditItemForm.tsx

import { useState } from 'react';
import { Button } from '@/components/ui/button';

interface EditItemFormProps {
  item: PostDetail | ReviewDetail;
  onSubmit: (data: { title: string; content: string; rating?: number }) => void;
  onCancel: () => void;
}

export const EditItemForm: React.FC<EditItemFormProps> = ({ item, onSubmit, onCancel }) => {
  const [title, setTitle] = useState(item.title);
  const [content, setContent] = useState(item.content);
  const [rating, setRating] = useState('movie' in item ? item.rating : undefined);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const updatedData: { title: string; content: string; rating?: number } = { title, content };
    if ('movie' in item && rating !== undefined) {
      updatedData.rating = rating;
    }
    onSubmit(updatedData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* 제목 입력 */}
      <div>
        <label>제목</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>
      {/* 내용 입력 */}
      <div>
        <label>내용</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
        />
      </div>
      {/* 리뷰인 경우 평점 입력 */}
      {'movie' in item && (
        <div>
          <label>평점</label>
          <input
            type="number"
            value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
            min={1}
            max={5}
            required
          />
        </div>
      )}
      <div className="flex space-x-2">
        <Button type="submit">수정 완료</Button>
        <Button variant="secondary" onClick={onCancel}>
          취소
        </Button>
      </div>
    </form>
  );
};
