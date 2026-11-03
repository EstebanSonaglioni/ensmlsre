import type { NextConfig } from "next";

const apiInternal = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  allowedDevOrigins: [
    "**.hackerrank.net",
    "**.hackerrank.com",
    "**.hrcdn.net",
  ],
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${apiInternal.replace(/\/$/, "")}/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' blob: data: http://localhost:8000 http://localhost:8010",
              "connect-src 'self' http://localhost:8000 http://localhost:8010 ws://localhost:8000 ws://localhost:8010 ws: wss:",
              "frame-ancestors 'self' https://*.hackerrank.com https://*.hackerrank.net https://*.hrcdn.net https://hackerrank.com https://hackerrank.net",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
