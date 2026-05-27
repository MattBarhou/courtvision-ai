import { createTheme } from "@mantine/core";

export const theme = createTheme({
  primaryColor: "clay",
  defaultRadius: "lg",
  fontFamily: "var(--font-manrope), sans-serif",
  fontFamilyMonospace: "var(--font-ibm-plex-mono), monospace",
  headings: {
    fontFamily: "var(--font-manrope), sans-serif",
    fontWeight: "700",
  },
  colors: {
    clay: [
      "#fff3e6",
      "#fce0c3",
      "#f7c294",
      "#f1a35f",
      "#ec8c38",
      "#e67e22",
      "#cf6b16",
      "#b65a0f",
      "#93480a",
      "#733707",
    ],
    ink: [
      "#eef2fb",
      "#d5def0",
      "#aebede",
      "#869fcd",
      "#6484bf",
      "#4f73b6",
      "#4367b2",
      "#355897",
      "#2c4e87",
      "#1f365f",
    ],
    sand: [
      "#fffaf1",
      "#f8f0e2",
      "#efe2c5",
      "#e7d2a6",
      "#dfc48c",
      "#dabb7b",
      "#d4b56f",
      "#b89d5c",
      "#a38b4e",
      "#8d7540",
    ],
  },
  shadows: {
    md: "0 16px 40px rgba(20, 33, 61, 0.08)",
    xl: "0 28px 70px rgba(20, 33, 61, 0.12)",
  },
});
