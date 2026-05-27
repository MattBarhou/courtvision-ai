"use client";

import {
  Badge,
  Button,
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

export default function SeasonOutlookPanel({
  count,
  loading,
  error,
  seasonData,
  onCountChange,
  onRefresh,
}) {
  const rows = seasonData?.projected_standings?.slice(0, 12) || [];
  const shouldReduceMotion = useReducedMotion();

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
              Season Simulation
            </Badge>
            <Title order={3}>Projected regular-season picture</Title>
            <Text c="dimmed" mt={6}>
              Run a fresh simulation and inspect the projected top of the
              table.
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
              Refresh Outlook
            </Button>
          </motion.div>
        </Group>

        {error ? (
          <Text c="red.7" fw={600}>
            {error}
          </Text>
        ) : null}

        <Group grow>
          <SummaryItem
            label="Completed games"
            value={seasonData ? seasonData.completed_games : "--"}
          />
          <SummaryItem
            label="Remaining games"
            value={seasonData ? seasonData.remaining_games : "--"}
          />
        </Group>

        {loading && !seasonData ? (
          <Stack gap="sm">
            <Skeleton h={20} radius="xl" />
            <Skeleton h={20} radius="xl" />
            <Skeleton h={20} radius="xl" />
            <Skeleton h={20} radius="xl" />
          </Stack>
        ) : (
          <ScrollArea h={420} offsetScrollbars>
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
                  <Table.Tr key={team.team_id}>
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
        )}

        <Text c="dimmed" fz="sm">
          {seasonData?.methodology ||
            "Simulation notes will appear here after the first run."}
        </Text>
      </Stack>
    </Paper>
  );
}
