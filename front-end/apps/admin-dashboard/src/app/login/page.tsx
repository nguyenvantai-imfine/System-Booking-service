"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@repo/ui/button";
import { apiClient } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await apiClient.login({
        ten_dang_nhap_hoac_email: email.trim(),
        mat_khau: password,
      });

      // Kiểm tra quyền hạn: Chỉ Admin mới có quyền truy cập Admin Dashboard
      if (res.user.vai_tro !== "ADMIN") {
        setError(
          "Tài khoản này không có quyền truy cập trang Quản trị (Admin Dashboard). Chỉ Quản trị viên mới được phép đăng nhập."
        );
        return;
      }

      // Lưu trữ JWT tokens và thông tin tài khoản
      localStorage.setItem("auth_token", res.access_token);
      localStorage.setItem("refresh_token", res.refresh_token);
      localStorage.setItem("auth_user", JSON.stringify(res.user));
      document.cookie = `auth_token=${res.access_token}; path=/; max-age=86400; SameSite=Lax`;

      // Chuyển hướng về trang chủ Admin Dashboard
      router.push("/");
    } catch (err: any) {
      const detail = err?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Email / Tên đăng nhập hoặc mật khẩu không chính xác.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-md border border-slate-200 p-8">
        {/* Tiêu đề */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Đăng Nhập Admin</h1>
          <p className="text-sm text-slate-500 mt-2">
            Hệ thống quản lý đặt phòng khách sạn & người dùng
          </p>
        </div>

        {/* Thông báo lỗi */}
        {error && (
          <div className="mb-6 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Form Đăng nhập */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email hoặc Tên đăng nhập
            </label>
            <input
              type="text"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@hotel.com"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Mật khẩu
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 cursor-pointer text-slate-600">
              <input
                type="checkbox"
                defaultChecked
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              Ghi nhớ đăng nhập
            </label>
            <span className="text-xs text-slate-400">
              (Mặc định: admin@hotel.com / 123456)
            </span>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full py-2.5 text-center flex justify-center"
            disabled={isLoading}
          >
            {isLoading ? "Đang xác thực..." : "Đăng Nhập"}
          </Button>
        </form>
      </div>
    </div>
  );
}
