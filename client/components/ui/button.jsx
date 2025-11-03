import * as React from "react"
import { cn } from "@/lib/utils"

const Button = React.forwardRef(({ className, variant = "default", size = "default", ...props }, ref) => {
  const variants = {
    default: "bg-gradient-to-r from-[#00ADB5] to-[#00C6FF] text-white hover:opacity-90 shadow-lg hover:shadow-xl",
    ghost: "border border-[var(--border-subtle)] bg-transparent hover:bg-[var(--bg-secondary)] text-[var(--text-primary)]",
    outline: "border-2 border-[#00ADB5] bg-transparent text-[#00ADB5] hover:bg-[#00ADB5] hover:text-white",
  }

  const sizes = {
    default: "px-6 py-3 text-sm",
    sm: "px-4 py-2 text-xs",
    lg: "px-8 py-4 text-base",
  }

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
