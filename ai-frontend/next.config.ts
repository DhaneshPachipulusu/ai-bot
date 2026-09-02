import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a standalone server bundle (.next/standalone/server.js) for the
  // multi-stage Docker runtime image.
  output: "standalone",
};

export default nextConfig;
