import React, { useEffect, useState } from "react"
import { motion, useAnimation } from "motion/react"

export const hourGlass = () => {
  const controls = useAnimation()

  // Design Constants
  const strokeColor = "#1B3B59"
  const strokeWidth = 8
  const sandColor = "#1B3B59"

  useEffect(() => {
    let isMounted = true

    const sequence = async () => {
      // Loop infinitely
      while (isMounted) {
        // 1. Reset/Initial State:
        // Top is full, Bottom is empty, Rotation is 0.
        controls.set("reset")

        // 2. Sand Falling Phase
        // Sand drains from top to bottom. Stream appears.
        await controls.start("falling")

        // 3. Pause Phase
        // Wait for a moment with the sand completely in the bottom bulb.
        if (!isMounted) return
        await new Promise((resolve) => setTimeout(resolve, 800))

        // 4. Rotation Phase
        // Rotate the entire hourglass 180 degrees.
        if (!isMounted) return
        await controls.start("rotate")

        // 5. Loop seamlessly
        // The code loops back to step 1 ("reset"), which snaps the rotation back to 0
        // and refills the top bulb instantly. Visually this looks identical to the
        // end of step 4.
        if (!isMounted) return
        await new Promise((resolve) => setTimeout(resolve, 100))
      }
    }

    sequence()

    return () => {
      isMounted = false
    }
  }, [controls])

  // Animation Variants
  const variants = {
    topSand: {
      reset: { height: "50%", y: 0 },
      falling: {
        height: "0%",
        y: 50,
        transition: { duration: 2.5, ease: "easeInOut" },
      },
      rotate: { height: "0%", y: 50 },
    },
    bottomSand: {
      reset: { height: "0%", y: 90 }, // Starts at bottom (y=90) with 0 height
      falling: {
        height: "40%", // Fills up to the neck (height 40, y=50)
        y: 50,
        transition: { duration: 2.5, ease: "easeInOut" },
      },
      rotate: { height: "40%", y: 50 },
    },
    stream: {
      reset: { opacity: 0, height: 0, y: 50 },
      falling: {
        opacity: [0, 1, 1, 0],
        height: [0, 40, 40, 0], // Extends down then shrinks
        transition: { duration: 2.5, times: [0, 0.1, 0.9, 1], ease: "linear" },
      },
      rotate: { opacity: 0 },
    },
    container: {
      reset: { rotate: 0 },
      falling: { rotate: 0 },
      rotate: {
        rotate: 180,
        transition: { duration: 1, ease: "easeInOut" },
      },
    },
  }

  return (
    <div className="flex items-center justify-center p-8">
      <motion.div
        initial="reset"
        animate={controls}
        variants={variants.container}
        className="w-48 h-48 relative"
      >
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full overflow-visible"
        >
          <defs>
            {/* 
               Hourglass Shape Clip Path 
               - Curved bulbs
               - Narrow neck at y=50
            */}
            <clipPath id="hourglassClip">
              <path
                d="M20 10 
                   C20 10, 15 35, 45 48 
                   L47 50 L53 50 
                   L55 48 
                   C85 35, 80 10, 80 10 
                   L20 10 Z
                   
                   M20 90 
                   C20 90, 15 65, 45 52 
                   L47 50 L53 50 
                   L55 52 
                   C85 65, 80 90, 80 90 
                   L20 90 Z"
              />
            </clipPath>
          </defs>

          {/* SAND LAYER - CLIPPED */}
          <g clipPath="url(#hourglassClip)">
            {/* Top Sand */}
            <motion.rect
              width="100"
              fill={sandColor}
              variants={variants.topSand}
              x="0"
            />
            {/* Bottom Sand */}
            <motion.rect
              width="100"
              fill={sandColor}
              variants={variants.bottomSand}
              x="0"
            />
            {/* Falling Stream */}
            <motion.rect
              width="4"
              x="48"
              fill={sandColor}
              variants={variants.stream}
            />
          </g>

          {/* OUTLINE LAYER - ON TOP */}
          {/* Top Bulb Outline */}
          <path
            d="M20 10 C20 10, 15 35, 45 48 L47 50"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M53 50 L55 48 C85 35, 80 10, 80 10"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Top Lid */}
          <path
            d="M20 10 L80 10"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Bottom Bulb Outline */}
          <path
            d="M20 90 C20 90, 15 65, 45 52 L47 50"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M53 50 L55 52 C85 65, 80 90, 80 90"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Bottom Base */}
          <path
            d="M20 90 L80 90"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </motion.div>
    </div>
  )
}
