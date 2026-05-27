"use client";

import Image from "next/image";
import { Box } from "@mantine/core";
import { motion, useReducedMotion } from "motion/react";

const BASKETBALLS = [
  { id: 1, size: 92, left: "6%", top: "12%", duration: 12, delay: 0, driftX: 8, driftY: 18, rotate: -5 },
  { id: 2, size: 78, left: "18%", top: "58%", duration: 14, delay: 1.4, driftX: -7, driftY: 16, rotate: 6 },
  { id: 3, size: 110, left: "29%", top: "22%", duration: 13.5, delay: 0.6, driftX: 10, driftY: 20, rotate: -7 },
  { id: 4, size: 70, left: "41%", top: "70%", duration: 11.5, delay: 1.1, driftX: -8, driftY: 17, rotate: 8 },
  { id: 5, size: 96, left: "54%", top: "18%", duration: 15, delay: 0.2, driftX: 9, driftY: 19, rotate: -6 },
  { id: 6, size: 82, left: "67%", top: "48%", duration: 12.5, delay: 1.8, driftX: -6, driftY: 18, rotate: 5 },
  { id: 7, size: 118, left: "79%", top: "16%", duration: 16, delay: 0.9, driftX: 11, driftY: 21, rotate: -8 },
  { id: 8, size: 74, left: "88%", top: "62%", duration: 13, delay: 0.4, driftX: -7, driftY: 16, rotate: 7 },
  { id: 9, size: 64, left: "11%", top: "84%", duration: 10.5, delay: 1.2, driftX: 6, driftY: 15, rotate: -5 },
  { id: 10, size: 88, left: "72%", top: "82%", duration: 14.2, delay: 0.7, driftX: -9, driftY: 18, rotate: 6 },
];

export default function BackgroundLayer() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <Box
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      <Box
        style={{
          position: "absolute",
          inset: 0,
          background: `
            radial-gradient(circle at 12% 14%, rgba(230, 126, 34, 0.2), transparent 24%),
            radial-gradient(circle at 84% 10%, rgba(63, 143, 139, 0.14), transparent 28%),
            radial-gradient(circle at 50% 88%, rgba(230, 126, 34, 0.1), transparent 32%),
            linear-gradient(180deg, #fffdf8 0%, #f8f0e4 48%, #f4eadb 100%)
          `,
        }}
      />

      <Box
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(20, 33, 61, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(20, 33, 61, 0.035) 1px, transparent 1px)",
          backgroundSize: "88px 88px",
          maskImage: "linear-gradient(180deg, rgba(0,0,0,0.5), transparent 88%)",
        }}
      />

      {BASKETBALLS.map((ball) => (
        <motion.div
          key={ball.id}
          initial={false}
          animate={
            shouldReduceMotion
              ? { x: 0, y: 0, rotate: 0, opacity: 0.09 }
              : {
                x: [-ball.driftX, ball.driftX, -ball.driftX],
                y: [-ball.driftY, ball.driftY, -ball.driftY],
                rotate: [-ball.rotate, ball.rotate, -ball.rotate],
                opacity: [0.085, 0.13, 0.085],
              }
          }
          transition={{
            duration: ball.duration,
            delay: ball.delay,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
          style={{
            position: "absolute",
            left: ball.left,
            top: ball.top,
            width: ball.size,
            height: ball.size,
            filter: "saturate(0.92) brightness(1.01)",
          }}
          className="cv-basketball"
        >
          <Image
            src="/basketball-sport-team-svgrepo-com.svg"
            loading="eager"
            alt=""
            fill
            sizes={`${ball.size}px`}
            style={{
              objectFit: "contain",
            }}
          />
        </motion.div>
      ))}
    </Box>
  );
}
