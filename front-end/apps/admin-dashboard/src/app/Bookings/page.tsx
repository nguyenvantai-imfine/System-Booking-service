"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search,
  Filter,
  Calendar,
  CreditCard,
  User,
  Building2,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Eye,
  RefreshCw,
  X,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type {
  DatPhongItem,
  TrangThaiBooking,
  KhachSanBrief,
} from "@repo/types";

export default function BookingsPage() {
  const [bookings, setBookings] = useState<DatPhongItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Tham chiếu khách sạn
  const [hotels, setHotels] = useState<KhachSanBrief[]>([]);

  // Bộ lọc
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [hotelFilter, setHotelFilter] = useState<string>("all");

  // Trạng thái giao diện
  const [isLoading, setIsLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Modal xem chi tiết đơn đặt phòng
  const [selectedBooking, setSelectedBooking] = useState<DatPhongItem | null>(null);

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

  // Tải danh sách khách sạn
  useEffect(() => {
    const loadHotels = async () => {
      try {
        const res = await apiClient.getHotels({ page: 1, page_size: 100 });
        setHotels(res.items);
      } catch (err) {
        console.error("Lỗi tải khách sạn:", err);
      }
    };
    loadHotels();
  }, []);

  // Tải danh sách đơn đặt phòng từ booking-service
  const fetchBookings = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.getBookings({
        hotel_id: hotelFilter !== "all" ? Number(hotelFilter) : undefined,
        status: statusFilter !== "all" ? (statusFilter as TrangThaiBooking) : undefined,
        keyword: debouncedKeyword || undefined,
        page,
        page_size: pageSize,
      });

      setBookings(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Không thể tải danh sách đơn đặt phòng.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [page, hotelFilter, statusFilter, debouncedKeyword]);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  // Thao tác xác nhận đơn
  const handleConfirmBooking = async (booking: DatPhongItem) => {
    if (!confirm(`Xác nhận đơn đặt phòng "${booking.ma_booking}"?`)) return;
    try {
      await apiClient.confirmBooking(booking.id_dat_phong, "Xác nhận thủ công từ Admin Dashboard");
      setToastMessage({
        type: "success",
        text: `Đã xác nhận đơn đặt phòng ${booking.ma_booking} thành công!`,
      });
      fetchBookings();
      if (selectedBooking?.id_dat_phong === booking.id_dat_phong) {
        const updated = await apiClient.getBookingDetail(booking.id_dat_phong);
        setSelectedBooking(updated);
      }
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Xác nhận đơn thất bại.",
      });
    }
  };

  // Thao tác hủy đơn
  const handleCancelBooking = async (booking: DatPhongItem) => {
    if (!confirm(`Bạn có chắc chắn muốn hủy đơn "${booking.ma_booking}" và giải phóng phòng?`)) return;
    try {
      await apiClient.cancelBooking(booking.id_dat_phong, "Hủy bởi Quản trị viên Dashboard");
      setToastMessage({
        type: "success",
        text: `Đã hủy đơn ${booking.ma_booking} và giải phóng phòng thành công.`,
      });
      fetchBookings();
      if (selectedBooking?.id_dat_phong === booking.id_dat_phong) {
        const updated = await apiClient.getBookingDetail(booking.id_dat_phong);
        setSelectedBooking(updated);
      }
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Hủy đơn thất bại.",
      });
    }
  };

  const getHotelName = (hotelId: number) => {
    const found = hotels.find((h) => h.id_khach_san === hotelId);
    return found ? found.ten_khach_san : `Khách sạn #${hotelId}`;
  };

  const getStatusBadge = (status: TrangThaiBooking) => {
    switch (status) {
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Đã xác nhận
          </span>
        );
      case "PENDING_PAYMENT":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
            Chờ thanh toán (Giữ chỗ)
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
            Đã hủy
          </span>
        );
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
            Hoàn thành
          </span>
        );
      case "REFUNDED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
            Đã hoàn tiền
          </span>
        );
      default:
        return null;
    }
  };

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

      {/* Bộ lọc và Tìm kiếm */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="relative flex-1 w-full lg:max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm theo mã booking, tên khách, email, SĐT..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 focus:bg-white transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            {/* Lọc Khách sạn */}
            <div className="flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-slate-400" />
              <select
                value={hotelFilter}
                onChange={(e) => {
                  setHotelFilter(e.target.value);
                  setPage(1);
                }}
                className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="all">Tất cả Khách sạn</option>
                {hotels.map((h) => (
                  <option key={h.id_khach_san} value={h.id_khach_san}>
                    {h.ten_khach_san}
                  </option>
                ))}
              </select>
            </div>

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
              <option value="PENDING_PAYMENT">Chờ thanh toán (Giữ chỗ)</option>
              <option value="CONFIRMED">Đã xác nhận</option>
              <option value="CANCELLED">Đã hủy</option>
              <option value="COMPLETED">Hoàn thành</option>
              <option value="REFUNDED">Đã hoàn tiền</option>
            </select>

            <button
              onClick={() => {
                setSearchTerm("");
                setHotelFilter("all");
                setStatusFilter("all");
                setPage(1);
              }}
              className="px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded-xl hover:bg-slate-50 transition"
            >
              Reset
            </button>

            <button
              onClick={fetchBookings}
              title="Làm mới dữ liệu"
              className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Bảng Đơn đặt phòng */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="px-5 py-3.5">Mã Booking</th>
                <th className="px-5 py-3.5">Khách sạn</th>
                <th className="px-5 py-3.5">Khách ở</th>
                <th className="px-5 py-3.5">Thời gian lưu trú</th>
                <th className="px-5 py-3.5">Phòng đặt</th>
                <th className="px-5 py-3.5">Tổng tiền</th>
                <th className="px-5 py-3.5">Trạng thái</th>
                <th className="px-5 py-3.5 text-center">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                    Đang tải danh sách đơn đặt phòng...
                  </td>
                </tr>
              ) : bookings.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-500">
                    Không tìm thấy đơn đặt phòng nào phù hợp.
                  </td>
                </tr>
              ) : (
                bookings.map((b) => (
                  <tr key={b.id_dat_phong} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-mono font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-100">
                        {b.ma_booking}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-medium text-slate-800">
                      {getHotelName(b.id_khach_san)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="font-medium text-slate-900">
                        {b.khach_o?.ho_ten || "Khách vãng lai"}
                      </div>
                      <div className="text-xs text-slate-400">{b.khach_o?.sdt}</div>
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-600">
                      <div>Nhận: <strong className="text-slate-800">{b.ngay_nhan_phong}</strong></div>
                      <div>Trả: <strong className="text-slate-800">{b.ngay_tra_phong}</strong></div>
                    </td>
                    <td className="px-5 py-4 text-xs">
                      {b.chi_tiet.map((ct) => (
                        <div key={ct.id_chi_tiet} className="font-medium text-slate-800">
                          {ct.so_phong || `Phòng #${ct.id_phong}`} ({ct.ten_loai_phong || "Tiêu chuẩn"})
                        </div>
                      ))}
                    </td>
                    <td className="px-5 py-4 font-bold text-slate-900">
                      {Number(b.tong_tien).toLocaleString("vi-VN")} đ
                    </td>
                    <td className="px-5 py-4">{getStatusBadge(b.trang_thai)}</td>
                    <td className="px-5 py-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          onClick={() => setSelectedBooking(b)}
                          title="Xem chi tiết đơn"
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {b.trang_thai === "PENDING_PAYMENT" && (
                          <button
                            onClick={() => handleConfirmBooking(b)}
                            title="Xác nhận thanh toán"
                            className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}

                        {(b.trang_thai === "PENDING_PAYMENT" || b.trang_thai === "CONFIRMED") && (
                          <button
                            onClick={() => handleCancelBooking(b)}
                            title="Hủy đơn & nhả phòng"
                            className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
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
            Hiển thị <span className="font-semibold text-slate-800">{bookings.length}</span> /{" "}
            <span className="font-semibold text-slate-800">{total}</span> đơn đặt phòng
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page <= 1 || isLoading}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Trang <span className="font-semibold text-slate-800">{page}</span> / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page >= totalPages || isLoading}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* MODAL CHI TIẾT ĐƠN ĐẶT PHÒNG */}
      {selectedBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-xl w-full p-6 space-y-5 animate-in fade-in zoom-in duration-150 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  Đơn Đặt Phòng: {selectedBooking.ma_booking}
                </h3>
                <span className="text-xs text-slate-400">
                  Khởi tạo lúc: {new Date(selectedBooking.ngay_tao).toLocaleString("vi-VN")}
                </span>
              </div>
              <button
                onClick={() => setSelectedBooking(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Thông tin chính */}
            <div className="grid grid-cols-2 gap-3 bg-slate-50 p-4 rounded-xl text-sm">
              <div>
                <span className="text-xs text-slate-400 block">Khách sạn</span>
                <span className="font-semibold text-slate-800">
                  {getHotelName(selectedBooking.id_khach_san)}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Trạng thái</span>
                <div>{getStatusBadge(selectedBooking.trang_thai)}</div>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Ngày nhận phòng</span>
                <span className="font-semibold text-slate-800">{selectedBooking.ngay_nhan_phong}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Ngày trả phòng</span>
                <span className="font-semibold text-slate-800">{selectedBooking.ngay_tra_phong}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Thời hạn giữ chỗ</span>
                <span className="font-semibold text-amber-700">
                  {new Date(selectedBooking.han_giu_cho).toLocaleTimeString("vi-VN")}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Tổng tiền</span>
                <span className="font-bold text-emerald-600 text-base">
                  {Number(selectedBooking.tong_tien).toLocaleString("vi-VN")} đ
                </span>
              </div>
            </div>

            {/* Thông tin khách hàng */}
            <div>
              <h4 className="font-semibold text-slate-800 text-sm mb-2 flex items-center gap-1.5">
                <User className="w-4 h-4 text-slate-500" />
                Thông Tin Khách Lưu Trú
              </h4>
              <div className="border border-slate-200 rounded-xl p-3 text-sm space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Họ và tên:</span>
                  <span className="font-medium text-slate-800">{selectedBooking.khach_o?.ho_ten}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Email:</span>
                  <span className="font-medium text-slate-800">{selectedBooking.khach_o?.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Số điện thoại:</span>
                  <span className="font-medium text-slate-800">{selectedBooking.khach_o?.sdt}</span>
                </div>
                {selectedBooking.khach_o?.ghi_chu_dac_biet && (
                  <div className="border-t pt-1.5 text-xs text-slate-600">
                    <span className="font-semibold text-slate-700">Ghi chú:</span>{" "}
                    {selectedBooking.khach_o.ghi_chu_dac_biet}
                  </div>
                )}
              </div>
            </div>

            {/* Danh sách phòng đã chọn */}
            <div>
              <h4 className="font-semibold text-slate-800 text-sm mb-2 flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-slate-500" />
                Danh Sách Phòng Trong Đơn
              </h4>
              <div className="border border-slate-200 rounded-xl divide-y text-sm">
                {selectedBooking.chi_tiet.map((ct) => (
                  <div key={ct.id_chi_tiet} className="p-3 flex justify-between items-center">
                    <div>
                      <div className="font-bold text-slate-900">
                        {ct.so_phong || `Phòng #${ct.id_phong}`}
                      </div>
                      <div className="text-xs text-slate-500">{ct.ten_loai_phong || "Hạng phòng chuẩn"}</div>
                    </div>
                    <div className="font-semibold text-slate-800">
                      {Number(ct.gia_tai_thoi_diem_dat).toLocaleString("vi-VN")} đ / đêm
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Lịch sử trạng thái */}
            <div>
              <h4 className="font-semibold text-slate-800 text-sm mb-2 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-slate-500" />
                Lịch Sử Trạng Thái (Audit Trail)
              </h4>
              <div className="space-y-1.5 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
                {selectedBooking.nhat_ky.map((nk) => (
                  <div key={nk.id_nhat_ky} className="flex items-start justify-between">
                    <div>
                      <span className="font-semibold text-slate-800">{nk.trang_thai_moi}</span>:{" "}
                      <span className="text-slate-600">{nk.ly_do}</span>
                    </div>
                    <span className="text-slate-400 whitespace-nowrap ml-2">
                      {new Date(nk.thoi_gian).toLocaleTimeString("vi-VN")}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Nút hành động */}
            <div className="flex justify-end gap-3 pt-2 border-t">
              {selectedBooking.trang_thai === "PENDING_PAYMENT" && (
                <button
                  onClick={() => handleConfirmBooking(selectedBooking)}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold transition"
                >
                  Xác Nhận Đơn
                </button>
              )}
              {(selectedBooking.trang_thai === "PENDING_PAYMENT" || selectedBooking.trang_thai === "CONFIRMED") && (
                <button
                  onClick={() => handleCancelBooking(selectedBooking)}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-semibold transition"
                >
                  Hủy Đơn Đặt
                </button>
              )}
              <button
                onClick={() => setSelectedBooking(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-semibold transition"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
