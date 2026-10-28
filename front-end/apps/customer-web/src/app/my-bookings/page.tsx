"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/api";
import { formatVND, formatDate, calculateNights } from "@/lib/utils";
import type { DatPhongItem, TrangThaiBooking } from "@repo/types";
import {
  Ticket,
  Calendar,
  Building2,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  ExternalLink,
  Search,
  Filter,
} from "lucide-react";

export default function MyBookingsPage() {
  const { user, isAuthenticated, openAuthModal } = useAuth();
  const [bookings, setBookings] = useState<DatPhongItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  const fetchBookings = async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const res = await apiClient.getBookings({ page: 1, page_size: 50 });
      if (res?.items) {
        setBookings(res.items);
      } else {
        setBookings([]);
      }
    } catch (err: any) {
      console.error("Fetch my bookings error:", err);
      if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
        setBookings([
          {
            id_dat_phong: 991,
            ma_booking: "BK-202611-DEMO01",
            id_tai_khoan: 10,
            id_khach_san: 4,
            ngay_nhan_phong: "2026-11-01",
            ngay_tra_phong: "2026-11-03",
            tien_phong: 3600000,
            thue_phi: 360000,
            tong_tien: 3960000,
            trang_thai: "CONFIRMED",
            han_giu_cho: "2026-11-01T15:00:00",
            ngay_tao: "2026-10-25T10:00:00",
            ngay_cap_nhat: "2026-10-25T10:15:00",
            chi_tiet: [
              {
                id_chi_tiet: 1,
                id_dat_phong: 991,
                id_phong: 21,
                id_loai_phong: 4,
                so_phong: "P.401",
                ten_loai_phong: "Premier Oceanfront Suite",
                gia_tai_thoi_diem_dat: 1800000,
              },
            ],
            khach_o: {
              id_khach_o: 1,
              id_dat_phong: 991,
              ho_ten: "Nguyễn Văn A",
              email: "customer@hotel.com",
              sdt: "0912345678",
            },
            nhat_ky: [],
          },
        ]);
      } else {
        setErrorMessage("Không thể kết nối đến máy chủ. Vui lòng thử lại sau.");
        setBookings([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchBookings();
    } else {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  const filteredBookings = useMemo(() => {
    if (selectedStatus === "all") return bookings;
    return bookings.filter((b) => b.trang_thai === selectedStatus);
  }, [bookings, selectedStatus]);

  const getStatusBadge = (status: TrangThaiBooking) => {
    switch (status) {
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Đã xác nhận
          </span>
        );
      case "PENDING_PAYMENT":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5" />
            Chờ thanh toán
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" />
            Đã hủy
          </span>
        );
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Hoàn thành
          </span>
        );
      case "REFUNDED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200">
            Đã hoàn tiền
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-6">
        <div className="w-20 h-20 rounded-3xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto shadow-sm">
          <Ticket className="w-10 h-10" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Quản Lý Đơn Đặt Phòng Của Bạn
          </h1>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Vui lòng đăng nhập tài khoản để tra cứu lịch sử đặt phòng, tải vé điện tử hoặc quản lý các đơn đặt phòng hiện có.
          </p>
        </div>
        <div>
          <button
            onClick={() => openAuthModal("login")}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all hover:scale-105"
          >
            Đăng nhập ngay
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center gap-2 text-indigo-600 text-xs font-bold uppercase tracking-wider">
            <Ticket className="w-4 h-4" />
            Hồ sơ tài khoản
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight mt-1">
            Đơn Đặt Phòng Của Tôi
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Theo dõi tình trạng đơn đặt, quản lý lịch trình và tải vé check-in điện tử
          </p>
        </div>

        <Link
          href="/search"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all hover:scale-105 self-start sm:self-auto"
        >
          <Search className="w-3.5 h-3.5" />
          Đặt thêm phòng mới
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {[
          { id: "all", label: "Tất cả đơn" },
          { id: "CONFIRMED", label: "Đã xác nhận" },
          { id: "PENDING_PAYMENT", label: "Chờ thanh toán" },
          { id: "CANCELLED", label: "Đã hủy" },
          { id: "COMPLETED", label: "Hoàn thành" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedStatus(tab.id)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              selectedStatus === tab.id
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Bookings List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-44 bg-white rounded-3xl border border-slate-200 animate-pulse"
            />
          ))}
        </div>
      ) : errorMessage ? (
        <div className="text-center py-16 bg-white rounded-3xl border border-rose-200 p-8 space-y-4 shadow-xs">
          <div className="w-16 h-16 rounded-full bg-rose-50 flex items-center justify-center mx-auto text-rose-500">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            Không thể kết nối đến máy chủ
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {errorMessage}
          </p>
          <button
            onClick={() => fetchBookings()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
          >
            <RefreshCw className="w-4 h-4" />
            Thử lại
          </button>
        </div>
      ) : filteredBookings.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-3xl border border-slate-200 p-8 space-y-4 shadow-xs">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
            <Ticket className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            {selectedStatus === "all"
              ? "Bạn chưa có đơn đặt phòng nào"
              : "Không có đơn đặt phòng nào trong mục này"}
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Hãy khám phá hàng ngàn khách sạn và resort sang trọng tại LuxeStay với ưu đãi giá tốt nhất ngay hôm nay!
          </p>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md transition-all"
          >
            <Search className="w-3.5 h-3.5" />
            Khám phá khách sạn ngay
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredBookings.map((bk) => {
            const nights = calculateNights(bk.ngay_nhan_phong, bk.ngay_tra_phong);
            const primaryRoom = bk.chi_tiet?.[0];

            return (
              <div
                key={bk.id_dat_phong}
                className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-xs hover:shadow-md transition-all space-y-4"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Mã đơn:
                    </span>
                    <Link
                      href={`/booking/success/${bk.ma_booking}`}
                      className="font-mono text-base font-black text-indigo-700 hover:underline"
                    >
                      {bk.ma_booking}
                    </Link>
                    <span className="text-xs text-slate-400">• Ngày đặt: {formatDate(bk.ngay_tao)}</span>
                  </div>

                  <div>{getStatusBadge(bk.trang_thai)}</div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                  <div className="md:col-span-8 space-y-3">
                    {/* Hotel & Room Title */}
                    <div>
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
                        <Building2 className="w-4 h-4 text-indigo-600 shrink-0" />
                        <span>Khách sạn #{bk.id_khach_san}</span>
                        {primaryRoom?.so_phong && (
                          <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[11px] font-bold">
                            Phòng {primaryRoom.so_phong}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-extrabold text-slate-900 mt-0.5">
                        {primaryRoom?.ten_loai_phong || "Hạng phòng tiêu chuẩn"}
                      </p>
                    </div>

                    {/* Stay Dates */}
                    <div className="flex items-center gap-4 text-xs text-slate-600 bg-slate-50 p-3 rounded-2xl border border-slate-100">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-indigo-600 shrink-0" />
                        <span>
                          Nhận: <strong>{formatDate(bk.ngay_nhan_phong)}</strong>
                        </span>
                      </div>
                      <span>→</span>
                      <div>
                        Trả: <strong>{formatDate(bk.ngay_tra_phong)}</strong>
                      </div>
                      <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 text-[11px] font-bold">
                        {nights} đêm
                      </span>
                    </div>

                    {/* Guest Info */}
                    {bk.khach_o && (
                      <p className="text-xs text-slate-500">
                        Khách ở: <strong className="text-slate-700">{bk.khach_o.ho_ten}</strong> ({bk.khach_o.sdt})
                      </p>
                    )}
                  </div>

                  {/* Right Actions & Total Price */}
                  <div className="md:col-span-4 flex flex-col md:items-end justify-between gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
                    <div>
                      <p className="text-xs text-slate-400 md:text-right">Tổng thanh toán</p>
                      <p className="text-2xl font-black text-indigo-700 md:text-right">
                        {formatVND(bk.tong_tien)}
                      </p>
                      {bk.thue_phi ? (
                        <p className="text-[10px] text-slate-400 md:text-right">
                          (Đã bao gồm {formatVND(bk.thue_phi)} thuế/phí)
                        </p>
                      ) : null}
                    </div>

                    <div className="flex items-center gap-2 w-full md:w-auto">
                      <Link
                        href={`/booking/success/${bk.ma_booking}`}
                        className="w-full md:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Xem vé & QR
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
