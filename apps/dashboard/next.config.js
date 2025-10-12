/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Performance optimizations
  swcMinify: true, // Use SWC for faster minification

  // Compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Experimental features for better performance
  experimental: {
    optimizeCss: true, // Optimize CSS loading
    scrollRestoration: true,
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },

  // Reduce bundle size
  modularizeImports: {
    recharts: {
      transform: 'recharts/es6/{{member}}',
    },
  },
};

module.exports = nextConfig;
