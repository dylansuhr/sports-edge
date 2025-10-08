export const metadata = { title: process.env.NEXT_PUBLIC_APP_NAME || 'sports-edge' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, sans-serif', margin: 0, padding: 16 }}>
        {children}
      </body>
    </html>
  );
}
