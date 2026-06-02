"use client";

import {
  Badge,
  Button,
  Group,
  Paper,
  Progress,
  SegmentedControl,
  Skeleton,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { motion, useReducedMotion } from "motion/react";
import { IconRefresh, IconSparkles } from "@tabler/icons-react";

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function ChampionshipPanel({
  count,
  loading,
  error,
  championshipData,
  onCountChange,
  onRefresh,
}) {
  const rows = championshipData?.probabilities?.slice(0, 10) || [];
  const shouldReduceMotion = useReducedMotion();

  return (
    <Paper
      radius={30}
      p={{ base: "xl", md: 34 }}
      style={{
        background:
          "linear-gradient(180deg, rgba(20,33,61,0.97), rgba(35,51,88,0.94))",
        color: "white",
      }}
    >
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start">
          <div>
            <Badge size="lg" radius="sm" color="clay" variant="filled" mb="sm">
              Championship Odds
            </Badge>
            <Title order={3} c="white">
              Title race snapshot
            </Title>
            <Text c="rgba(255,255,255,0.72)" mt={6}>
              Current title picture based on {count} simulation runs.
            </Text>
          </div>
          <ThemeIcon size={48} radius="md" color="clay" variant="white">
            <IconSparkles size={24} />
          </ThemeIcon>
        </Group>

        <Group justify="space-between" align="end" wrap="wrap">
          <Stack gap={6}>
            <Text fz="sm" fw={700} c="rgba(255,255,255,0.88)">
              Simulation count
            </Text>
            <SegmentedControl
              value={count}
              onChange={onCountChange}
              data={[
                { label: "100", value: "100" },
                { label: "200", value: "200" },
                { label: "500", value: "500" },
              ]}
              color="clay"
            />
          </Stack>

          <motion.div
            whileHover={shouldReduceMotion ? undefined : { y: -3, scale: 1.01 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.985 }}
          >
            <Button
              radius="xl"
              color="clay"
              loading={loading}
              onClick={onRefresh}
              leftSection={<IconRefresh size={18} />}
            >
              Refresh Title Odds
            </Button>
          </motion.div>
        </Group>

        {error ? (
          <Text c="red.2" fw={600}>
            {error}
          </Text>
        ) : null}

        <Paper
          radius="lg"
          p="md"
          style={{
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          <Text c="rgba(255,255,255,0.78)" fz="sm">
            Disclaimer: these title probabilities are based primarily on regular-season-driven
            model projections, with eliminated playoff teams removed using the live bracket.
          </Text>
        </Paper>

        {loading && !championshipData ? (
          <Stack gap="md">
            <Skeleton h={56} radius="lg" />
            <Skeleton h={56} radius="lg" />
            <Skeleton h={56} radius="lg" />
          </Stack>
        ) : (
          <Stack gap="md">
            {rows.map((team) => (
              <motion.div
                key={team.team_id}
                whileHover={{ y: -2 }}
                transition={{ duration: 0.18 }}
              >
                <Paper
                  radius="lg"
                  p="md"
                  style={{ background: "rgba(255,255,255,0.06)" }}
                >
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text fw={700} c="white">
                        {team.team_name}
                      </Text>
                      <Text fw={800} c="white">
                        {formatPercent(team.championship_probability)}
                      </Text>
                    </Group>
                    <Progress
                      value={team.championship_probability * 100}
                      color="clay"
                      radius="xl"
                      size="lg"
                    />
                  </Stack>
                </Paper>
              </motion.div>
            ))}
          </Stack>
        )}

        <Text c="rgba(255,255,255,0.72)" fz="sm">
          {championshipData?.methodology ||
            "Title-odds notes will appear here after the first request."}
        </Text>
      </Stack>
    </Paper>
  );
}
