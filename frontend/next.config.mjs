/** @type {import('next').NextConfig} */
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig = {
  reactStrictMode: true,
  output: "export", // 纯静态导出 -> out/，可部署任何静态host(GitHub Pages/Vercel/Netlify/自有服务器)
  basePath,
  images: { unoptimized: true }, // 静态导出要求关闭图片优化
  trailingSlash: true,
};

export default nextConfig;
