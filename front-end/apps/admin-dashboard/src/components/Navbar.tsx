"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  Users,
  Building2,
  Bed,
  Calendar,
  CreditCard,
  Bell,
  Menu,
  X,
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Tự động ẩn Taskbar nếu đang ở trang Đăng nhập (/login)
  if (pathname === "/login") {
    return null;
  }

  const navItems = [
    { href: "/Users", label: "Người dùng", icon: Users },
    { href: "/Hotels", label: "Khách Sạn", icon: Building2 },
    { href: "/Rooms", label: "Phòng", icon: Bed },
    { href: "/Bookings", label: "Đặt Phòng", icon: Calendar },
    { href: "/Payments", label: "Thanh toán", icon: CreditCard },
    { href: "/Notifications", label: "Thông báo", icon: Bell },
  ];

  return (
    <nav className="sticky top-0 z-50 py-4 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white/60 backdrop-blur-md rounded-2xl shadow-sm p-3 sm:p-4 w-full">
          <div className="flex flex-wrap items-center gap-2 sm:gap-4">
            {/* Logo */}
            <div className="flex items-center flex-shrink-0 mr-2">
              <Link href="/" className="flex items-center">
                <span className="text-lg font-bold text-gray-900">
                  Admin Dashboard
                </span>
              </Link>
            </div>

            {/* Desktop Navigation - Grid layout for even distribution */}
            <div className="hidden sm:flex flex-1 flex-wrap items-center gap-2 sm:gap-3">
              {navItems.map((item) => {
                const isActive =
                  pathname === item.href ||
                  pathname?.startsWith(item.href + "/");
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center space-x-1.5 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                      isActive
                        ? "bg-gray-100 text-gray-900"
                        : "text-gray-800 hover:bg-gray-50 hover:opacity-60"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* Admin Badge */}
            <div className="hidden sm:flex items-center flex-shrink-0 ml-auto">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-100 text-xs font-semibold text-indigo-700">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Quản trị viên
              </span>
            </div>

            {/* Mobile menu button */}
            <div className="sm:hidden ml-auto flex-shrink-0">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-lg text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300"
              >
                {isMobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <div className="sm:hidden mt-2">
          <div className="bg-white/60 backdrop-blur-md rounded-2xl shadow-sm p-4 space-y-2">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href || pathname?.startsWith(item.href + "/");
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`flex items-center space-x-3 px-3 py-3 rounded-xl text-sm font-medium transition-opacity whitespace-nowrap ${
                    isActive
                      ? "bg-gray-100 text-gray-900"
                      : "text-gray-800 hover:bg-gray-50 hover:opacity-60"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            <div className="border-t border-gray-200 pt-3 mt-2">
              <span className="inline-flex items-center gap-2 px-3 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 rounded-xl w-full">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Đang trực tuyến: Quản trị viên
              </span>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
