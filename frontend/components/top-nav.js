"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Group, Paper } from "@mantine/core";
import { motion, useReducedMotion } from "motion/react";

const navItems = [
  { href: "/", label: "Game Prediction" },
  { href: "/season-simulation", label: "Season Simulation" },
  { href: "/title-odds", label: "Title Odds" },
];

export default function TopNav() {
  const pathname = usePathname();
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      style={{
        position: "sticky",
        top: 18,
        zIndex: 20,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <motion.div
        initial={shouldReduceMotion ? false : { opacity: 0, y: -18 }}
        animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: "easeOut" }}
      >
        <Paper
          radius="xl"
          px={{ base: "xs", md: "sm" }}
          py="xs"
          style={{
            background: "rgba(255, 253, 248, 0.78)",
            backdropFilter: "blur(14px)",
          }}
        >
          <Group gap={6} wrap="nowrap">
            {navItems.map((item) => {
              const isActive = pathname === item.href;

              return (
                <motion.div
                  key={item.href}
                  whileHover={shouldReduceMotion ? undefined : { y: -2 }}
                  whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
                  transition={{ duration: 0.18 }}
                >
                  <Link
                    href={item.href}
                    style={{
                      display: "block",
                      padding: "10px 16px",
                      borderRadius: 999,
                      color: isActive ? "#fffdf8" : "#14213d",
                      background: isActive ? "#14213d" : "transparent",
                      fontWeight: 700,
                      fontSize: 14,
                      letterSpacing: "-0.02em",
                      textDecoration: "none",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.label}
                  </Link>
                </motion.div>
              );
            })}
          </Group>
        </Paper>
      </motion.div>
    </div>
  );
}
