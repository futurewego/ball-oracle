import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "球神谕 · 2026世界杯AI预测",
  description: "数据驱动的世界杯竞彩概率分析工具，诚实不承诺赢，仅供参考。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
