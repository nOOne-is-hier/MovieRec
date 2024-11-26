import { Post } from '@/types/community'
import { PostItem } from './PostItem'
import { motion } from 'framer-motion'

interface PostListProps {
  posts: Post[];
  onPostClick: (id: number) => void;
}

export const PostList: React.FC<PostListProps> = ({ posts, onPostClick }) => {
  return (
    <motion.div 
      className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 p-4 bg-[#F9F9F9] dark:bg-[#121212] rounded-lg transition-colors duration-300"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {posts.length > 0 ? (
        posts.map((post, index) => (
          <motion.div
            key={post.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <PostItem post={post} onClick={() => onPostClick(post.id)} />
          </motion.div>
        ))
      ) : (
        <div className="col-span-full text-center py-8 text-[#666666] dark:text-[#B0B0B0]">
          게시물이 없습니다.
        </div>
      )}
    </motion.div>
  )
}

