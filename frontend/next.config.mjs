/** @type {import('next').NextConfig} */
const nextConfig = {
  // Add the following configuration for images.
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000', // Specify the port your FastAPI server is on
        pathname: '/static/**', // Allow all images under the /static/ path
      },
    ],
  },
};

export default nextConfig;
