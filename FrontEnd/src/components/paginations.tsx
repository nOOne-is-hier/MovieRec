'use client'

import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const [inputValue, setInputValue] = useState(currentPage.toString());

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowLeft' && currentPage > 1) {
      onPageChange(currentPage - 1)
    } else if (e.key === 'ArrowRight' && currentPage < totalPages) {
      onPageChange(currentPage + 1)
    }
  }

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentPage])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  useEffect(() => {
    setInputValue(currentPage.toString());
  }, [currentPage]);

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const value = parseInt(inputValue)
      if (!isNaN(value) && value >= 1 && value <= totalPages) {
        onPageChange(value)
      }
    }
  }

  const renderPageButtons = () => {
    const buttons = []
    let startPage: number
    let endPage: number

    if (totalPages <= 10) {
      startPage = 1
      endPage = totalPages
    } else {
      if (currentPage <= 6) {
        startPage = 1
        endPage = 10
      } else if (currentPage + 4 >= totalPages) {
        startPage = totalPages - 9
        endPage = totalPages
      } else {
        startPage = currentPage - 5
        endPage = currentPage + 4
      }
    }

    if (startPage > 1) {
      buttons.push(
        <Button
          key="1"
          variant={currentPage === 1 ? "default" : "outline"}
          onClick={() => onPageChange(1)}
          className={`w-10 h-10 ${
            currentPage === 1 ? "bg-pink-500 hover:bg-pink-600" : "bg-gray-800 hover:bg-gray-700"
          }`}
        >
          1
        </Button>
      )
      if (startPage > 2) {
        buttons.push(<span key="start-dots" className="px-2 text-gray-400">...</span>)
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      buttons.push(
        <Button
          key={i}
          variant={currentPage === i ? "default" : "outline"}
          onClick={() => onPageChange(i)}
          className={`w-10 h-10 ${
            currentPage === i ? "bg-pink-500 hover:bg-pink-600" : "bg-gray-800 hover:bg-gray-700"
          }`}
        >
          {i}
        </Button>
      )
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        buttons.push(<span key="end-dots" className="px-2 text-gray-400">...</span>)
      }
      buttons.push(
        <Button
          key={totalPages}
          variant={currentPage === totalPages ? "default" : "outline"}
          onClick={() => onPageChange(totalPages)}
          className={`w-10 h-10 ${
            currentPage === totalPages ? "bg-pink-500 hover:bg-pink-600" : "bg-gray-800 hover:bg-gray-700"
          }`}
        >
          {totalPages}
        </Button>
      )
    }

    return buttons
  }

  return (
    <div className="mt-8 flex flex-col items-center gap-4">
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="bg-gray-800 hover:bg-gray-700 w-10 h-10"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <div className="flex items-center gap-2">
          {renderPageButtons()}
        </div>

        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="bg-gray-800 hover:bg-gray-700 w-10 h-10"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center">
        <Input
          type="number"
          min={1}
          max={totalPages}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleInputKeyDown}
          className="w-16 h-10 bg-gray-800 border-gray-700 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
        <span className="text-gray-400 ml-2">/ {totalPages}</span>
      </div>
    </div>
  )
}

