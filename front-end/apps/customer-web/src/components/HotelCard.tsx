import React from "react";
import Link from "next/link";
import { Star, MapPin, ChevronRight } from "lucide-react";
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
    tien_nghi?: Array<{
      id_tien_nghi?: number;
      ten_tien_nghi: string;
    }>;
    gia_thap_nhat?: number;
    diem_danh_gia?: number;
    so_luong_danh_gia?: number;
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

  const amenities = Array.isArray(hotel.tien_nghi) ? hotel.tien_nghi : [];
  const minPrice =
    typeof hotel.gia_thap_nhat === "number" ? hotel.gia_thap_nhat : null;

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
        {typeof hotel.so_sao === "number" && (
          <div className="absolute top-3 left-3 flex items-center gap-1 px-2.5 py-1 rounded-xl bg-slate-950/70 backdrop-blur-md text-amber-400 text-xs font-bold shadow-md">
            <Star className="w-3.5 h-3.5 fill-amber-400" />
            <span>{hotel.so_sao} Sao</span>
          </div>
        )}
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
            {typeof hotel.diem_danh_gia === "number" && (
              <div className="flex items-center gap-2 shrink-0">
                <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-slate-800">Đánh giá</p>
                  {typeof hotel.so_luong_danh_gia === "number" && (
                    <p className="text-[10px] text-slate-400">
                      {hotel.so_luong_danh_gia} lượt đánh giá
                    </p>
                  )}
                </div>
                <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white font-extrabold text-sm flex items-center justify-center shadow-xs">
                  {hotel.diem_danh_gia}
                </div>
              </div>
            )}
          </div>

          {/* Description snippet */}
          <p className="text-xs text-slate-600 mt-3 line-clamp-2 leading-relaxed">
            {hotel.mo_ta || "Khách sạn chưa cung cấp mô tả."}
          </p>

          {/* Amenities tags */}
          {amenities.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 mt-4">
              {amenities.slice(0, 4).map((amenity) => (
                <span
                  key={amenity.id_tien_nghi ?? amenity.ten_tien_nghi}
                  className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium"
                >
                  {amenity.ten_tien_nghi}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Pricing and Action */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
          <div>
            <p className="text-[11px] text-slate-400 font-medium">Giá mỗi đêm từ</p>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl md:text-2xl font-black text-indigo-700">
                {minPrice === null ? "Chưa có dữ liệu giá" : formatVND(minPrice)}
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
