import { Review } from '@/types/community'
import { ReviewItem } from './ReviewItem'
import { motion } from 'framer-motion'
import { FileQuestion } from 'lucide-react'

interface ReviewListProps {
  reviews: Review[];
  onReviewClick: (id: number) => void;
}

export const ReviewList: React.FC<ReviewListProps> = ({ reviews, onReviewClick }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  }

  return (
    <motion.div 
      className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 p-4 bg-[#F9F9F9] dark:bg-[#121212] rounded-lg transition-colors duration-300"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {reviews.length > 0 ? (
        reviews.map((review) => (
          <motion.div key={review.id} variants={itemVariants}>
            <ReviewItem review={review} onClick={() => onReviewClick(review.id)} />
          </motion.div>
        ))
      ) : (
        <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
          <FileQuestion className="w-16 h-16 text-gray-400 dark:text-gray-600 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">아직 리뷰가 없습니다</h3>
          <p className="text-gray-500 dark:text-gray-400">첫 번째 리뷰를 작성해보세요!</p>
        </div>
      )}
    </motion.div>
  )
}

