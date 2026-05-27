import { IBM_Plex_Mono, Manrope } from "next/font/google";
import "@mantine/core/styles.css";
import "./globals.css";

import {
  ColorSchemeScript,
  MantineProvider,
  mantineHtmlProps,
} from "@mantine/core";

import { theme } from "@/theme";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata = {
  title: "CourtVision AI",
  description:
    "NBA game predictions, season simulations, and championship probabilities powered by a FastAPI backend.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      {...mantineHtmlProps}
      className={`${manrope.variable} ${ibmPlexMono.variable}`}
    >
      <head>
        <ColorSchemeScript defaultColorScheme="light" />
      </head>
      <body>
        <MantineProvider theme={theme} defaultColorScheme="light">
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
