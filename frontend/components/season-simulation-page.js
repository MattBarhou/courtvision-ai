"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { IconTrophy } from "@tabler/icons-react";
import { motion, useReducedMotion } from "motion/react";

import AppShell from "@/components/app-shell";
import PageHero from "@/components/page-hero";
import SeasonOutlookPanel from "@/components/season-outlook-panel";
import { simulateSeason } from "@/lib/api";

const DEFAULT_SIMULATION_COUNT = "200";

export default function SeasonSimulationPage() {
  const [simulationCount, setSimulationCount] = useState(DEFAULT_SIMULATION_COUNT);
  const [seasonData, setSeasonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    loadSeason(DEFAULT_SIMULATION_COUNT);
  }, []);

  async function loadSeason(count) {
    try {
      setError("");
      setLoading(true);
      const result = await simulateSeason(Number(count));
      setSeasonData(result);
    } catch (loadError) {
      setError(loadError.message || "Unable to load season simulation.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHero
        badge="Season Simulation"
        title="Projected Standings"
        description="Explore the current regular-season outlook without crowding the prediction experience. Adjust the simulation count and rerun the table whenever you want."
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
        whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <SeasonOutlookPanel
          count={simulationCount}
          loading={loading}
          error={error}
          seasonData={seasonData}
          onCountChange={setSimulationCount}
          onRefresh={() => loadSeason(simulationCount)}
        />
      </motion.section>
    </AppShell>
  );
}
