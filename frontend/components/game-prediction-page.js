"use client";

import { useState } from "react";
import Link from "next/link";
import { IconChartHistogram, IconRadar2 } from "@tabler/icons-react";
import { motion, useReducedMotion } from "motion/react";

import AppShell from "@/components/app-shell";
import PageHero from "@/components/page-hero";
import PredictionPanel from "@/components/prediction-panel";
import { predictGame } from "@/lib/api";

const DEFAULT_PREDICTION_FORM = {
  homeTeam: "Boston Celtics",
  awayTeam: "Milwaukee Bucks",
  gameDate: "",
};

export default function GamePredictionPage() {
  const [predictionForm, setPredictionForm] = useState(DEFAULT_PREDICTION_FORM);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState("");
  const shouldReduceMotion = useReducedMotion();

  async function handlePredictionSubmit() {
    if (
      !predictionForm.homeTeam ||
      !predictionForm.awayTeam ||
      predictionForm.homeTeam === predictionForm.awayTeam
    ) {
      setPredictionError("Choose two different teams before submitting.");
      return;
    }

    try {
      setPredictionError("");
      setPredictionLoading(true);
      const payload = {
        home_team: predictionForm.homeTeam,
        away_team: predictionForm.awayTeam,
      };

      if (predictionForm.gameDate) {
        payload.game_date = predictionForm.gameDate;
      }

      const result = await predictGame(payload);
      setPredictionResult(result);
    } catch (error) {
      setPredictionError(error.message || "Prediction request failed.");
    } finally {
      setPredictionLoading(false);
    }
  }

  function handlePredictionChange(field, value) {
    setPredictionForm((current) => ({
      ...current,
      [field]: value || "",
    }));
  }

  function handleSwapTeams() {
    setPredictionForm((current) => ({
      ...current,
      homeTeam: current.awayTeam,
      awayTeam: current.homeTeam,
    }));
  }

  return (
    <AppShell>
      <PageHero
        badge="Single Game Prediction"
        title="CourtVision AI"
        description="Focus on one matchup at a time with a cleaner prediction workflow built entirely around the game winner model."
        actions={[
          {
            href: "#prediction-panel",
            label: "Start Prediction",
            color: "clay",
            icon: <IconRadar2 size={18} />,
          },
          {
            href: "/season-simulation",
            label: "Season Simulation",
            color: "white",
            variant: "subtle",
            icon: <IconChartHistogram size={18} />,
            component: Link,
          },
        ]}
      />

      <motion.section
        id="prediction-panel"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
        animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
        style={{ position: "relative", zIndex: 1 }}
      >
        <PredictionPanel
          form={predictionForm}
          loading={predictionLoading}
          error={predictionError}
          result={predictionResult}
          onSubmit={handlePredictionSubmit}
          onSwapTeams={handleSwapTeams}
          onChange={handlePredictionChange}
        />
      </motion.section>
    </AppShell>
  );
}
