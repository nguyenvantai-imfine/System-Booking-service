"use client";

import React, { useEffect, useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/SearchBar";
import { HotelCard } from "@/components/HotelCard";
import { apiClient } from "@/lib/api";
import {
  SlidersHorizontal,
  Star,
  DollarSign,
  Wifi,
  Waves,
  Utensils,
  MapPin,
  RefreshCw,
  SearchX,
  AlertCircle,
} from "lucide-react";

function SearchContent() {
  const searchParams = useSearchParams();

  const city = searchParams.get("city") || "";
  const keyword = searchParams.get("keyword") || "";
  const checkIn = searchParams.get("check_in") || "";
  const checkOut = searchParams.get("check_out") || "";
  const adults = parseInt(searchParams.get("adults") || "2", 10);
  const children = parseInt(searchParams.get("children") || "0", 10);
  const rooms = parseInt(searchParams.get("rooms") || "1", 10);

  const [hotels, setHotels] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  // Filter States
  const [selectedStars, setSelectedStars] = useState<number[]>([]);
  const [selectedPriceRange, setSelectedPriceRange] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("popular");

  const fetchHotels = async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const queryParams: any = { page: 1, page_size: 30 };
      if (city) queryParams.city = city;
      if (keyword) queryParams.keyword = keyword;

      const res = await apiClient.getHotels(queryParams);

      if (res?.items && res.items.length > 0) {
        setHotels(res.items);
      } else {
        if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
          setHotels([
            {
              id_khach_san: 4,
              ten_khach_san: `Grand Luxury Resort & Spa ${city || "Đà Nẵng"}`,
              dia_chi: `123 Đường Ven Biển, ${city || "Sơn Trà"}`,
              thanh_pho: city || "Đà Nẵng",
              so_sao: 5,
              gia_thap_nhat: 1800000,
              diem_danh_gia: 9.4,
              mo_ta: `Khách sạn 5 sao cao cấp với tầm nhìn toàn cảnh ${city || "bờ biển"}, hồ bơi vô cực và ẩm thực Á-Âu thượng hạng.`,
            },
          ]);
        } else {
          setHotels([]);
        }
      }
    } catch (err: any) {
      console.error("API search error:", err);
      if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
        setHotels([
          {
            id_khach_san: 4,
            ten_khach_san: `Test JWT Grand Hotel ${city || "Đà Nẵng"} (Demo)`,
            dia_chi: "123 Võ Nguyên Giáp, Sơn Trà",
            thanh_pho: city || "Đà Nẵng",
            so_sao: 5,
            gia_thap_nhat: 1800000,
            diem_danh_gia: 9.4,
          },
        ]);
      } else {
        setErrorMessage("Không thể kết nối đến máy chủ. Vui lòng thử lại sau.");
        setHotels([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHotels();
  }, [city, keyword]);

  // Client-side Filter & Sort
  const filteredHotels = useMemo(() => {
    let result = [...hotels];

    // Star filter
    if (selectedStars.length > 0) {
      result = result.filter((h) => selectedStars.includes(h.so_sao || 5));
    }

    // Price range filter
    if (selectedPriceRange === "under1m") {
      result = result.filter((h) => (h.gia_thap_nhat || 1800000) < 1000000);
    } else if (selectedPriceRange === "1m-2m") {
      result = result.filter((h) => {
        const p = h.gia_thap_nhat || 1800000;
        return p >= 1000000 && p <= 2000000;
      });
    } else if (selectedPriceRange === "2m-4m") {
      result = result.filter((h) => {
        const p = h.gia_thap_nhat || 1800000;
        return p > 2000000 && p <= 4000000;
      });
    } else if (selectedPriceRange === "above4m") {
      result = result.filter((h) => (h.gia_thap_nhat || 1800000) > 4000000);
    }

    // Sort
    if (sortBy === "price_asc") {
      result.sort((a, b) => (a.gia_thap_nhat || 0) - (b.gia_thap_nhat || 0));
    } else if (sortBy === "price_desc") {
      result.sort((a, b) => (b.gia_thap_nhat || 0) - (a.gia_thap_nhat || 0));
    } else if (sortBy === "rating") {
      result.sort((a, b) => (b.diem_danh_gia || 0) - (a.diem_danh_gia || 0));
    }

    return result;
  }, [hotels, selectedStars, selectedPriceRange, sortBy]);

  const toggleStar = (star: number) => {
    setSelectedStars((prev) =>
      prev.includes(star) ? prev.filter((s) => s !== star) : [...prev, star]
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Compact Search Bar */}
      <div>
        <SearchBar
          initialCity={city}
          initialCheckIn={checkIn}
          initialCheckOut={checkOut}
          initialAdults={adults}
          initialChildren={children}
          initialRooms={rooms}
          compact
        />
      </div>

      {/* Main Layout: Filters + Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Sidebar Filters */}
        <aside className="lg:col-span-3 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2 text-slate-900 font-bold text-base">
                <SlidersHorizontal className="w-5 h-5 text-indigo-600" />
                <span>Bộ lọc tìm kiếm</span>
              </div>
              {(selectedStars.length > 0 || selectedPriceRange !== "all") && (
                <button
                  onClick={() => {
                    setSelectedStars([]);
                    setSelectedPriceRange("all");
                  }}
                  className="text-xs font-semibold text-indigo-600 hover:underline"
                >
                  Đặt lại
                </button>
              )}
            </div>

            {/* Star Rating Filter */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Hạng sao khách sạn
              </h4>
              <div className="space-y-2">
                {[5, 4, 3].map((star) => (
                  <label
                    key={star}
                    className="flex items-center gap-2.5 text-sm font-medium text-slate-700 cursor-pointer select-none"
                  >
                    <input
                      type="checkbox"
                      checked={selectedStars.includes(star)}
                      onChange={() => toggleStar(star)}
                      className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-300"
                    />
                    <div className="flex items-center gap-1">
                      {Array.from({ length: star }).map((_, i) => (
                        <Star key={i} className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                      ))}
                      <span className="text-xs text-slate-500 ml-1">({star} sao)</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Price Range Filter */}
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Khoảng giá mỗi đêm
              </h4>
              <div className="space-y-2">
                {[
                  { id: "all", label: "Tất cả mức giá" },
                  { id: "under1m", label: "Dưới 1.000.000 ₫" },
                  { id: "1m-2m", label: "1.000.000 ₫ - 2.000.000 ₫" },
                  { id: "2m-4m", label: "2.000.000 ₫ - 4.000.000 ₫" },
                  { id: "above4m", label: "Trên 4.000.000 ₫" },
                ].map((item) => (
                  <label
                    key={item.id}
                    className="flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer select-none"
                  >
                    <input
                      type="radio"
                      name="priceRange"
                      checked={selectedPriceRange === item.id}
                      onChange={() => setSelectedPriceRange(item.id)}
                      className="w-4 h-4 text-indigo-600 focus:ring-indigo-500 border-slate-300"
                    />
                    <span className="text-xs font-medium">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Popular Amenities Filter */}
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Tiện ích phổ biến
              </h4>
              <div className="space-y-2 text-xs text-slate-600">
                <span className="flex items-center gap-2">
                  <Waves className="w-3.5 h-3.5 text-sky-500" /> Hồ bơi vô cực
                </span>
                <span className="flex items-center gap-2">
                  <Wifi className="w-3.5 h-3.5 text-indigo-500" /> Wifi tốc độ cao
                </span>
                <span className="flex items-center gap-2">
                  <Utensils className="w-3.5 h-3.5 text-amber-500" /> Bữa sáng buffet
                </span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Hotel Results */}
        <div className="lg:col-span-9 space-y-6">
          {/* Results Summary Bar */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base sm:text-lg font-extrabold text-slate-900">
                {city ? `Khách sạn tại ${city}` : "Tất cả khách sạn"}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Tìm thấy{" "}
                <span className="font-bold text-indigo-600">
                  {filteredHotels.length}
                </span>{" "}
                không gian nghỉ dưỡng phù hợp
              </p>
            </div>

            {/* Sort Select */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 whitespace-nowrap">
                Sắp xếp theo:
              </span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-xs font-semibold text-slate-800 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="popular">Phổ biến nhất</option>
                <option value="price_asc">Giá: Thấp đến Cao</option>
                <option value="price_desc">Giá: Cao đến Thấp</option>
                <option value="rating">Đánh giá cao nhất</option>
              </select>
            </div>
          </div>

          {/* Cards List */}
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  className="h-56 bg-white rounded-3xl border border-slate-200 animate-pulse"
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
                onClick={() => fetchHotels()}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
              >
                <RefreshCw className="w-4 h-4" />
                Thử lại
              </button>
            </div>
          ) : filteredHotels.length === 0 ? (
            <div className="text-center py-20 bg-white rounded-3xl border border-slate-200 p-8 space-y-4">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                <SearchX className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">
                Không tìm thấy khách sạn phù hợp với bộ lọc
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Hãy thử nới rộng khoảng giá hoặc bỏ chọn một số hạng sao để khám phá thêm nhiều lựa chọn nghỉ dưỡng hấp dẫn khác.
              </p>
              <button
                onClick={() => {
                  setSelectedStars([]);
                  setSelectedPriceRange("all");
                }}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-bold text-xs shadow-md shadow-indigo-600/20 hover:bg-indigo-700 transition-all"
              >
                Xóa bộ lọc & Xem lại
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredHotels.map((hotel) => (
                <HotelCard
                  key={hotel.id_khach_san}
                  hotel={hotel}
                  checkIn={checkIn}
                  checkOut={checkOut}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-400">
          Đang tải kết quả tìm kiếm...
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
