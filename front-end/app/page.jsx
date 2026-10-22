"use client";
import React, { useState } from 'react';
import { cva } from "class-variance-authority";
import * as LabelPrimitive from "@radix-ui/react-label";
import ModelPlayground from "./interface";

export default function Page() {
  const [loading, setLoading] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  return <ModelPlayground />
}


const Card = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={className}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={className}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={className}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={className}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"


const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div 
  ref={ref} 
  className={className} 
  {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={className}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }




const buttonVariants = cva(
  "button",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-purple-600 to-indigo-600 text-primary-foreground shadow-md hover:from-purple-700 hover:to-indigo-700",
        destructive:
          "bg-gradient-to-r from-red-600 to-pink-600 text-destructive-foreground shadow-md hover:from-red-700 hover:to-pink-700",
        outline:
          "border border-input bg-transparent shadow-sm hover:border-accent hover:text-accent-foreground",
        secondary:
          "bg-gradient-to-r from-blue-600 to-cyan-600 text-secondary-foreground shadow-md hover:from-blue-700 hover:to-cyan-700",
        ghost: "hover:bg-accent/20 hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)



const Button = React.forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={buttonVariants({ variant, size, className })}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"



const Label = React.forwardRef(({ className, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={className}
    {...props}
  />
))
// Label.displayName = LabelPrimitive.Root.displayName