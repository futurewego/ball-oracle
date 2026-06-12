// 把 Python 管线产出的 build/predictions.json 同步到前端 data/ 供 SSG 导入。
import { mkdirSync, copyFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "../../build/predictions.json");
const dest = resolve(here, "../data/predictions.json");

if (!existsSync(src)) {
  console.error(`未找到 ${src}，请先运行: python -m pipeline.build`);
  process.exit(1);
}
mkdirSync(dirname(dest), { recursive: true });
copyFileSync(src, dest);
console.log(`已同步预测数据 -> ${dest}`);
