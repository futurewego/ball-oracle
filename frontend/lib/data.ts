import type { Predictions, MatchPrediction } from "./types";
import raw from "@/data/predictions.json";

// 数据源（当前：管线生成的静态 JSON）。
// Supabase 接入点：将来用户 PK/排行从 Supabase 读，预测仍可 SSG 静态化。
export function getPredictions(): Predictions {
  return raw as unknown as Predictions;
}

export function groupedByGroup(): Record<string, MatchPrediction[]> {
  const out: Record<string, MatchPrediction[]> = {};
  for (const m of getPredictions().matches) {
    (out[m.group] ??= []).push(m);
  }
  for (const g of Object.keys(out)) {
    out[g].sort((a, b) => a.matchday - b.matchday);
  }
  return out;
}
