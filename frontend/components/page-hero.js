"use client";

import { Badge, Box, Button, Group, Paper, Stack, Text, Title } from "@mantine/core";
import { motion, useReducedMotion } from "motion/react";

export default function PageHero({
  badge,
  title,
  description,
  actions = [],
}) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.section
      initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
      animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
    >
      <Paper
        radius={32}
        p={{ base: "xl", md: 40 }}
        style={{
          background:
            "linear-gradient(145deg, rgba(18,32,58,0.98), rgba(43,60,94,0.96))",
          color: "white",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <Box
          style={{
            position: "absolute",
            inset: "auto -4% -18% auto",
            width: 320,
            height: 320,
            borderRadius: "50%",
            background: "rgba(230,126,34,0.15)",
            filter: "blur(18px)",
          }}
        />
        <Stack gap="lg" style={{ position: "relative", zIndex: 1 }}>
          <Badge
            size="lg"
            radius="sm"
            color="clay"
            variant="filled"
            w="fit-content"
          >
            {badge}
          </Badge>

          <div>
            <Title order={1} fz={{ base: 36, md: 60 }} lh={1}>
              {title}
            </Title>
            <Text
              mt="md"
              maw={760}
              c="rgba(255,255,255,0.76)"
              fz={{ base: "md", md: "lg" }}
            >
              {description}
            </Text>
          </div>

          {actions.length ? (
            <Group gap="md" wrap="wrap">
              {actions.map((action) => (
                <motion.div
                  key={action.label}
                  whileHover={shouldReduceMotion ? undefined : { y: -3, scale: 1.01 }}
                  whileTap={shouldReduceMotion ? undefined : { scale: 0.985 }}
                >
                  <Button
                    component={action.component || "a"}
                    href={action.href}
                    size="md"
                    radius="xl"
                    color={action.color || "clay"}
                    variant={action.variant}
                    leftSection={action.icon}
                  >
                    {action.label}
                  </Button>
                </motion.div>
              ))}
            </Group>
          ) : null}
        </Stack>
      </Paper>
    </motion.section>
  );
}
