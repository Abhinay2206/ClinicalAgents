import * as React from "react"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

const Button = React.forwardRef(({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
  const Comp = asChild ? motion.slot : motion.button

  const variants = {
    default: "bg-gradient-to-r from-[#00ADB5] to-[#00C6FF] text-white shadow-lg border border-transparent",
    ghost: "border border-[var(--border-subtle)] bg-transparent hover:bg-[var(--bg-secondary)] text-[var(--text-primary)]",
    outline: "border-2 border-[#00ADB5] bg-transparent text-[#00ADB5]",
    glass: "bg-white/5 backdrop-blur-md border border-white/10 text-white hover:bg-white/10 shadow-[var(--shadow-soft)]",
  }

  const sizes = {
    default: "px-6 py-3 text-sm",
    sm: "px-4 py-2 text-xs",
    lg: "px-8 py-4 text-base",
    icon: "h-10 w-10 p-2",
  }

  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      ref={ref}
      whileHover={{ scale: 1.02, boxShadow: "0 0 20px rgba(0, 173, 181, 0.3)" }}
      whileTap={{ scale: 0.98 }}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
