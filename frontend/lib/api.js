const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = "Request failed.";

    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      detail = response.statusText || detail;
    }

    throw new Error(detail);
  }

  return response.json();
}

export function fetchAppHealth() {
  return request("/health", {
    cache: "no-store",
  });
}

export function fetchPredictionHealth() {
  return request("/api/predictions/health", {
    cache: "no-store",
  });
}

export function predictGame(payload) {
  return request("/api/predictions/game", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function simulateSeason(numSimulations) {
  return request(
    `/api/predictions/season-simulation?num_simulations=${numSimulations}`,
    {
      method: "POST",
    }
  );
}

export function fetchChampionshipProbabilities(numSimulations) {
  return request(
    `/api/predictions/championship-probabilities?num_simulations=${numSimulations}`,
    {
      cache: "no-store",
    }
  );
}
