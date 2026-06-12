const ORDER = ["0", "1", "2", "3", "4", "5", "6", "7+"];

export function GoalSpark({ tg }: { tg: Record<string, number> }) {
  const max = Math.max(...Object.values(tg)) || 1;
  return (
    <div className="tgrow">
      {ORDER.map((k) => (
        <div className="tg" key={k}>
          <div className="tgfill" style={{ height: `${(tg[k] / max) * 100}%` }} />
          <div className="tglab">{k}</div>
        </div>
      ))}
    </div>
  );
}
