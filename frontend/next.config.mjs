/** @type {import('next').NextConfig} */
// Media thumbnails are served by the central API configured in NEXT_PUBLIC_API_URL.
// Derive the allowed image origin from that value so local/dev/demo ports all work.
const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fallback = new URL("http://localhost:8000");
let apiOrigin;
try {
  apiOrigin = new URL(apiUrl);
} catch {
  apiOrigin = fallback;
}

const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: apiOrigin.protocol === "https:" ? "https" : "http",
        hostname: apiOrigin.hostname || fallback.hostname,
        port:
          apiOrigin.port ||
          (apiOrigin.protocol === "https:" ? "443" : "80"),
        pathname: "/static/**",
      },
    ],
  },
};

export default nextConfig;
