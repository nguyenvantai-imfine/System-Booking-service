import React from "react";
import Link from "next/link";
import { Hotel, Phone, Mail, MapPin, ShieldCheck, Award, Clock, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-auto bg-slate-900 text-slate-300 border-t border-slate-800">
      {/* Features Bar */}
      <div className="border-b border-slate-800/80 bg-slate-950/60 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Bảo đảm giá tốt nhất</h4>
                <p className="text-xs text-slate-400">Không phí ẩn, hoàn tiền nếu tìm thấy giá rẻ hơn</p>
              </div>
            </div>

            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center shrink-0">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Xác nhận tức thì</h4>
                <p className="text-xs text-slate-400">Nhận ngay mã vé điện tử và QR code qua Email</p>
              </div>
            </div>

            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                <Award className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Khách sạn chuẩn 4-5★</h4>
                <p className="text-xs text-slate-400">Được thẩm định thực tế và xác thực chất lượng</p>
              </div>
            </div>

            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                <Phone className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Hỗ trợ 24/7</h4>
                <p className="text-xs text-slate-400">Đội ngũ chuyên viên tư vấn mọi lúc mọi nơi</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer Links */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Company Info */}
          <div className="lg:col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md">
                <Hotel className="w-5 h-5" />
              </div>
              <span className="text-2xl font-black tracking-tight text-white">
                LuxeStay
              </span>
            </Link>
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
              Nền tảng đặt phòng khách sạn và resort cao cấp hàng đầu Việt Nam. Kết nối bạn với hàng ngàn không gian nghỉ dưỡng sang trọng bậc nhất.
            </p>
            <div className="space-y-2 text-xs text-slate-400 pt-2">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-indigo-400" />
                <span>Tòa nhà Innovation Hub, Quận 1, TP. Hồ Chí Minh</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-indigo-400" />
                <span>Hotline: 1900 8888 (Miễn phí cước gọi)</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-indigo-400" />
                <span>support@luxestay.vn</span>
              </div>
            </div>
          </div>

          {/* Destinations */}
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-4">
              Điểm đến nổi bật
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <Link href="/search?city=Đà Nẵng" className="hover:text-white transition-colors">
                  Khách sạn Đà Nẵng
                </Link>
              </li>
              <li>
                <Link href="/search?city=Hà Nội" className="hover:text-white transition-colors">
                  Khách sạn Hà Nội
                </Link>
              </li>
              <li>
                <Link href="/search?city=TP. Hồ Chí Minh" className="hover:text-white transition-colors">
                  Khách sạn Sài Gòn
                </Link>
              </li>
              <li>
                <Link href="/search?city=Phú Quốc" className="hover:text-white transition-colors">
                  Resort Phú Quốc
                </Link>
              </li>
              <li>
                <Link href="/search?city=Nha Trang" className="hover:text-white transition-colors">
                  Khách sạn Nha Trang
                </Link>
              </li>
            </ul>
          </div>

          {/* Policies */}
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-4">
              Chính sách & Hỗ trợ
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <a href="#rules" className="hover:text-white transition-colors">
                  Quy định đặt phòng
                </a>
              </li>
              <li>
                <a href="#refund" className="hover:text-white transition-colors">
                  Chính sách hoàn tiền
                </a>
              </li>
              <li>
                <a href="#privacy" className="hover:text-white transition-colors">
                  Bảo mật thông tin
                </a>
              </li>
              <li>
                <a href="#faq" className="hover:text-white transition-colors">
                  Câu hỏi thường gặp
                </a>
              </li>
            </ul>
          </div>

          {/* Payment Methods */}
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-4">
              Kênh thanh toán
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
              <span className="p-2.5 rounded-lg bg-slate-800 text-center text-slate-200 border border-slate-700">
                VNPAY QR
              </span>
              <span className="p-2.5 rounded-lg bg-slate-800 text-center text-slate-200 border border-slate-700">
                MoMo Wallet
              </span>
              <span className="p-2.5 rounded-lg bg-slate-800 text-center text-slate-200 border border-slate-700">
                Thẻ ATM Nội địa
              </span>
              <span className="p-2.5 rounded-lg bg-slate-800 text-center text-slate-200 border border-slate-700">
                Visa / Master
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-3">
              Mã hóa SSL 256-bit bảo mật tuyệt đối cho mọi giao dịch thanh toán.
            </p>
          </div>
        </div>

        {/* Bottom copyright */}
        <div className="mt-12 pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 LuxeStay Platform. Bản quyền thuộc về Hệ thống Đặt phòng Khách sạn.</p>
          <p className="flex items-center gap-1">
            Thiết kế trải nghiệm nghỉ dưỡng hoàn hảo <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
          </p>
        </div>
      </div>
    </footer>
  );
}
