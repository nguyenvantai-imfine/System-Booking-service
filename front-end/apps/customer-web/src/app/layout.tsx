import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { AuthModal } from "@/components/AuthModal";

export const metadata: Metadata = {
  title: "LuxeStay - Đặt Phòng Khách Sạn & Resort Nghỉ Dưỡng Cao Cấp",
  description:
    "Hệ thống đặt phòng khách sạn trực tuyến hàng đầu Việt Nam. Hơn 5,000+ khách sạn và resort sang trọng tại Đà Nẵng, Hà Nội, Nha Trang, Phú Quốc với giá ưu đãi tốt nhất.",
  keywords: "đặt phòng khách sạn, resort đà nẵng, khách sạn hà nội, booking khách sạn, du lịch nghỉ dưỡng",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased selection:bg-indigo-600 selection:text-white">
        <AuthProvider>
          <Navbar />
          <AuthModal />
          <main className="flex-1">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
