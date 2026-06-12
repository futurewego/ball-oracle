export interface Spf {
  home: number;
  draw: number;
  away: number;
}

export interface MatchPrediction {
  date: string;
  group: string;
  matchday: number;
  neutral: boolean;
  home: string;
  away: string;
  home_cn: string;
  away_cn: string;
  lam_home: number;
  lam_away: number;
  spf: Spf;
  total_goals: Record<string, number>;
  top_scores: [string, number][];
  summary: string;
}

export interface Predictions {
  generated_for: string;
  model: string;
  note: string;
  matches: MatchPrediction[];
}
