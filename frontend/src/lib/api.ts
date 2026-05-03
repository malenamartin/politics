const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

export type MentionsItem = {
  date: string;
  entity_name: string;
  mentions: number;
};

export type SentimentItem = {
  date: string;
  entity_name: string;
  avg_sentiment: number;
};

export type ShareItem = {
  entity_name: string;
  mentions: number;
  share_of_voice: number;
};

export type QualityMetadata = {
  sample_size: number;
  minimum_significant_sample?: number;
  adaptive_threshold?: number;
  is_significant: boolean;
  missing_to_significant: number;
  confidence_band?: "very_low" | "low" | "medium" | "high";
};

export type ForecastPoint = {
  date: string;
  entity_name: string;
  predicted_mentions: number;
  predicted_avg_sentiment: number;
  predicted_share_of_voice: number;
};

export type ForecastBaselinePoint = {
  date: string;
  entity_name: string;
  mentions: number;
  avg_sentiment: number;
  share_of_voice: number;
};

export type RecommendationItem = {
  type: "feature" | "content" | "optimization" | "insight" | "ai-action";
  priority: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  actionText: string;
  expectedImpact: "low" | "medium" | "high";
  timeToImplement: string;
  confidence: number;
  evidence?: {
    source_count?: number;
    narrative_count?: number;
    signal_trend?: string;
  };
};

export type QueryRun = {
  id: string;
  query_text: string;
  aliases: string[];
  status: "queued" | "running" | "completed" | "failed";
  horizon_days: number;
  coverage: Record<string, number>;
  quality: QualityMetadata | Record<string, never>;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
};

export type QueryResult = {
  query_run_id: string;
  query_text: string;
  status: string;
  coverage: Record<string, number>;
  quality: QualityMetadata;
  summary: {
    total_mentions: number;
    sources_used: string[];
    top_narratives: Array<{ tag: string; count: number }>;
  };
};

export type SentimentMap = {
  totals: { positive: number; neutral: number; negative: number };
  distribution: { positive: number; neutral: number; negative: number };
  by_source: Record<
    string,
    { positive: number; neutral: number; negative: number; total: number }
  >;
  narrative_intensity: Array<{
    tag: string;
    volume: number;
    avg_sentiment: number;
    momentum: number;
  }>;
};

type ApiListResponse<T> = {
  items: T[];
  quality?: QualityMetadata;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`);
  }
  return response.json();
}

async function getJsonWithHeaders<T>(
  path: string,
  headers?: Record<string, string>
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers,
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`);
  }
  return response.json();
}

function buildEntitiesQuery(entities: string[]): string {
  if (!entities.length) {
    return "";
  }
  return `&entities=${encodeURIComponent(entities.join(","))}`;
}

export async function fetchAiMentions(days: number, entities: string[]) {
  return getJson<ApiListResponse<MentionsItem>>(
    `/api/stats/ai-mentions?days=${days}${buildEntitiesQuery(entities)}`
  );
}

export async function fetchAiSentiment(days: number, entities: string[]) {
  return getJson<ApiListResponse<SentimentItem>>(
    `/api/stats/ai-sentiment?days=${days}${buildEntitiesQuery(entities)}`
  );
}

export async function fetchShareOfVoice(days: number, entities: string[]) {
  return getJson<ApiListResponse<ShareItem>>(
    `/api/stats/share-of-voice?days=${days}${buildEntitiesQuery(entities)}`
  );
}

export async function fetchForecast(
  entity: string,
  horizon: number,
  proKey?: string
): Promise<{
  entity_name: string;
  horizon_days: number;
  baseline: ForecastBaselinePoint[];
  forecast: ForecastPoint[];
  metrics: { mae: number | null; mape: number | null; confidence: number };
  quality: QualityMetadata;
}> {
  const encodedEntity = encodeURIComponent(entity);
  return getJsonWithHeaders(`/api/pro/forecast?entity=${encodedEntity}&horizon=${horizon}`, {
    ...(proKey ? { "x-pro-key": proKey } : {}),
  });
}

export async function fetchRecommendations(
  entity: string,
  horizon: number,
  proKey?: string
): Promise<{
  entity_name: string;
  horizon_days: number;
  recommendations: RecommendationItem[];
  signals: {
    sample_size: number;
    avg_sentiment: number;
    top_narratives: Array<{ tag: string; count: number }>;
    forecast_confidence: number;
  };
  quality: QualityMetadata;
}> {
  const encodedEntity = encodeURIComponent(entity);
  return getJsonWithHeaders(
    `/api/pro/recommendations?entity=${encodedEntity}&horizon=${horizon}`,
    {
      ...(proKey ? { "x-pro-key": proKey } : {}),
    }
  );
}

export async function createQueryRun(queryText: string, horizon: number) {
  const response = await fetch(`${API_BASE_URL}/api/query-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query_text: queryText, horizon }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create query run: ${response.status}`);
  }
  return response.json() as Promise<{ query_run: QueryRun }>;
}

export async function fetchQueryRun(runId: string) {
  return getJson<{ query_run: QueryRun }>(`/api/query-runs/${encodeURIComponent(runId)}`);
}

export async function fetchQueryRunResults(runId: string) {
  return getJson<{
    query_run: QueryRun;
    result: QueryResult;
    sentiment_map: SentimentMap;
    forecast: {
      query_run_id: string;
      horizon_days: number;
      baseline: ForecastBaselinePoint[];
      forecast: ForecastPoint[];
      model_version: string;
      metrics: { mae: number | null; mape: number | null; confidence: number };
      scenario_forecast?: {
        base: ForecastPoint[];
        bull: ForecastPoint[];
        bear: ForecastPoint[];
      };
      narrative_shift_risk?: "low" | "medium" | "high";
    };
    recommendations: {
      query_run_id: string;
      horizon_days: number;
      recommendations: RecommendationItem[];
      signals: {
        sample_size: number;
        avg_sentiment: number;
        coverage_by_source: Record<string, number>;
        top_narratives: Array<{ tag: string; count: number }>;
        forecast_confidence: number;
      };
    };
  }>(`/api/query-runs/${encodeURIComponent(runId)}/results`);
}
