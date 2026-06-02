"use client";

import {
  ActionIcon,
  Badge,
  Button,
  Grid,
  Group,
  Paper,
  Progress,
  Select,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { motion, useReducedMotion } from "motion/react";
import {
  IconArrowsExchange,
  IconArrowUpRight,
  IconBolt,
  IconTargetArrow,
} from "@tabler/icons-react";

import { NBA_TEAMS } from "@/lib/teams";

const teamOptions = NBA_TEAMS.map((team) => ({ value: team, label: team }));

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function PredictionPanel({
  form,
  loading,
  error,
  result,
  onSubmit,
  onSwapTeams,
  onChange,
}) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <Paper
      radius={30}
      p={{ base: "xl", md: 34 }}
      style={{
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.94), rgba(251,247,240,0.86))",
        border: "1px solid rgba(20, 33, 61, 0.08)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        position: "relative",
        zIndex: 1,
      }}
    >
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start">
          <div>
            <Badge
              size="lg"
              radius="sm"
              color="clay"
              variant="light"
              mb="sm"
            >
              Single Game Prediction
            </Badge>
            <Title order={2} c="ink.9">
              Predict the next matchup
            </Title>
            <Text c="dimmed" mt={6}>
              Choose both teams, add an optional date, and compare each
              side&apos;s win probability.
            </Text>
          </div>
          <ThemeIcon size={48} radius="md" color="ink" variant="light">
            <IconTargetArrow size={24} />
          </ThemeIcon>
        </Group>

        <Grid align="end">
          <Grid.Col span={{ base: 12, md: 5 }}>
            <Select
              label="Home team"
              placeholder="Choose home team"
              data={teamOptions}
              value={form.homeTeam}
              onChange={(value) => onChange("homeTeam", value)}
              searchable
              nothingFoundMessage="No team found"
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 2 }}>
            <Group justify="center">
              <motion.div
                whileHover={shouldReduceMotion ? undefined : { rotate: 12, y: -2 }}
                whileTap={shouldReduceMotion ? undefined : { scale: 0.94 }}
              >
                <ActionIcon
                  aria-label="Swap teams"
                  variant="light"
                  color="ink"
                  size={42}
                  radius="xl"
                  onClick={onSwapTeams}
                  mt={{ base: 0, md: 24 }}
                >
                  <IconArrowsExchange size={20} />
                </ActionIcon>
              </motion.div>
            </Group>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 5 }}>
            <Select
              label="Away team"
              placeholder="Choose away team"
              data={teamOptions}
              value={form.awayTeam}
              onChange={(value) => onChange("awayTeam", value)}
              searchable
              nothingFoundMessage="No team found"
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 5 }}>
            <TextInput
              label="Game date"
              type="date"
              value={form.gameDate}
              onChange={(event) => onChange("gameDate", event.target.value)}
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 7 }}>
            <motion.div
              whileHover={shouldReduceMotion ? undefined : { y: -3, scale: 1.01 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.985 }}
            >
              <Button
                fullWidth
                size="md"
                radius="xl"
                color="clay"
                loading={loading}
                onClick={onSubmit}
                leftSection={<IconArrowUpRight size={18} />}
                mt={{ base: 0, md: 24 }}
              >
                Generate Prediction
              </Button>
            </motion.div>
          </Grid.Col>
        </Grid>

        {error ? (
          <Text c="red.7" fw={600}>
            {error}
          </Text>
        ) : null}

        <Paper
          radius={24}
          p="lg"
          style={{
            background: "rgba(255,255,255,0.82)",
            border: "1px solid rgba(20, 33, 61, 0.06)",
          }}
        >
          {result ? (
            <Stack gap="md">
              <Group justify="space-between" align="center">
                <div>
                  <Text fz="sm" tt="uppercase" fw={700} c="dimmed">
                    Projected winner
                  </Text>
                  <Title order={3} mt={4}>
                    {result.predicted_winner}
                  </Title>
                </div>
                <Badge
                  color="clay"
                  size="xl"
                  variant="filled"
                  radius="sm"
                  leftSection={<IconBolt size={14} />}
                >
                  {formatPercent(result.confidence_score)} confidence
                </Badge>
              </Group>

              <Stack gap="xs">
                <Group justify="space-between">
                  <Text fw={600}>{result.home_team}</Text>
                  <Text fw={700}>{formatPercent(result.home_win_probability)}</Text>
                </Group>
                <Progress
                  value={result.home_win_probability * 100}
                  color="clay"
                  radius="xl"
                  size="lg"
                />
              </Stack>

              <Stack gap="xs">
                <Group justify="space-between">
                  <Text fw={600}>{result.away_team}</Text>
                  <Text fw={700}>{formatPercent(result.away_win_probability)}</Text>
                </Group>
                <Progress
                  value={result.away_win_probability * 100}
                  color="ink"
                  radius="xl"
                  size="lg"
                />
              </Stack>
            </Stack>
          ) : (
            <Stack gap="xs">
              <Text fw={600}>No prediction yet</Text>
              <Text c="dimmed" fz="sm">
                Choose two teams and submit the form to see a probability-based
                winner projection.
              </Text>
            </Stack>
          )}
        </Paper>
      </Stack>
    </Paper>
  );
}
