"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@repo/ui/button";

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
      // Giả lập kiểm tra đăng nhập (Sau này sẽ gọi @repo/api-client)
      if (email === "admin@hotel.com" && password === "123456") {
        // Đăng nhập thành công -> Chuyển hướng về trang chủ Dashboard
        router.push("/");
      } else {
        setError(
          "Email hoặc mật khẩu không đúng! (Gợi ý: admin@hotel.com / 123456)",
        );
      }
    } catch (err) {
      setError("Đã xảy ra lỗi, vui lòng thử lại sau.");
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
            Hệ thống quản lý đặt phòng khách sạn
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
              Email
            </label>
            <input
              type="email"
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
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              Ghi nhớ đăng nhập
            </label>
            <a href="#" className="text-blue-600 hover:underline font-medium">
              Quên mật khẩu?
            </a>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full py-2.5 text-center flex justify-center"
            disabled={isLoading}
          >
            {isLoading ? "Đang xử lý..." : "Đăng Nhập"}
          </Button>
        </form>
      </div>
    </div>
  );
}
