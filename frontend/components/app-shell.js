"use client";

import { Box, Container, Stack } from "@mantine/core";

import BackgroundLayer from "@/components/background-layer";
import TopNav from "@/components/top-nav";

export default function AppShell({ children }) {
  return (
    <Box py={{ base: 18, md: 28 }} style={{ position: "relative", zIndex: 1 }}>
      <BackgroundLayer />
      <Container size={1280}>
        <Stack gap="xl">
          <TopNav />
          {children}
        </Stack>
      </Container>
    </Box>
  );
}
