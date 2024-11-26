"use client"

import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

const RangeSlider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex w-full touch-none select-none items-center",
      className
    )}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-1 w-full grow overflow-hidden rounded-full bg-gray-800/60">
      <SliderPrimitive.Range className="absolute h-full bg-purple-500/40 backdrop-blur-sm" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-3 w-3 rounded border border-purple-500 bg-purple-500 backdrop-blur-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-purple-500/80 focus-visible:ring-offset-1 disabled:pointer-events-none disabled:opacity-50" />
    <SliderPrimitive.Thumb className="block h-3 w-3 rounded border border-purple-500 bg-purple-500 backdrop-blur-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-purple-500/80 focus-visible:ring-offset-1 disabled:pointer-events-none disabled:opacity-50" />
  </SliderPrimitive.Root>
))
RangeSlider.displayName = SliderPrimitive.Root.displayName

export { RangeSlider }

