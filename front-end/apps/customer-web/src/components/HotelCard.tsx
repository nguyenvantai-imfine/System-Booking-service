import React from "react";
import Link from "next/link";
import { Star, MapPin, Wifi, Waves, Utensils, Sparkles, ChevronRight } from "lucide-react";
import { formatVND } from "@/lib/utils";

interface HotelCardProps {
  hotel: {
    id_khach_san: number;
    ten_khach_san: string;
    dia_chi?: string;
    quan_huyen?: string;
    thanh_pho?: string;
    so_sao?: number;
    anh_dai_dien?: string;
    mo_ta?: string;
    gia_thap_nhat?: number;
    diem_danh_gia?: number;
  };
  checkIn?: string;
  checkOut?: string;
}

export function HotelCard({ hotel, checkIn, checkOut }: HotelCardProps) {
  // High quality fallback image based on ID
  const defaultImages = [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
  ];
  const coverImage =
    hotel.anh_dai_dien ||
    defaultImages[hotel.id_khach_san % defaultImages.length];

  const stars = hotel.so_sao || 5;
  const rating = hotel.diem_danh_gia || 9.2;
  const minPrice = hotel.gia_thap_nhat || 1800000;

  const query = new URLSearchParams();
  if (checkIn) query.set("check_in", checkIn);
  if (checkOut) query.set("check_out", checkOut);
  const detailUrl = `/hotels/${hotel.id_khach_san}${query.toString() ? `?${query.toString()}` : ""}`;

  return (
    <div className="group bg-white rounded-3xl border border-slate-200/90 overflow-hidden shadow-xs hover:shadow-xl hover:shadow-indigo-900/10 transition-all duration-300 flex flex-col md:flex-row hover:-translate-y-1">
      {/* Image thumbnail */}
      <div className="relative md:w-80 h-56 md:h-auto shrink-0 overflow-hidden bg-slate-100">
        <img
          src={coverImage}
          alt={hotel.ten_khach_san}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute top-3 left-3 flex items-center gap-1 px-2.5 py-1 rounded-xl bg-slate-950/70 backdrop-blur-md text-amber-400 text-xs font-bold shadow-md">
          <Star className="w-3.5 h-3.5 fill-amber-400" />
          <span>{stars} Sao</span>
        </div>
        <div className="absolute bottom-3 right-3 px-2 py-0.5 rounded-lg bg-black/60 backdrop-blur-xs text-white text-[11px] font-medium">
          {hotel.thanh_pho || "Việt Nam"}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-5 md:p-6 flex flex-col justify-between">
        <div>
          {/* Header Title & Rating */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <Link href={detailUrl}>
                <h3 className="text-lg md:text-xl font-bold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                  {hotel.ten_khach_san}
                </h3>
              </Link>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="line-clamp-1">
                  {[hotel.dia_chi, hotel.quan_huyen, hotel.thanh_pho]
                    .filter(Boolean)
                    .join(", ")}
                </span>
              </div>
            </div>

            {/* Rating badge */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-bold text-slate-800">Rất tốt</p>
                <p className="text-[10px] text-slate-400">128 đánh giá</p>
              </div>
              <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white font-extrabold text-sm flex items-center justify-center shadow-xs">
                {rating}
              </div>
            </div>
          </div>

          {/* Description snippet */}
          <p className="text-xs text-slate-600 mt-3 line-clamp-2 leading-relaxed">
            {hotel.mo_ta ||
              "Khách sạn đẳng cấp với view biển ngoạn mục, phòng ốc hiện đại trang bị nội thất chuẩn 5 sao, bể bơi vô cực và ẩm thực Á-Âu phong phú."}
          </p>

          {/* Amenities tags */}
          <div className="flex flex-wrap items-center gap-2 mt-4">
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium">
              <Wifi className="w-3 h-3 text-indigo-500" /> Wifi tốc độ cao
            </span>
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium">
              <Waves className="w-3 h-3 text-sky-500" /> Bể bơi vô cực
            </span>
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium">
              <Utensils className="w-3 h-3 text-amber-500" /> Buffet sáng
            </span>
            <span className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-[11px] font-semibold">
              <Sparkles className="w-3 h-3" /> Miễn phí hủy phòng
            </span>
          </div>
        </div>

        {/* Pricing and Action */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
          <div>
            <p className="text-[11px] text-slate-400 font-medium">Giá mỗi đêm từ</p>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl md:text-2xl font-black text-indigo-700">
                {formatVND(minPrice)}
              </span>
              <span className="text-xs text-slate-400">/đêm</span>
            </div>
          </div>

          <Link
            href={detailUrl}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-indigo-600/20 hover:scale-105 active:scale-95 transition-all"
          >
            <span>Xem phòng trống</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
