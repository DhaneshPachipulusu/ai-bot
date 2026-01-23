import type { Metadata } from "next";
import "./globals.css";
import MainLayout from "@/components/MainLayout";
import AuthCheck from "@/components/AuthCheck";

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
        <AuthCheck>
          <MainLayout>{children}</MainLayout>
        </AuthCheck>
      </body>
    </html>
  );
}