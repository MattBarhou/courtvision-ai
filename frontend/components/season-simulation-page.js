"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { IconTrophy } from "@tabler/icons-react";
import { motion, useReducedMotion } from "motion/react";

import AppShell from "@/components/app-shell";
import PageHero from "@/components/page-hero";
import SeasonOutlookPanel from "@/components/season-outlook-panel";
import { fetchSeasonResults } from "@/lib/api";

const DEFAULT_SIMULATION_COUNT = "200";

export default function SeasonSimulationPage() {
  const [simulationCount, setSimulationCount] = useState(DEFAULT_SIMULATION_COUNT);
  const [seasonResults, setSeasonResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    loadSeasonResults(DEFAULT_SIMULATION_COUNT);
  }, []);

  async function loadSeasonResults(count) {
    try {
      setError("");
      setLoading(true);
      const result = await fetchSeasonResults(Number(count));
      setSeasonResults(result);
    } catch (loadError) {
      setError(loadError.message || "Unable to load season comparison.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHero
        badge="Season Simulation"
        title="Projected Standings vs. Reality"
        description="See how the model&apos;s projected table compares to the actual 2025-26 regular-season finish, then use the same season context to follow the current playoff picture."
        actions={[
          {
            href: "/title-odds",
            label: "View Title Odds",
            color: "clay",
            icon: <IconTrophy size={18} />,
            component: Link,
          },
        ]}
      />

      <motion.section
        initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
        animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
        style={{ position: "relative", zIndex: 1 }}
      >
        <SeasonOutlookPanel
          count={simulationCount}
          loading={loading}
          error={error}
          seasonResults={seasonResults}
          onCountChange={setSimulationCount}
          onRefresh={() => loadSeasonResults(simulationCount)}
        />
      </motion.section>
    </AppShell>
  );
}
