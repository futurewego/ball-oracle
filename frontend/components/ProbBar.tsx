import type { Spf } from "@/lib/types";

export function ProbBar({ spf, homeCn, awayCn }: { spf: Spf; homeCn: string; awayCn: string }) {
  const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
  const lbl = (x: number) => `${(x * 100).toFixed(0)}%`;
  return (
    <>
      <div className="bar">
        <div className="seg home" style={{ width: pct(spf.home) }}><span>{lbl(spf.home)}</span></div>
        <div className="seg draw" style={{ width: pct(spf.draw) }}><span>{lbl(spf.draw)}</span></div>
        <div className="seg away" style={{ width: pct(spf.away) }}><span>{lbl(spf.away)}</span></div>
      </div>
      <div className="legend">
        <span><i className="dot home" />{homeCn}胜</span>
        <span><i className="dot draw" />平</span>
        <span><i className="dot away" />{awayCn}胜</span>
      </div>
    </>
  );
}
