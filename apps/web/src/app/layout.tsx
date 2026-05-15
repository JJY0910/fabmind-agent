import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FabMind Agent',
  description: 'Evidence-first troubleshooting platform for Load Port / FOUP Clamp equipment.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
