"use client";

import {
  Badge,
  Group,
  Paper,
  ScrollArea,
  Skeleton,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { IconTournament } from "@tabler/icons-react";

function TeamRow({ competitor }) {
  const isWinner = Boolean(competitor.is_series_winner);

  return (
    <Paper
      radius="md"
      px="sm"
      py={10}
      style={{
        background: isWinner ? "rgba(230, 126, 34, 0.16)" : "rgba(20, 33, 61, 0.04)",
        border: isWinner
          ? "1px solid rgba(230, 126, 34, 0.28)"
          : "1px solid rgba(20, 33, 61, 0.06)",
      }}
    >
      <Group justify="space-between" align="center" gap="sm">
        <Text fw={isWinner ? 800 : 600} c={isWinner ? "clay.8" : "ink.9"}>
          {competitor.seed ? `${competitor.seed}. ` : ""}
          {competitor.team_name}
        </Text>
        {isWinner ? (
          <Badge color="clay" variant="filled" radius="sm">
            Advanced
          </Badge>
        ) : null}
      </Group>
    </Paper>
  );
}

function MatchupCard({ matchup }) {
  return (
    <Paper
      radius="lg"
      p="md"
      style={{ background: "rgba(255,255,255,0.68)" }}
    >
      <Stack gap={8}>
        <Group justify="space-between" align="flex-start">
          <div>
            <Text fw={700}>{matchup.series_title}</Text>
            <Text c="dimmed" fz="sm">
              {matchup.series_summary || matchup.status_detail}
            </Text>
          </div>
          <Badge
            color={matchup.is_complete ? "ink" : "clay"}
            variant={matchup.is_complete ? "light" : "filled"}
            radius="sm"
          >
            {matchup.is_complete ? "Final" : "Live"}
          </Badge>
        </Group>

        <Stack gap="xs">
          <TeamRow competitor={matchup.competitor_one} />
          <TeamRow competitor={matchup.competitor_two} />
        </Stack>

        <Text c="dimmed" fz="sm">
          {matchup.status_detail}
        </Text>
      </Stack>
    </Paper>
  );
}

export default function PlayoffBracketPanel({
  playoffStatus,
  playoffRounds,
  generatedAt,
  loading,
  error,
}) {
  const visibleRounds = (playoffRounds || [])
    .map((round) => ({
      ...round,
      matchups: (round.matchups || []).filter((matchup) => {
        const firstTeam = matchup.competitor_one?.team_name?.trim().toLowerCase();
        const secondTeam = matchup.competitor_two?.team_name?.trim().toLowerCase();
        const seriesTitle = matchup.series_title?.trim().toLowerCase();

        const bothTeamsTbd =
          (!firstTeam || firstTeam === "tbd") &&
          (!secondTeam || secondTeam === "tbd");

        return !bothTeamsTbd && seriesTitle !== "tbd";
      }),
    }))
    .filter((round) => round.round_id > 0 && round.matchups.length > 0);

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
              Actual Playoffs
            </Badge>
            <Title order={3}>Current 2025-26 playoff bracket</Title>
            <Text c="dimmed" mt={6}>
              Live postseason status alongside the model&apos;s title odds.
            </Text>
          </div>
          <ThemeIcon size={48} radius="md" color="clay" variant="light">
            <IconTournament size={24} />
          </ThemeIcon>
        </Group>

        <Badge
          color={playoffStatus === "complete" ? "ink" : "clay"}
          variant={playoffStatus === "complete" ? "light" : "filled"}
          radius="sm"
          w="fit-content"
        >
          {playoffStatus === "complete" ? "Postseason complete" : "Playoffs in progress"}
        </Badge>

        {error ? (
          <Text c="red.7" fw={600}>
            {error}
          </Text>
        ) : null}

        {loading && !visibleRounds.length ? (
          <Stack gap="sm">
            <Skeleton h={28} radius="xl" />
            <Skeleton h={88} radius="xl" />
            <Skeleton h={88} radius="xl" />
            <Skeleton h={88} radius="xl" />
          </Stack>
        ) : (
          <ScrollArea h={720} offsetScrollbars>
            <Stack gap="md">
              {visibleRounds.map((round) => (
                <Stack key={round.round_id} gap="sm">
                  <Text fw={800} fz="lg">
                    {round.round_name}
                  </Text>
                  {round.matchups.map((matchup) => (
                    <MatchupCard key={`${round.round_id}-${matchup.matchup_id}`} matchup={matchup} />
                  ))}
                </Stack>
              ))}
            </Stack>
          </ScrollArea>
        )}

        <Text c="dimmed" fz="sm">
          {generatedAt
            ? `Current snapshot generated from public source data at ${generatedAt}.`
            : "Current playoff status will appear here after the first load."}
        </Text>
      </Stack>
    </Paper>
  );
}
