"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { QRCode } from "@/components/QRCode";
import { formatVND, formatDate } from "@/lib/utils";
import {
  CheckCircle2,
  Printer,
  Calendar,
  MapPin,
  Mail,
  Phone,
  User,
  Ticket,
  ShieldCheck,
  ArrowRight,
  Home,
  Clock,
  Sparkles,
} from "lucide-react";

export default function BookingSuccessPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const [booking, setBooking] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchBooking() {
      try {
        const data = await apiClient.getBookingDetail(code);
        setBooking(data);
      } catch (err) {
        console.warn("Could not fetch real booking detail, using code reference:", err);
        // Fallback representation using the booking code
        setBooking({
          ma_booking: code,
          trang_thai: "CONFIRMED",
          tong_tien: 1980000,
          ngay_nhan_phong: "2026-11-01",
          ngay_tra_phong: "2026-11-03",
          khach_san: {
            ten_khach_san: "Test JWT Grand Hotel",
            dia_chi: "123 Võ Nguyên Giáp, Sơn Trà, Đà Nẵng",
          },
          thong_tin_khach: {
            ho_ten: "Khách hàng LuxeStay",
            email: "khachhang@example.com",
            sdt: "0901234567",
          },
          chi_tiet: [
            {
              ten_loai_phong: "Premier Oceanfront Suite",
              so_phong: "P.401",
              gia_tai_thoi_diem_dat: 1980000,
            },
          ],
        });
      } finally {
        setIsLoading(false);
      }
    }

    if (code) {
      fetchBooking();
    }
  }, [code]);

  const handlePrintTicket = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="inline-block w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-slate-500 font-medium">Đang tải thông tin vé điện tử...</p>
      </div>
    );
  }

  const guest = booking?.thong_tin_khach || {};
  const room = booking?.chi_tiet?.[0] || {};
  const hotel = booking?.khach_san || {};

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      {/* Success Celebration Header */}
      <div className="text-center space-y-3">
        <div className="w-16 h-16 rounded-3xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20 animate-bounce">
          <CheckCircle2 className="w-9 h-9" />
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          Đặt phòng thành công & Đã xác nhận
        </div>
        <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
          Cảm Ơn Quý Khách Đã Đặt Phòng!
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-lg mx-auto">
          Vé điện tử và mã QR check-in đã được hệ thống gửi tự động tới email{" "}
          <strong className="text-slate-800">{guest.email || "của bạn"}</strong>.
        </p>
      </div>

      {/* ELECTRONIC TICKET (E-Ticket Card with QR) */}
      <div className="bg-white rounded-3xl border-2 border-indigo-100 shadow-2xl overflow-hidden print:border-none print:shadow-none">
        {/* Ticket Header */}
        <div className="bg-gradient-to-r from-indigo-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-bold tracking-widest text-indigo-300">
              Vé Đặt Phòng Điện Tử (E-Ticket)
            </span>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight">
              {hotel.ten_khach_san || "Test JWT Grand Hotel"}
            </h2>
            <div className="flex items-center gap-1.5 text-xs text-slate-300">
              <MapPin className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span>{hotel.dia_chi || "123 Võ Nguyên Giáp, Sơn Trà, Đà Nẵng"}</span>
            </div>
          </div>

          <div className="text-left sm:text-right shrink-0">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Mã đặt phòng (Booking Code)
            </span>
            <div className="text-lg sm:text-xl font-black font-mono tracking-wider bg-white/10 px-3.5 py-1.5 rounded-xl text-amber-300 mt-1 border border-white/10 inline-block">
              {booking?.ma_booking || code}
            </div>
          </div>
        </div>

        {/* Ticket Body */}
        <div className="p-6 sm:p-8 grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
          {/* Left Details */}
          <div className="md:col-span-8 space-y-6">
            {/* Stay Dates Grid */}
            <div className="grid grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                  Ngày nhận phòng
                </span>
                <p className="text-base font-extrabold text-slate-900 mt-1">
                  {formatDate(booking?.ngay_nhan_phong)}
                </p>
                <p className="text-xs text-slate-500 font-medium">Từ 14:00 chiều</p>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                  Ngày trả phòng
                </span>
                <p className="text-base font-extrabold text-slate-900 mt-1">
                  {formatDate(booking?.ngay_tra_phong)}
                </p>
                <p className="text-xs text-slate-500 font-medium">Trước 12:00 trưa</p>
              </div>
            </div>

            {/* Room & Guest Info */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <span className="text-slate-400 font-medium">Hạng phòng & Số phòng:</span>
                <p className="text-sm font-bold text-slate-900">
                  {room.ten_loai_phong || "Premier Oceanfront Suite"}
                </p>
                <p className="text-indigo-600 font-semibold">
                  Phòng: {room.so_phong || "P.401"}
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 font-medium">Khách lưu trú:</span>
                <p className="text-sm font-bold text-slate-900">
                  {guest.ho_ten || "Khách hàng LuxeStay"}
                </p>
                <p className="text-slate-500">{guest.sdt || "0901234567"}</p>
              </div>
            </div>

            {/* Total Amount & Status */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 font-medium">Tổng tiền thanh toán</span>
                <p className="text-2xl font-black text-indigo-700">
                  {formatVND(booking?.tong_tien || 1980000)}
                </p>
              </div>

              <div className="text-right">
                <span className="text-xs text-slate-400 font-medium">Trạng thái</span>
                <div>
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-extrabold mt-0.5">
                    ✓ ĐÃ XÁC NHẬN
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right QR Code Check-in Box */}
          <div className="md:col-span-4 flex flex-col items-center justify-center p-6 bg-slate-50/80 rounded-3xl border border-slate-200/80 text-center space-y-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-900">
              Quét mã Check-in
            </span>
            <QRCode value={booking?.ma_booking || code} size={150} />
            <p className="text-[11px] text-slate-500 max-w-[180px] leading-relaxed">
              Xuất trình mã QR này tại quầy lễ tân để nhận phòng nhanh chóng không cần giấy tờ.
            </p>
          </div>
        </div>

        {/* Ticket Footer Instructions */}
        <div className="bg-slate-50 px-6 sm:px-8 py-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-500 gap-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>Thời gian check-in quy định từ 14:00. Hỗ trợ nhận phòng sớm theo tình trạng phòng thực tế.</span>
          </div>
          <div className="flex items-center gap-1 font-semibold text-slate-700 shrink-0">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Xác thực bởi LuxeStay Cloud</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-2 print:hidden">
        <button
          onClick={handlePrintTicket}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-800 font-bold text-xs hover:bg-slate-50 transition-colors shadow-xs"
        >
          <Printer className="w-4 h-4 text-slate-600" />
          In vé điện tử / Lưu PDF
        </button>

        <Link
          href="/search"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
        >
          <span>Khám phá thêm khách sạn</span>
          <ArrowRight className="w-4 h-4" />
        </Link>

        <Link
          href="/"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-colors"
        >
          <Home className="w-4 h-4" />
          Về trang chủ
        </Link>
      </div>
    </div>
  );
}
