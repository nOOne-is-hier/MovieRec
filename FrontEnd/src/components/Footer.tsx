import { Mail, Phone } from 'lucide-react'

const Footer = () => {
  return (
    <footer className="fixed bottom-0 w-full bg-gray-900/80 backdrop-blur-sm border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-2">
          <div className="flex items-center gap-6 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4" />
              <span>010-1234-5678</span>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              <span>contact@movieapp.com</span>
            </div>
          </div>
          <p className="text-sm text-gray-400">
            &copy; 2024 Movie Recommendation SPA. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer