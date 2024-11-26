import React from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Star } from 'lucide-react';

interface PopularityToggleProps {
  onToggle: (isAscending: boolean) => void;
  className?: string;  // className을 선택적 prop으로 추가
}

const PopularityToggle: React.FC<PopularityToggleProps> = ({ onToggle, className }) => {
  const [isAscending, setIsAscending] = React.useState(false);

  const handleToggle = () => {
    const newIsAscending = !isAscending;
    setIsAscending(newIsAscending);
    onToggle(newIsAscending);
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleToggle}
      className={`flex items-center justify-center rounded-full bg-gray-800 hover:bg-gray-700 px-3 py-2 ${className}`}
      aria-label={`정렬: ${isAscending ? "오름차순" : "내림차순"}`}
    >
      <Star className="h-4 w-4 text-yellow-500 fill-current mr-2" />
      {isAscending ? (
        <ChevronUp className="h-4 w-4 text-gray-300 fill-current" aria-hidden="true" />
      ) : (
        <ChevronDown className="h-4 w-4 text-gray-300 fill-current" aria-hidden="true" />
      )}
    </Button>
  );
};

export default PopularityToggle;

