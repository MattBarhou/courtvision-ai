"use client";

import {
  Badge,
  Button,
  Grid,
  Group,
  Paper,
  ScrollArea,
  SegmentedControl,
  Skeleton,
  Stack,
  Table,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { motion, useReducedMotion } from "motion/react";
import { IconRefresh, IconTrophy } from "@tabler/icons-react";

function SummaryItem({ label, value }) {
  return (
    <Paper
      radius="lg"
      p="md"
      style={{ background: "rgba(255,255,255,0.62)" }}
    >
      <Text fz="xs" tt="uppercase" fw={700} c="dimmed">
        {label}
      </Text>
      <Text fw={800} fz="xl" mt={6}>
        {value}
      </Text>
    </Paper>
  );
}

function PredictedStandingsTable({ rows }) {
  return (
    <ScrollArea h={520} offsetScrollbars>
      <Table highlightOnHover verticalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Rank</Table.Th>
            <Table.Th>Team</Table.Th>
            <Table.Th ta="right">W</Table.Th>
            <Table.Th ta="right">L</Table.Th>
            <Table.Th ta="right">Win %</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((team) => (
            <Table.Tr key={`predicted-${team.team_id}`}>
              <Table.Td fw={700}>{team.rank}</Table.Td>
              <Table.Td>{team.team_name}</Table.Td>
              <Table.Td ta="right">{team.wins}</Table.Td>
              <Table.Td ta="right">{team.losses}</Table.Td>
              <Table.Td ta="right">{team.win_pct}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </ScrollArea>
  );
}

function ActualStandingsTable({ rows }) {
  return (
    <ScrollArea h={520} offsetScrollbars>
      <Table highlightOnHover verticalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Rank</Table.Th>
            <Table.Th>Team</Table.Th>
            <Table.Th ta="right">W</Table.Th>
            <Table.Th ta="right">L</Table.Th>
            <Table.Th ta="right">Seed</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((team) => (
            <Table.Tr key={`actual-${team.team_name}`}>
              <Table.Td fw={700}>{team.rank}</Table.Td>
              <Table.Td>{team.team_name}</Table.Td>
              <Table.Td ta="right">{team.wins}</Table.Td>
              <Table.Td ta="right">{team.losses}</Table.Td>
              <Table.Td ta="right">{team.playoff_seed ?? "-"}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </ScrollArea>
  );
}

export default function SeasonOutlookPanel({
  count,
  loading,
  error,
  seasonResults,
  onCountChange,
  onRefresh,
}) {
  const shouldReduceMotion = useReducedMotion();
  const predictedRows = seasonResults?.predicted_standings || [];
  const actualRows = seasonResults?.actual_regular_season_standings || [];
  const summary = seasonResults?.accuracy_summary;

  return (
    <Paper
      radius={30}
      p={{ base: "xl", md: 34 }}
      style={{ background: "rgba(255,255,255,0.74)" }}
    >
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start">
          <div>
            <Badge size="lg" radius="sm" color="ink" variant="light" mb="sm">
              Season Comparison
            </Badge>
            <Title order={3}>Predicted vs. actual regular-season standings</Title>
            <Text c="dimmed" mt={6}>
              Compare the model&apos;s projected table with the actual 2025-26
              regular-season finish.
            </Text>
          </div>
          <ThemeIcon size={48} radius="md" color="clay" variant="light">
            <IconTrophy size={24} />
          </ThemeIcon>
        </Group>

        <Group justify="space-between" align="end" wrap="wrap">
          <Stack gap={6}>
            <Text fz="sm" fw={700}>
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
            />
          </Stack>

          <motion.div
            whileHover={shouldReduceMotion ? undefined : { y: -3, scale: 1.01 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.985 }}
          >
            <Button
              radius="xl"
              color="ink"
              loading={loading}
              onClick={onRefresh}
              leftSection={<IconRefresh size={18} />}
            >
              Refresh Comparison
            </Button>
          </motion.div>
        </Group>

        {error ? (
          <Text c="red.7" fw={600}>
            {error}
          </Text>
        ) : null}

        <Grid>
          <Grid.Col span={{ base: 6, md: 3 }}>
            <SummaryItem
              label="Exact matches"
              value={summary ? summary.exact_rank_matches : "--"}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 6, md: 3 }}>
            <SummaryItem
              label="Within 3 spots"
              value={summary ? summary.within_three_slots : "--"}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 6, md: 3 }}>
            <SummaryItem
              label="Top 8 overlap"
              value={summary ? summary.top_eight_overlap : "--"}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 6, md: 3 }}>
            <SummaryItem
              label="Avg rank error"
              value={summary ? summary.mean_absolute_rank_error : "--"}
            />
          </Grid.Col>
        </Grid>

        {loading && !seasonResults ? (
          <Stack gap="sm">
            <Skeleton h={20} radius="xl" />
            <Skeleton h={20} radius="xl" />
            <Skeleton h={20} radius="xl" />
            <Skeleton h={20} radius="xl" />
          </Stack>
        ) : (
          <Grid gutter="xl" align="start">
            <Grid.Col span={{ base: 12, xl: 6 }}>
              <Stack gap="sm">
                <Text fw={700}>Predicted standings</Text>
                <PredictedStandingsTable rows={predictedRows} />
              </Stack>
            </Grid.Col>
            <Grid.Col span={{ base: 12, xl: 6 }}>
              <Stack gap="sm">
                <Text fw={700}>Actual regular-season standings</Text>
                <ActualStandingsTable rows={actualRows} />
              </Stack>
            </Grid.Col>
          </Grid>
        )}

        <Text c="dimmed" fz="sm">
          {seasonResults?.methodology ||
            "The model-vs-actual season comparison will appear here after the first load."}
        </Text>
      </Stack>
    </Paper>
  );
}
