"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { HotelCard } from "@/components/HotelCard";
import { apiClient } from "@/lib/api";
import {
  Sparkles,
  MapPin,
  ShieldCheck,
  TrendingUp,
  Percent,
  Compass,
  ArrowRight,
  Flame,
} from "lucide-react";

export default function HomePage() {
  const [hotels, setHotels] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchFeaturedHotels() {
      try {
        const res = await apiClient.getHotels({ page: 1, page_size: 6 });
        if (res?.items && res.items.length > 0) {
          setHotels(res.items);
        } else {
          // Sample fallback hotels if database is empty
          setHotels([
            {
              id_khach_san: 4,
              ten_khach_san: "Test JWT Grand Hotel",
              dia_chi: "123 Võ Nguyên Giáp",
              quan_huyen: "Sơn Trà",
              thanh_pho: "Đà Nẵng",
              so_sao: 5,
              gia_thap_nhat: 1800000,
              diem_danh_gia: 9.4,
              mo_ta:
                "Tọa lạc ngay mặt biển Mỹ Khê với tầm nhìn vô cực ra vịnh Đà Nẵng. Hệ thống phòng nghỉ xa hoa và dịch vụ quản gia cao cấp.",
            },
            {
              id_khach_san: 101,
              ten_khach_san: "The Opera Grand Hotel Hanoi",
              dia_chi: "29 Tràng Tiền",
              quan_huyen: "Hoàn Kiếm",
              thanh_pho: "Hà Nội",
              so_sao: 5,
              gia_thap_nhat: 2450000,
              diem_danh_gia: 9.6,
              mo_ta:
                "Khách sạn di sản kiến trúc Pháp cổ điển ngay trung tâm phố cổ Hà Nội. Gần Hồ Gươm và Nhà Hát Lớn.",
            },
            {
              id_khach_san: 102,
              ten_khach_san: "Saigon Riverfront Palace",
              dia_chi: "8 Tôn Đức Thắng",
              quan_huyen: "Quận 1",
              thanh_pho: "TP. Hồ Chí Minh",
              so_sao: 5,
              gia_thap_nhat: 3100000,
              diem_danh_gia: 9.5,
              mo_ta:
                "Khách sạn 5 sao ven sông Sài Gòn với hồ bơi chân mây tầng 30, sky bar đẳng cấp và nhà hàng sao Michelin.",
            },
          ]);
        }
      } catch (err) {
        console.warn("Could not fetch hotels from API, using curated display:", err);
        setHotels([
          {
            id_khach_san: 4,
            ten_khach_san: "Test JWT Grand Hotel Da Nang",
            dia_chi: "123 Võ Nguyên Giáp",
            quan_huyen: "Sơn Trà",
            thanh_pho: "Đà Nẵng",
            so_sao: 5,
            gia_thap_nhat: 1800000,
            diem_danh_gia: 9.4,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchFeaturedHotels();
  }, []);

  const popularDestinations = [
    {
      name: "Đà Nẵng",
      hotelsCount: "120+ khách sạn",
      image: "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=800&q=80",
      tag: "Biển Mỹ Khê & Bà Nà Hills",
    },
    {
      name: "Hà Nội",
      hotelsCount: "180+ khách sạn",
      image: "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=800&q=80",
      tag: "Phố Cổ & Ẩm Thực Tinh Hoa",
    },
    {
      name: "TP. Hồ Chí Minh",
      hotelsCount: "250+ khách sạn",
      image: "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=800&q=80",
      tag: "Sôi Động & Hiện Đại",
    },
    {
      name: "Phú Quốc",
      hotelsCount: "95+ resort cao cấp",
      image: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
      tag: "Đảo Ngọc & Hoàng Hôn",
    },
    {
      name: "Nha Trang",
      hotelsCount: "110+ khách sạn",
      image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
      tag: "Vịnh Biển Thiên Đường",
    },
    {
      name: "Đà Lạt",
      hotelsCount: "140+ biệt thự nghỉ dưỡng",
      image: "https://images.unsplash.com/photo-1605649487212-47bdab064df8?auto=format&fit=crop&w=800&q=80",
      tag: "Thành Phố Ngàn Hoa",
    },
  ];

  return (
    <div className="space-y-16 sm:space-y-24 pb-20">
      {/* 1. HERO SECTION */}
      <section className="relative min-h-[620px] flex items-center justify-center pt-12 pb-24 px-4 sm:px-6 lg:px-8 overflow-hidden bg-slate-950">
        {/* Background Image with Ambient Gradients */}
        <div className="absolute inset-0 z-0">
          <img
            src="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=2000&q=85"
            alt="Luxury Hotel Resort"
            className="w-full h-full object-cover opacity-40 scale-105 animate-pulse-subtle"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-950/80 via-transparent to-slate-950/80" />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-bold tracking-wider uppercase backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Nền tảng đặt phòng trực tuyến hàng đầu
          </div>

          <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-tight">
            Nghỉ Dưỡng Thượng Lưu <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200 bg-clip-text text-transparent">
              Trải Nghiệm Đẳng Cấp
            </span>
          </h1>

          <p className="text-sm sm:text-lg text-slate-300 max-w-2xl mx-auto font-medium leading-relaxed">
            Khám phá hơn 5,000+ khách sạn và resort sang trọng tại Việt Nam. Giá cam kết tốt nhất, xác nhận tức thì và hỗ trợ tận tâm 24/7.
          </p>

          {/* Floating Search Bar */}
          <div className="pt-4 max-w-4xl mx-auto">
            <SearchBar />
          </div>

          {/* Quick Badges */}
          <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-medium">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Cam kết giá tốt nhất
            </span>
            <span className="flex items-center gap-1.5">
              <Percent className="w-4 h-4 text-amber-400" /> Giảm tới 35% cho hội viên VIP
            </span>
            <span className="flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-sky-400" /> Hơn 100,000+ đêm nghỉ thành công
            </span>
          </div>
        </div>
      </section>

      {/* 2. POPULAR DESTINATIONS */}
      <section id="destinations" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 text-indigo-600 font-bold text-xs uppercase tracking-wider">
              <Compass className="w-4 h-4" />
              Điểm đến yêu thích
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-1">
              Khám Phá Các Thành Phố Du Lịch
            </h2>
          </div>
          <Link
            href="/search"
            className="flex items-center gap-1.5 text-sm font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            <span>Xem tất cả điểm đến</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {popularDestinations.map((dest) => (
            <Link
              key={dest.name}
              href={`/search?city=${encodeURIComponent(dest.name)}`}
              className="group relative h-64 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
            >
              <img
                src={dest.image}
                alt={dest.name}
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
              <div className="absolute bottom-3 left-3 right-3 text-white">
                <p className="text-[10px] text-amber-300 font-bold tracking-wider uppercase">
                  {dest.tag}
                </p>
                <h3 className="text-base font-extrabold tracking-tight mt-0.5">
                  {dest.name}
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">{dest.hotelsCount}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 3. PROMOTIONAL BANNER */}
      <section id="promotions" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-indigo-900 via-indigo-800 to-sky-900 text-white p-8 sm:p-12 shadow-2xl">
          <div className="absolute -right-10 -bottom-10 w-96 h-96 bg-sky-500/20 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-400 text-slate-950 font-bold text-xs uppercase">
              <Flame className="w-3.5 h-3.5 fill-slate-950" /> Ưu Đãi Mùa Du Lịch 2026
            </div>
            <h3 className="text-2xl sm:text-4xl font-black tracking-tight leading-tight">
              Giảm Ngay 25% Khi Đặt Phòng Tại Đà Nẵng & Nha Trang
            </h3>
            <p className="text-sm text-indigo-100 leading-relaxed">
              Áp dụng cho mọi đơn đặt phòng từ 2 đêm trở lên tại các resort 5 sao cao cấp. Tặng kèm bữa sáng buffet miễn phí và voucher spa 500.000 ₫.
            </p>
            <div className="pt-2">
              <Link
                href="/search?city=Đà Nẵng"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-indigo-950 font-extrabold text-sm hover:bg-amber-300 transition-colors shadow-lg hover:scale-105 transition-transform"
              >
                Nhận Ưu Đãi Ngay
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 4. FEATURED HOTELS SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 text-indigo-600 font-bold text-xs uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-amber-500" />
              Lựa chọn hàng đầu
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-1">
              Khách Sạn & Resort Nổi Bật Nhất
            </h2>
          </div>
          <Link
            href="/search"
            className="flex items-center gap-1.5 text-sm font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            <span>Xem thêm khách sạn</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-56 bg-slate-200/70 rounded-3xl animate-pulse"
              />
            ))}
          </div>
        ) : hotels.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-3xl border border-slate-200">
            <p className="text-slate-500">Chưa có khách sạn nào được cập nhật.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {hotels.map((hotel) => (
              <HotelCard key={hotel.id_khach_san} hotel={hotel} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
