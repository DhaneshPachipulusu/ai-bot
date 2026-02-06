import type { Metadata } from "next";
import "./globals.css";
import MainLayout from "@/components/MainLayout";
import AuthCheck from "@/components/AuthCheck";
import Providers from "@/components/Providers";

export const metadata: Metadata = {
  title: "AI Interview Bot",
  description: "Master your interview skills with AI-powered practice",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>
          <AuthCheck>
            <MainLayout>{children}</MainLayout>
          </AuthCheck>
        </Providers>
      </body>
    </html>
  );
}