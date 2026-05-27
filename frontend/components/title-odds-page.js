"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { IconChartHistogram } from "@tabler/icons-react";
import { motion, useReducedMotion } from "motion/react";

import AppShell from "@/components/app-shell";
import ChampionshipPanel from "@/components/championship-panel";
import PageHero from "@/components/page-hero";
import { fetchChampionshipProbabilities } from "@/lib/api";

const DEFAULT_SIMULATION_COUNT = "200";

export default function TitleOddsPage() {
  const [simulationCount, setSimulationCount] = useState(DEFAULT_SIMULATION_COUNT);
  const [championshipData, setChampionshipData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    loadTitleOdds(DEFAULT_SIMULATION_COUNT);
  }, []);

  async function loadTitleOdds(count) {
    try {
      setError("");
      setLoading(true);
      const result = await fetchChampionshipProbabilities(Number(count));
      setChampionshipData(result);
    } catch (loadError) {
      setError(loadError.message || "Unable to load title odds.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHero
        badge="Title Odds"
        title="Championship Picture"
        description="Keep the title race on its own page so the probability table has room to breathe and stays easy to scan."
        actions={[
          {
            href: "/season-simulation",
            label: "Open Season Simulation",
            color: "clay",
            icon: <IconChartHistogram size={18} />,
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
        <ChampionshipPanel
          count={simulationCount}
          loading={loading}
          error={error}
          championshipData={championshipData}
          onCountChange={setSimulationCount}
          onRefresh={() => loadTitleOdds(simulationCount)}
        />
      </motion.section>
    </AppShell>
  );
}
