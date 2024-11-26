import { Comment } from '@/types/community';
import { CommentItem } from './CommentItem';
import { useMemo } from 'react';

interface CommentListProps {
  comments: Comment[];
  onCommentSubmit: (content: string, parent: number | null) => void;
  fetchItemDetail: () => void;
}

export const CommentList: React.FC<CommentListProps> = ({ comments, onCommentSubmit, fetchItemDetail }) => {
  // 최상위 댓글만 필터링하는 함수
  const filterTopLevelComments = (comments: Comment[]): Comment[] => {
    return comments.filter(comment => comment.parent === null);
  };

  // useMemo를 사용하여 최상위 댓글 목록 렌더링
  const commentItems = useMemo(() => {
    const topLevelComments = filterTopLevelComments(comments);
    return topLevelComments.map((comment) => (
      <CommentItem 
        key={comment.id} 
        comment={comment} 
        onReply={onCommentSubmit}
        fetchItemDetail={fetchItemDetail}
        level={0}
        allComments={comments} // 모든 댓글을 전달하여 대댓글을 찾을 수 있게 함
      />
    ));
  }, [comments, onCommentSubmit, fetchItemDetail]);

  return (
    <div className="space-y-6 bg-white dark:bg-[#121212] p-4 rounded-lg shadow-sm transition-colors duration-300">
      <h3 className="font-semibold text-lg text-[#333333] dark:text-white border-b border-[#E0E0E0] dark:border-[#333333] pb-2">
        댓글 ({comments.length})
      </h3>
      {comments.length > 0 ? (
        <div className="space-y-4">
          {commentItems}
        </div>
      ) : (
        <p className="text-[#666666] dark:text-[#B0B0B0] text-center py-4">
          아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!
        </p>
      )}
    </div>
  );
};

