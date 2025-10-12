import './globals.css';
import { Inter, JetBrains_Mono } from 'next/font/google';
import Navigation from '@/components/Navigation';

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-inter',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  display: 'swap',
  variable: '--font-jetbrains',
});

export const metadata = { title: process.env.NEXT_PUBLIC_APP_NAME || 'SportsEdge' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetbrainsMono.variable}`}>
        <Navigation />
        {children}
      </body>
    </html>
  );
}
