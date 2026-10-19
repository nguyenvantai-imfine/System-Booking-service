import type { Metadata } from "next";
import Navbar from "../components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Admin Dashboard - Hệ Thống Quản Lý Khách Sạn",
  description: "Trang quản trị toàn bộ hệ thống đặt phòng",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body className="antialiased bg-slate-100 text-slate-900 min-h-screen max-w-7xl mx-auto px-6">
        <header className="bg-blue-300 border-b border-slate-200 sticky top-0 z-50 shadow-xs">
          <Navbar />
        </header>
        <main>
          {children}
          <div></div>
        </main>
        <footer className="bg-slate-800"></footer>
      </body>
    </html>
  );
}
