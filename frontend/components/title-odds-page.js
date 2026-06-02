"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Grid } from "@mantine/core";
import { IconChartHistogram } from "@tabler/icons-react";
import { motion, useReducedMotion } from "motion/react";

import AppShell from "@/components/app-shell";
import ChampionshipPanel from "@/components/championship-panel";
import PageHero from "@/components/page-hero";
import PlayoffBracketPanel from "@/components/playoff-bracket-panel";
import {
  fetchChampionshipProbabilities,
  fetchSeasonResults,
} from "@/lib/api";

const DEFAULT_SIMULATION_COUNT = "200";

export default function TitleOddsPage() {
  const [simulationCount, setSimulationCount] = useState(DEFAULT_SIMULATION_COUNT);
  const [championshipData, setChampionshipData] = useState(null);
  const [seasonResults, setSeasonResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    loadTitleOddsPage(DEFAULT_SIMULATION_COUNT);
  }, []);

  async function loadTitleOddsPage(count) {
    try {
      setError("");
      setLoading(true);
      const numericCount = Number(count);
      const [odds, results] = await Promise.all([
        fetchChampionshipProbabilities(numericCount),
        fetchSeasonResults(numericCount),
      ]);
      setChampionshipData(odds);
      setSeasonResults(results);
    } catch (loadError) {
      setError(loadError.message || "Unable to load title odds and playoff data.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHero
        badge="Title Odds"
        title="Championship Picture"
        description="This page shows the probability of each team winning the NBA title, based on the model's predictions and the current playoff bracket."
        actions={[
          {
            href: "/season-simulation",
            label: "Open Season Comparison",
            color: "clay",
            icon: <IconChartHistogram size={18} />,
            component: Link,
          },
        ]}
      />

      <Grid gutter={{ base: "xl", md: 28 }} align="start">
        <Grid.Col span={{ base: 12, xl: 5 }}>
          <motion.section
            initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
            animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
            style={{ position: "relative", zIndex: 1 }}
          >
            <ChampionshipPanel
              count={simulationCount}
              loading={loading}
              error={error}
              championshipData={championshipData}
              onCountChange={setSimulationCount}
              onRefresh={() => loadTitleOddsPage(simulationCount)}
            />
          </motion.section>
        </Grid.Col>

        <Grid.Col span={{ base: 12, xl: 7 }}>
          <motion.section
            initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
            animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
            style={{ position: "relative", zIndex: 1 }}
          >
            <PlayoffBracketPanel
              playoffStatus={seasonResults?.playoff_status}
              playoffRounds={seasonResults?.current_playoff_bracket || []}
              generatedAt={seasonResults?.generated_at}
              loading={loading}
              error={error}
            />
          </motion.section>
        </Grid.Col>
      </Grid>
    </AppShell>
  );
}
