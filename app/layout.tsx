import type { Metadata, Viewport } from "next";
import { Literata, Fraunces } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const literata = Literata({
  subsets: ["latin"],
  variable: "--font-literata",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Chep's Blog",
    template: "%s | Chep's Blog",
  },
  description: "A personal writing archive by Conor Chepenik. I've decided to write everyday for the rest of my life or until Medium goes out of business.",
  keywords: ["blog", "writing", "Conor Chepenik", "personal archive", "daily writing", "bitcoin", "life", "essays"],
  authors: [{ name: "Conor Chepenik" }],
  creator: "Conor Chepenik",
  publisher: "Conor Chepenik",
  metadataBase: new URL("https://chepsblog.com"),
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "Chep's Blog",
    title: "Chep's Blog",
    description: "A personal writing archive by Conor Chepenik. Daily writing until Medium goes out of business.",
    images: [
      {
        url: "https://i.nostr.build/WRENNwgKeliYZ52G.jpg",
        width: 1200,
        height: 630,
        alt: "Chep's Blog",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Chep's Blog",
    description: "A personal writing archive by Conor Chepenik. Daily writing until Medium goes out of business.",
    creator: "@conaboricua",
    images: ["https://i.nostr.build/WRENNwgKeliYZ52G.jpg"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fdfbf7" },
    { media: "(prefers-color-scheme: dark)", color: "#171412" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${literata.variable} ${fraunces.variable}`}>
      <head />
      <body className="antialiased">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
