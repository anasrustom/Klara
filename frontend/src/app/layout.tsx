import type { Metadata } from "next";
import { Inter, Cairo } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/contexts/LanguageContext";

const inter = Inter({ 
  subsets: ["latin"],
  variable: '--font-inter',
  display: 'swap',
});

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: '--font-cairo',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Klara - AI Contract Lifecycle Management",
  description: "Klara: AI-powered contract analysis and management platform supporting English and Arabic",
  keywords: ["contract management", "AI", "legal tech", "document analysis", "CLM", "Klara"],
  icons: {
    icon: '/favicon.svg',
    apple: '/favicon.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" dir="ltr" className={`${inter.variable} ${cairo.variable}`}>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body className={`${inter.className} font-sans`}>
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
