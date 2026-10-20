"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { formatVND, calculateNights } from "@/lib/utils";
import {
  ShieldCheck,
  CreditCard,
  Building2,
  Calendar,
  Users,
  CheckCircle2,
  AlertCircle,
  QrCode,
  Wallet,
  Landmark,
  ArrowRight,
  ChevronLeft,
} from "lucide-react";

function CheckoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  const hotelId = parseInt(searchParams.get("hotel_id") || "4", 10);
  const hotelName = searchParams.get("hotel_name") || "Test JWT Grand Hotel";
  const roomTypeId = parseInt(searchParams.get("room_type_id") || "4", 10);
  const roomTypeName = searchParams.get("room_type_name") || "Premier Oceanfront Suite";
  const roomId = parseInt(searchParams.get("room_id") || "21", 10);
  const roomNumber = searchParams.get("room_number") || "P.401";
  const pricePerNight = parseFloat(searchParams.get("price_per_night") || "1800000");
  const checkIn = searchParams.get("check_in") || "2026-11-01";
  const checkOut = searchParams.get("check_out") || "2026-11-03";

  const nights = calculateNights(checkIn, checkOut);
  const roomTotal = pricePerNight * nights;
  const taxAndFee = Math.round(roomTotal * 0.1); // 10% VAT & Service fee
  const finalTotal = roomTotal + taxAndFee;

  // Guest Information Form
  const [guestName, setGuestName] = useState(user?.ho_ten || "");
  const [guestEmail, setGuestEmail] = useState(user?.email || "");
  const [guestPhone, setGuestPhone] = useState(user?.sdt || "");
  const [specialNotes, setSpecialNotes] = useState("");

  // Payment Method
  const [paymentMethod, setPaymentMethod] = useState<"VNPAY" | "MOMO" | "ATM_CARD" | "TIEN_MAT">("VNPAY");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (user) {
      if (!guestName && user.ho_ten) setGuestName(user.ho_ten);
      if (!guestEmail && user.email) setGuestEmail(user.email);
      if (!guestPhone && user.sdt) setGuestPhone(user.sdt);
    }
  }, [user]);

  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    if (!guestName.trim() || !guestEmail.trim() || !guestPhone.trim()) {
      setErrorMessage("Vui lòng điền đầy đủ Họ tên, Email và Số điện thoại!");
      return;
    }

    setIsSubmitting(true);

    try {
      // 1. Tạo đơn đặt phòng qua Booking Service
      const bookingPayload = {
        id_khach_san: hotelId,
        ngay_nhan_phong: checkIn,
        ngay_tra_phong: checkOut,
        rooms: [
          {
            id_phong: roomId,
            id_loai_phong: roomTypeId,
            so_phong: roomNumber,
            ten_loai_phong: roomTypeName,
            gia: roomTotal,
          },
        ],
        khach_o: {
          ho_ten: guestName.trim(),
          email: guestEmail.trim(),
          sdt: guestPhone.trim(),
          ghi_chu_dac_biet: specialNotes.trim() || undefined,
        },
        id_tai_khoan: user?.id ? Number(user.id) : undefined,
      };

      const bookingRes = await apiClient.createBookingOrder(bookingPayload);

      const bookingCode = bookingRes.ma_booking;
      const bookingId = bookingRes.id_dat_phong;

      // 2. Tạo giao dịch thanh toán
      try {
        const paymentRes = await apiClient.createPayment({
          id_dat_phong: bookingId,
          ma_booking: bookingCode,
          so_tien: finalTotal,
          phuong_thuc: paymentMethod as any,
          ghi_chu: `Thanh toán cho đơn ${bookingCode}`,
        });

        // 3. Nếu là thanh toán online (VNPAY / MOMO / ATM), mô phỏng IPN tự động xác nhận đơn
        if (paymentMethod !== "TIEN_MAT" && paymentRes.ma_giao_dich_gateway) {
          try {
            await apiClient.simulateIpn({
              ma_giao_dich_gateway: paymentRes.ma_giao_dich_gateway,
              note: `Thanh toán tự động thành công qua cổng ${paymentMethod}`,
            });
          } catch (ipnErr) {
            console.warn("IPN simulation warning:", ipnErr);
          }
        }
      } catch (payErr) {
        console.warn("Payment service warning, booking was created:", payErr);
      }

      // 4. Chuyển hướng tới trang thành công kèm mã QR
      router.push(`/booking/success/${bookingCode}`);
    } catch (err: any) {
      console.error("Booking error:", err);
      setErrorMessage(
        err.message || "Không thể khởi tạo đơn đặt phòng. Vui lòng kiểm tra lại thông tin."
      );
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button */}
      <div>
        <Link
          href={`/hotels/${hotelId}`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Quay lại thông tin khách sạn
        </Link>
      </div>

      {/* Stepper Progress */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-center gap-3 sm:gap-8 text-xs font-bold">
          <div className="flex items-center gap-2 text-indigo-600">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs">
              1
            </span>
            <span>Thông tin đặt phòng</span>
          </div>
          <span className="w-8 sm:w-16 h-0.5 bg-indigo-200" />
          <div className="flex items-center gap-2 text-indigo-600">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs">
              2
            </span>
            <span>Thanh toán</span>
          </div>
          <span className="w-8 sm:w-16 h-0.5 bg-slate-200" />
          <div className="flex items-center gap-2 text-slate-400">
            <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-xs">
              3
            </span>
            <span>Nhận vé điện tử & QR</span>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2.5 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-semibold">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Checkout Columns */}
      <form onSubmit={handleBookingSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left Column: Form & Payment Methods */}
        <div className="lg:col-span-7 space-y-8">
          {/* Guest Info Card */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">
                Thông tin người nhận phòng
              </h3>
              <span className="text-xs font-bold text-indigo-600">
                * Bắt buộc
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                  Họ và tên khách chính *
                </label>
                <input
                  type="text"
                  required
                  value={guestName}
                  onChange={(e) => setGuestName(e.target.value)}
                  placeholder="Ví dụ: NGUYEN VAN A (như trên CCCD)"
                  className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                    Email nhận vé điện tử *
                  </label>
                  <input
                    type="email"
                    required
                    value={guestEmail}
                    onChange={(e) => setGuestEmail(e.target.value)}
                    placeholder="nguyenvana@gmail.com"
                    className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Vé điện tử và mã QR sẽ gửi về địa chỉ này
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                    Số điện thoại liên hệ *
                  </label>
                  <input
                    type="tel"
                    required
                    value={guestPhone}
                    onChange={(e) => setGuestPhone(e.target.value)}
                    placeholder="0901234567"
                    className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Khách sạn sẽ gọi để xác nhận dịch vụ
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                  Yêu cầu đặc biệt (Không bắt buộc)
                </label>
                <textarea
                  rows={2}
                  value={specialNotes}
                  onChange={(e) => setSpecialNotes(e.target.value)}
                  placeholder="Ví dụ: Nhận phòng muộn sau 18:00, phòng tầng cao, giường đôi..."
                  className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Payment Method Selector Card */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
            <div className="pb-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">
                Phương thức thanh toán
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Mọi giao dịch đều được mã hóa và bảo mật an toàn tuyệt đối
              </p>
            </div>

            <div className="space-y-3">
              {/* VNPAY */}
              <label
                onClick={() => setPaymentMethod("VNPAY")}
                className={`flex items-center gap-4 p-4 rounded-2xl border cursor-pointer transition-all ${
                  paymentMethod === "VNPAY"
                    ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="paymentMethod"
                  checked={paymentMethod === "VNPAY"}
                  onChange={() => setPaymentMethod("VNPAY")}
                  className="w-4 h-4 text-indigo-600"
                />
                <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center font-black text-xs shrink-0">
                  <QrCode className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold text-slate-900">VNPAY QR</p>
                  <p className="text-xs text-slate-500">
                    Quét mã QR bằng ứng dụng ngân hàng hoặc ví VNPAY
                  </p>
                </div>
                <span className="px-2 py-0.5 rounded-md bg-red-100 text-red-800 text-[10px] font-bold">
                  Khuyên dùng
                </span>
              </label>

              {/* MoMo */}
              <label
                onClick={() => setPaymentMethod("MOMO")}
                className={`flex items-center gap-4 p-4 rounded-2xl border cursor-pointer transition-all ${
                  paymentMethod === "MOMO"
                    ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="paymentMethod"
                  checked={paymentMethod === "MOMO"}
                  onChange={() => setPaymentMethod("MOMO")}
                  className="w-4 h-4 text-indigo-600"
                />
                <div className="w-10 h-10 rounded-xl bg-pink-50 text-pink-600 flex items-center justify-center font-black text-xs shrink-0">
                  <Wallet className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold text-slate-900">Ví điện tử MoMo</p>
                  <p className="text-xs text-slate-500">
                    Thanh toán nhanh chóng qua ứng dụng ví MoMo
                  </p>
                </div>
              </label>

              {/* ATM Card */}
              <label
                onClick={() => setPaymentMethod("ATM_CARD")}
                className={`flex items-center gap-4 p-4 rounded-2xl border cursor-pointer transition-all ${
                  paymentMethod === "ATM_CARD"
                    ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="paymentMethod"
                  checked={paymentMethod === "ATM_CARD"}
                  onChange={() => setPaymentMethod("ATM_CARD")}
                  className="w-4 h-4 text-indigo-600"
                />
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-black text-xs shrink-0">
                  <CreditCard className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold text-slate-900">
                    Thẻ ATM Nội địa / Internet Banking
                  </p>
                  <p className="text-xs text-slate-500">
                    Hỗ trợ tất cả các ngân hàng tại Việt Nam
                  </p>
                </div>
              </label>

              {/* Pay at Hotel */}
              <label
                onClick={() => setPaymentMethod("TIEN_MAT")}
                className={`flex items-center gap-4 p-4 rounded-2xl border cursor-pointer transition-all ${
                  paymentMethod === "TIEN_MAT"
                    ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="paymentMethod"
                  checked={paymentMethod === "TIEN_MAT"}
                  onChange={() => setPaymentMethod("TIEN_MAT")}
                  className="w-4 h-4 text-indigo-600"
                />
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-black text-xs shrink-0">
                  <Landmark className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold text-slate-900">
                    Thanh toán khi nhận phòng (Pay at hotel)
                  </p>
                  <p className="text-xs text-slate-500">
                    Giữ phòng trước, thanh toán trực tiếp tại quầy lễ tân
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Right Column: Order Summary & Submit */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6 sticky top-28">
            <h3 className="text-lg font-bold text-slate-900 pb-3 border-b border-slate-100">
              Tóm tắt đơn đặt phòng
            </h3>

            {/* Hotel & Room Info */}
            <div className="space-y-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                  Khách sạn
                </span>
                <h4 className="text-base font-extrabold text-slate-900">
                  {hotelName}
                </h4>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 space-y-1.5">
                <p className="text-xs font-bold text-slate-800">
                  {roomTypeName}
                </p>
                <p className="text-xs text-slate-500">
                  Số phòng dự kiến: <strong className="text-slate-800">{roomNumber}</strong>
                </p>
              </div>
            </div>

            {/* Stay Dates */}
            <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-100 text-xs">
              <div>
                <span className="text-slate-400 font-medium">Nhận phòng:</span>
                <p className="font-bold text-slate-900 mt-0.5">{checkIn}</p>
                <p className="text-[11px] text-slate-500">Từ 14:00</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Trả phòng:</span>
                <p className="font-bold text-slate-900 mt-0.5">{checkOut}</p>
                <p className="text-[11px] text-slate-500">Trước 12:00</p>
              </div>
            </div>

            {/* Price Breakdown */}
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span>
                  Tiền phòng ({nights} đêm x {formatVND(pricePerNight)})
                </span>
                <span className="font-bold text-slate-900">
                  {formatVND(roomTotal)}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>Thuế VAT & Phí phục vụ (10%)</span>
                <span className="font-bold text-slate-900">
                  {formatVND(taxAndFee)}
                </span>
              </div>
              <div className="flex items-center justify-between text-emerald-600 font-semibold">
                <span>Ưu đãi thành viên LuxeStay</span>
                <span>Miễn phí bữa sáng</span>
              </div>
            </div>

            {/* Final Total */}
            <div className="pt-4 border-t border-slate-200 flex items-baseline justify-between">
              <div>
                <p className="text-xs text-slate-500 font-medium">Tổng tiền thanh toán</p>
                <p className="text-[10px] text-slate-400">Đã bao gồm toàn bộ thuế phí</p>
              </div>
              <span className="text-2xl font-black text-indigo-700">
                {formatVND(finalTotal)}
              </span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-4 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-base shadow-xl shadow-indigo-600/30 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <span className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Đang xử lý đặt phòng & gửi vé...</span>
                </>
              ) : (
                <>
                  <span>Xác nhận & Đặt phòng ngay</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            <div className="flex items-center justify-center gap-2 text-[11px] text-slate-400 text-center">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>Bảo mật giao dịch bằng SSL 256-bit</span>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-400">
          Đang tải thông tin thanh toán...
        </div>
      }
    >
      <CheckoutContent />
    </Suspense>
  );
}
