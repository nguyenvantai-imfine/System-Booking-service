"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search,
  CreditCard,
  DollarSign,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  RefreshCw,
  X,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  Send,
  ArrowUpRight,
  RotateCcw,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type {
  ThanhToanItem,
  PaymentStats,
  TrangThaiThanhToan,
  PhuongThucThanhToan,
} from "@repo/types";

export default function PaymentsPage() {
  const [payments, setPayments] = useState<ThanhToanItem[]>([]);
  const [stats, setStats] = useState<PaymentStats>({
    total_revenue: 0,
    total_transactions: 0,
    success_count: 0,
    pending_count: 0,
    failed_count: 0,
  });
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Bộ lọc
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [methodFilter, setMethodFilter] = useState<string>("all");

  // Trạng thái giao diện
  const [isLoading, setIsLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Modal Sandbox IPN
  const [isIpnModalOpen, setIsIpnModalOpen] = useState(false);
  const [ipnTxnGateway, setIpnTxnGateway] = useState("");
  const [ipnStatus, setIpnStatus] = useState<TrangThaiThanhToan>("SUCCESS");
  const [ipnNote, setIpnNote] = useState("");
  const [isSubmittingIpn, setIsSubmittingIpn] = useState(false);

  // Debounce tìm kiếm
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedKeyword(searchTerm);
      setPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Tự tắt Toast
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Tải thống kê doanh thu
  const fetchStats = async () => {
    try {
      const res = await apiClient.getPaymentStats();
      setStats(res);
    } catch (err) {
      console.error("Lỗi tải thống kê doanh thu:", err);
    }
  };

  // Tải danh sách giao dịch
  const fetchPayments = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.getPayments({
        status: statusFilter !== "all" ? statusFilter : undefined,
        method: methodFilter !== "all" ? methodFilter : undefined,
        keyword: debouncedKeyword || undefined,
        page,
        page_size: pageSize,
      });

      setPayments(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Không thể tải danh sách giao dịch.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [page, statusFilter, methodFilter, debouncedKeyword]);

  useEffect(() => {
    fetchPayments();
    fetchStats();
  }, [fetchPayments]);

  // Kích hoạt mô phỏng IPN nhanh từ dòng dữ liệu
  const handleQuickSimulateIpn = async (payment: ThanhToanItem, status: "SUCCESS" | "FAILED") => {
    try {
      await apiClient.simulateIpn({
        ma_giao_dich_gateway: payment.ma_giao_dich_gateway,
        trang_thai: status,
        note: `Mô phỏng IPN ${status} từ Admin Dashboard`,
      });
      setToastMessage({
        type: "success",
        text: `Đã mô phỏng IPN ${status} cho GD ${payment.ma_giao_dich_gateway}. Đơn booking ${payment.ma_booking} đã được cập nhật!`,
      });
      fetchPayments();
      fetchStats();
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Mô phỏng IPN thất bại.",
      });
    }
  };

  // Submit modal IPN
  const handleCustomIpnSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ipnTxnGateway.trim()) {
      setToastMessage({ type: "error", text: "Vui lòng nhập mã giao dịch gateway." });
      return;
    }
    setIsSubmittingIpn(true);
    try {
      await apiClient.simulateIpn({
        ma_giao_dich_gateway: ipnTxnGateway.trim(),
        trang_thai: ipnStatus,
        note: ipnNote || "Sandbox IPN simulation",
      });
      setToastMessage({
        type: "success",
        text: `Callback IPN (${ipnStatus}) gửi thành công!`,
      });
      setIsIpnModalOpen(false);
      setIpnTxnGateway("");
      setIpnNote("");
      fetchPayments();
      fetchStats();
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Lỗi mô phỏng callback IPN.",
      });
    } finally {
      setIsSubmittingIpn(false);
    }
  };

  const getStatusBadge = (status: TrangThaiThanhToan) => {
    switch (status) {
      case "SUCCESS":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
            Thành công
          </span>
        );
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
            Đang xử lý
          </span>
        );
      case "FAILED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            Thất bại
          </span>
        );
      case "REFUNDED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <RotateCcw className="w-3.5 h-3.5 text-purple-600" />
            Đã hoàn tiền
          </span>
        );
      default:
        return null;
    }
  };

  const getMethodBadge = (method: PhuongThucThanhToan) => {
    switch (method) {
      case "VNPAY":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
            VNPAY
          </span>
        );
      case "MOMO":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-pink-50 text-pink-700 border border-pink-200">
            MOMO
          </span>
        );
      case "CREDIT_CARD":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
            <CreditCard className="w-3 h-3" />
            Thẻ quốc tế
          </span>
        );
      case "CASH":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300">
            Tiền mặt
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600">
            {method}
          </span>
        );
    }
  };

  const successRate =
    stats.total_transactions > 0
      ? Math.round((stats.success_count / stats.total_transactions) * 100)
      : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Toast thông báo */}
      {toastMessage && (
        <div
          className={`fixed bottom-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border text-sm transition-all ${
            toastMessage.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          )}
          <span>{toastMessage.text}</span>
          <button onClick={() => setToastMessage(null)} className="ml-2 hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* THẺ THỐNG KÊ DOANH THU & DÒNG TIỀN */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Tổng doanh thu */}
        <div className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-2xl p-5 shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-emerald-100 text-xs font-medium uppercase tracking-wider">
                Tổng Dòng Tiền Thu Được
              </p>
              <h3 className="text-2xl font-bold mt-2">
                {Number(stats.total_revenue || 0).toLocaleString("vi-VN")} đ
              </h3>
            </div>
            <div className="p-2.5 bg-white/20 rounded-xl">
              <DollarSign className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs text-emerald-100">
            <TrendingUp className="w-4 h-4 mr-1 text-emerald-200" />
            <span>Doanh thu thực nhận từ giao dịch thành công</span>
          </div>
        </div>

        {/* Tổng giao dịch */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">
                Tổng Giao Dịch
              </p>
              <h3 className="text-2xl font-bold text-slate-800 mt-2">
                {stats.total_transactions}
              </h3>
            </div>
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl border border-blue-100">
              <CreditCard className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-3 text-xs text-slate-500">
            Tỉ lệ thành công: <strong className="text-emerald-600">{successRate}%</strong>
          </div>
        </div>

        {/* Giao dịch thành công */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">
                Thành Công
              </p>
              <h3 className="text-2xl font-bold text-emerald-600 mt-2">
                {stats.success_count}
              </h3>
            </div>
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
              <CheckCircle className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-3 text-xs text-slate-500">
            Đã phát sinh chuyển đổi phòng
          </div>
        </div>

        {/* Chờ xử lý / Thất bại */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">
                Chờ & Thất Bại
              </p>
              <h3 className="text-2xl font-bold text-slate-800 mt-2">
                <span className="text-amber-600">{stats.pending_count}</span>
                <span className="text-slate-300 mx-1.5">/</span>
                <span className="text-rose-600">{stats.failed_count}</span>
              </h3>
            </div>
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl border border-amber-100">
              <Clock className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-3 text-xs text-slate-500">
            {stats.pending_count} đang chờ thanh toán
          </div>
        </div>
      </div>

      {/* BỘ LỌC VÀ TÌM KIẾM */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="relative flex-1 w-full lg:max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm theo mã booking, mã giao dịch gateway..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 focus:bg-white transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            {/* Lọc Phương thức */}
            <select
              value={methodFilter}
              onChange={(e) => {
                setMethodFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">Tất cả Phương thức</option>
              <option value="VNPAY">VNPAY</option>
              <option value="MOMO">MOMO</option>
              <option value="CREDIT_CARD">Thẻ quốc tế</option>
              <option value="CASH">Tiền mặt</option>
            </select>

            {/* Lọc Trạng thái */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">Tất cả Trạng thái</option>
              <option value="SUCCESS">Thành công</option>
              <option value="PENDING">Đang chờ xử lý</option>
              <option value="FAILED">Thất bại</option>
              <option value="REFUNDED">Đã hoàn tiền</option>
            </select>

            <button
              onClick={() => {
                setSearchTerm("");
                setMethodFilter("all");
                setStatusFilter("all");
                setPage(1);
              }}
              className="px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded-xl hover:bg-slate-50 transition"
            >
              Reset
            </button>

            <button
              onClick={() => {
                fetchPayments();
                fetchStats();
              }}
              title="Làm mới dữ liệu"
              className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>

            {/* Nút mở Modal Sandbox */}
            <button
              onClick={() => setIsIpnModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
            >
              <ShieldCheck className="w-4 h-4" />
              Mô Phỏng IPN Sandbox
            </button>
          </div>
        </div>
      </div>

      {/* BẢNG LỊCH SỬ GIAO DỊCH */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="px-5 py-3.5">Mã GD Gateway</th>
                <th className="px-5 py-3.5">Mã Booking</th>
                <th className="px-5 py-3.5">Số tiền</th>
                <th className="px-5 py-3.5">Phương thức</th>
                <th className="px-5 py-3.5">Trạng thái</th>
                <th className="px-5 py-3.5">Thời gian khởi tạo</th>
                <th className="px-5 py-3.5">Cập nhật lúc</th>
                <th className="px-5 py-3.5 text-center">Mô phỏng Sandbox</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                    Đang tải lịch sử giao dịch thanh toán...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-500">
                    Không tìm thấy giao dịch nào phù hợp.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id_thanh_toan} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-4">
                      <div className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-1 rounded border border-slate-200 inline-block">
                        {p.ma_giao_dich_gateway}
                      </div>
                      {p.payment_url && (
                        <a
                          href={p.payment_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-[11px] text-blue-600 hover:underline mt-1"
                        >
                          Cổng thanh toán <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-mono font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-100 text-xs">
                        {p.ma_booking}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-bold text-slate-900 text-base">
                      {Number(p.so_tien).toLocaleString("vi-VN")} đ
                    </td>
                    <td className="px-5 py-4">{getMethodBadge(p.phuong_thuc)}</td>
                    <td className="px-5 py-4">{getStatusBadge(p.trang_thai)}</td>
                    <td className="px-5 py-4 text-xs text-slate-500">
                      {new Date(p.ngay_tao).toLocaleString("vi-VN")}
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-500">
                      {p.ngay_thanh_toan
                        ? new Date(p.ngay_thanh_toan).toLocaleString("vi-VN")
                        : "—"}
                    </td>
                    <td className="px-5 py-4 text-center">
                      {p.trang_thai === "PENDING" ? (
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => handleQuickSimulateIpn(p, "SUCCESS")}
                            title="Mô phỏng Thanh toán Thành Công (SUCCESS)"
                            className="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-xs font-semibold border border-emerald-200 transition"
                          >
                            Xác nhận TT
                          </button>
                          <button
                            onClick={() => handleQuickSimulateIpn(p, "FAILED")}
                            title="Mô phỏng Thanh toán Thất Bại (FAILED)"
                            className="px-2.5 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-semibold border border-rose-200 transition"
                          >
                            Báo lỗi
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Đã kết thúc</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Phân trang */}
        <div className="px-5 py-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <div>
            Hiển thị <span className="font-semibold text-slate-800">{payments.length}</span> /{" "}
            <span className="font-semibold text-slate-800">{total}</span> giao dịch
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
              disabled={page <= 1 || isLoading}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Trang <span className="font-semibold text-slate-800">{page}</span> / {totalPages}
            </span>
            <button
              onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={page >= totalPages || isLoading}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* MODAL MÔ PHỎNG CALLBACK IPN SANDBOX */}
      {isIpnModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                Mô Phỏng IPN Sandbox Gateway
              </h3>
              <button
                onClick={() => setIsIpnModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCustomIpnSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mã giao dịch Gateway (ma_giao_dich_gateway)
                </label>
                <input
                  type="text"
                  required
                  placeholder="VD: TXN-..."
                  value={ipnTxnGateway}
                  onChange={(e) => setIpnTxnGateway(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-xs"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Nhập mã TXN của giao dịch cần mô phỏng callback kết quả từ cổng thanh toán.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Kết quả trả về từ Cổng Thanh toán
                </label>
                <select
                  value={ipnStatus}
                  onChange={(e) => setIpnStatus(e.target.value as TrangThaiThanhToan)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  <option value="SUCCESS">SUCCESS (Thanh toán thành công)</option>
                  <option value="FAILED">FAILED (Thất bại / Hết hạn thanh toán)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Ghi chú mô phỏng
                </label>
                <input
                  type="text"
                  placeholder="VD: Kiểm thử luồng IPN webhook..."
                  value={ipnNote}
                  onChange={(e) => setIpnNote(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-800 space-y-1">
                <div className="font-semibold flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5" />
                  Cơ chế hoạt động:
                </div>
                <div>
                  Khi gửi yêu cầu, <code>payment-service</code> sẽ cập nhật bản ghi giao dịch, sau đó
                  phát tín hiệu Webhook sang <code>booking-service</code> để tự động chuyển đơn sang
                  trạng thái <strong>CONFIRMED</strong> (nếu SUCCESS).
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setIsIpnModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingIpn}
                  className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  {isSubmittingIpn ? "Đang gửi..." : "Gửi Callback IPN"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
