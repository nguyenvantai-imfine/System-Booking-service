"use client";

import React, { useEffect, useState, use, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api";
import { formatVND, getTodayDateString, calculateNights } from "@/lib/utils";
import {
  Star,
  MapPin,
  Wifi,
  Waves,
  Utensils,
  Sparkles,
  ShieldCheck,
  Clock,
  Maximize2,
  Users,
  Bed,
  CheckCircle2,
  Calendar,
  ChevronRight,
  ArrowLeft,
  Share2,
  Heart,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

function HotelDetailContent({ hotelId }: { hotelId: number }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const checkIn = searchParams.get("check_in") || getTodayDateString(0);
  const checkOut = searchParams.get("check_out") || getTodayDateString(1);
  const nights = calculateNights(checkIn, checkOut);

  const [hotel, setHotel] = useState<any>(null);
  const [roomTypes, setRoomTypes] = useState<any[]>([]);
  const [availableRooms, setAvailableRooms] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [bookingWarning, setBookingWarning] = useState("");
  const [selectedRoomType, setSelectedRoomType] = useState<any>(null);

  const fetchHotelDetail = async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      // 1. Fetch Hotel info
      let hotelData: any = null;
      try {
        hotelData = await apiClient.getHotelById(hotelId);
      } catch (err: any) {
        if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
          hotelData = {
            id_khach_san: hotelId,
            ten_khach_san: "Test JWT Grand Hotel (Demo)",
            dia_chi: "123 Võ Nguyên Giáp",
            quan_huyen: "Sơn Trà",
            thanh_pho: "Đà Nẵng",
            so_sao: 5,
            mo_ta:
              "Khách sạn nghỉ dưỡng 5 sao sang trọng tọa lạc tại bãi biển Mỹ Khê, Đà Nẵng. Sở hữu vị trí đắc địa với tầm nhìn toàn cảnh biển Đông ngoạn mục, hồ bơi chân mây tầng thượng, chuỗi nhà hàng cao cấp và dịch vụ spa chăm sóc sức khỏe chuẩn quốc tế.",
            hinh_anh: [],
            tien_nghi: [],
            quy_tac: [],
          };
        } else {
          throw err;
        }
      }
      setHotel(hotelData);

      // 2. Fetch Room Types for this hotel
      try {
        const types = await apiClient.getRoomTypesByHotel(hotelId);
        if (types && types.length > 0) {
          setRoomTypes(types);
          setSelectedRoomType(types[0]);
        } else {
          if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
            setRoomTypes([
              {
                id_loai_phong: 4,
                ten_loai_phong: "Premier Oceanfront Suite",
                mo_ta: "Phòng Suite cao cấp nhìn thẳng ra biển Mỹ Khê, ban công riêng đón bình minh.",
                suc_chua_nguoi_lon: 2,
                suc_chua_tre_em: 1,
                dien_tich_m2: 45,
                gia_co_ban_mot_dem: 1800000,
                tien_ich: [
                  { ten_tien_ich: "Ban công view biển" },
                  { ten_tien_ich: "Bồn tắm Jacuzzi" },
                  { ten_tien_ich: "Bữa sáng buffet miễn phí" },
                ],
              },
            ]);
            setSelectedRoomType({
              id_loai_phong: 4,
              ten_loai_phong: "Premier Oceanfront Suite",
              gia_co_ban_mot_dem: 1800000,
            });
          } else {
            setRoomTypes([]);
          }
        }
      } catch (e) {
        console.warn("Could not fetch room types:", e);
        setRoomTypes([]);
      }

      // 3. Fetch Available physical rooms
      try {
        const rooms = await apiClient.getAvailableRooms({
          hotel_id: hotelId,
          check_in: checkIn,
          check_out: checkOut,
        });
        setAvailableRooms(rooms || []);
      } catch (e) {
        console.warn("Could not fetch available rooms:", e);
        setAvailableRooms([]);
      }
    } catch (err: any) {
      console.error("Error loading hotel details:", err);
      setErrorMessage("Không thể kết nối đến máy chủ. Vui lòng thử lại sau.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHotelDetail();
  }, [hotelId, checkIn, checkOut]);

  const hotelImages = [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1400&q=85",
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80",
  ];

  const handleBookNow = (roomType: any) => {
    setBookingWarning("");
    // Find matching physical room ID if available
    const matchingRoom = availableRooms.find(
      (r) => r.id_loai_phong === roomType.id_loai_phong
    );
    if (!matchingRoom) {
      setBookingWarning(
        `Loại phòng "${roomType.ten_loai_phong}" hiện không còn phòng trống trong khoảng thời gian ${checkIn} đến ${checkOut}. Vui lòng chọn ngày khác hoặc loại phòng khác!`
      );
      return;
    }
    const roomId = matchingRoom.id_phong;

    const query = new URLSearchParams({
      hotel_id: hotelId.toString(),
      hotel_name: hotel?.ten_khach_san || "",
      room_type_id: roomType.id_loai_phong.toString(),
      room_type_name: roomType.ten_loai_phong,
      room_id: roomId.toString(),
      room_number: matchingRoom?.so_phong || `P.${roomId}`,
      price_per_night: roomType.gia_co_ban_mot_dem.toString(),
      check_in: checkIn,
      check_out: checkOut,
      nights: nights.toString(),
    });

    router.push(`/booking/checkout?${query.toString()}`);
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <div className="inline-block w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-slate-500 font-medium">Đang tải thông tin khách sạn & phòng trống...</p>
      </div>
    );
  }

  if (errorMessage || !hotel) {
    return (
      <div className="max-w-2xl mx-auto my-20 p-8 rounded-3xl bg-white border border-rose-200 text-center space-y-4 shadow-sm">
        <div className="w-16 h-16 rounded-full bg-rose-50 flex items-center justify-center mx-auto text-rose-500">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Không thể kết nối đến máy chủ</h2>
        <p className="text-sm text-slate-500">
          {errorMessage || "Không thể kết nối đến máy chủ. Vui lòng thử lại sau."}
        </p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => fetchHotelDetail()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md transition-all hover:scale-105"
          >
            <RefreshCw className="w-4 h-4" />
            Thử lại
          </button>
          <Link
            href="/search"
            className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-colors"
          >
            Quay lại danh sách
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Link href="/" className="hover:text-indigo-600">Trang chủ</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <Link href={`/search?city=${hotel?.thanh_pho || ""}`} className="hover:text-indigo-600">
            {hotel?.thanh_pho || "Việt Nam"}
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-slate-900 line-clamp-1">{hotel?.ten_khach_san}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({ title: hotel?.ten_khach_san, url: window.location.href });
              } else {
                navigator.clipboard.writeText(window.location.href);
                alert("Đã sao chép liên kết khách sạn!");
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <Share2 className="w-3.5 h-3.5" />
            Chia sẻ
          </button>
          <button
            onClick={() => alert("Đã lưu vào danh sách yêu thích!")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-rose-600 hover:bg-rose-50 transition-colors"
          >
            <Heart className="w-3.5 h-3.5" />
            Lưu
          </button>
        </div>
      </div>

      {bookingWarning && (
        <div className="flex items-center gap-2.5 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-sm font-semibold">
          <AlertCircle className="w-5 h-5 shrink-0 text-amber-600" />
          <span>{bookingWarning}</span>
        </div>
      )}

      {/* Hotel Title & Header Overview */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
              {hotel?.ten_khach_san}
            </h1>
            <div className="flex items-center gap-0.5 px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 text-xs font-bold">
              <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
              <span>{hotel?.so_sao || 5} Sao</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs sm:text-sm text-slate-600">
            <MapPin className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>
              {[hotel?.dia_chi, hotel?.quan_huyen, hotel?.thanh_pho].filter(Boolean).join(", ")}
            </span>
          </div>
        </div>

        {/* Rating Score Badge */}
        <div className="flex items-center gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs shrink-0">
          <div className="text-right">
            <p className="text-sm font-extrabold text-slate-900">Xuất sắc</p>
            <p className="text-xs text-slate-500">128 khách đã đánh giá</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-600 text-white font-black text-lg flex items-center justify-center shadow-md shadow-indigo-600/30">
            9.4
          </div>
        </div>
      </div>

      {/* PHOTO GALLERY (Airbnb Style 5-photo grid) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 h-[380px] sm:h-[460px] rounded-3xl overflow-hidden shadow-lg">
        {/* Main Big Photo */}
        <div className="md:col-span-2 h-full relative overflow-hidden group cursor-pointer">
          <img
            src={hotelImages[0]}
            alt="Hotel main"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
        </div>

        {/* Secondary Photos */}
        <div className="hidden md:grid col-span-2 grid-cols-2 gap-3 h-full">
          {hotelImages.slice(1, 5).map((img, idx) => (
            <div key={idx} className="relative h-full overflow-hidden group cursor-pointer">
              <img
                src={img}
                alt={`Hotel view ${idx + 1}`}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Booking Date Bar Info */}
      <div className="bg-gradient-to-r from-indigo-50 via-sky-50 to-indigo-50 border border-indigo-100 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Calendar className="w-5 h-5 text-indigo-600" />
          <span className="text-xs sm:text-sm font-semibold text-slate-800">
            Ngày lưu trú: <strong className="text-indigo-900">{checkIn}</strong> ➔ <strong className="text-indigo-900">{checkOut}</strong> ({nights} đêm)
          </span>
        </div>
        <Link
          href={`/search?city=${encodeURIComponent(hotel?.thanh_pho || "")}&check_in=${checkIn}&check_out=${checkOut}`}
          className="text-xs font-bold text-indigo-600 hover:text-indigo-800 hover:underline"
        >
          Thay đổi ngày đặt phòng
        </Link>
      </div>

      {/* Main Details & Room Types Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left Column: Description & Room Types */}
        <div className="lg:col-span-8 space-y-10">
          {/* Overview Description */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Giới thiệu khách sạn</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              {hotel?.mo_ta ||
                "Trải nghiệm kỳ nghỉ hoàn mỹ tại khách sạn chuẩn 5 sao với tầm nhìn toàn cảnh biển Đông ngoạn mục. Mỗi phòng nghỉ được thiết kế tinh tế theo phong cách kiến trúc hiện đại, trang bị đầy đủ tiện nghi đẳng cấp và ban công riêng biệt để bạn đón trọn làn gió biển mát lành."}
            </p>

            {/* Hotel Highlights */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-100">
              <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                <Waves className="w-4 h-4 text-sky-500" /> Bể bơi vô cực
              </div>
              <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                <Wifi className="w-4 h-4 text-indigo-500" /> Wifi tốc độ cao
              </div>
              <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                <Utensils className="w-4 h-4 text-amber-500" /> Buffet Á - Âu
              </div>
              <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                <Sparkles className="w-4 h-4 text-emerald-500" /> Trung tâm Spa
              </div>
            </div>
          </div>

          {/* ROOM TYPES LIST (Hạng phòng còn trống) */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-extrabold text-slate-900">
                  Các hạng phòng còn trống
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Giá đã bao gồm bữa sáng buffet và thuế phí dịch vụ
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                ✓ Sẵn sàng nhận khách
              </span>
            </div>

            <div className="space-y-6">
              {roomTypes.map((type, index) => {
                const roomImages = [
                  "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
                  "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80",
                  "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80",
                ];
                const roomCover = roomImages[index % roomImages.length];

                return (
                  <div
                    key={type.id_loai_phong}
                    className="bg-white rounded-3xl border border-slate-200/90 overflow-hidden shadow-xs hover:shadow-lg transition-all p-5 sm:p-6"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                      {/* Room Photo */}
                      <div className="md:col-span-5 relative h-52 md:h-auto rounded-2xl overflow-hidden bg-slate-100">
                        <img
                          src={roomCover}
                          alt={type.ten_loai_phong}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-black/60 text-white text-[11px] font-medium">
                          {type.dien_tich_m2 || 40} m²
                        </div>
                      </div>

                      {/* Room Details */}
                      <div className="md:col-span-7 flex flex-col justify-between space-y-4">
                        <div>
                          <h4 className="text-lg font-extrabold text-slate-900">
                            {type.ten_loai_phong}
                          </h4>
                          <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                            {type.mo_ta || "Phòng nghỉ hiện đại với cửa sổ kính chạm trần, nội thất cao cấp mang lại cảm giác thư thái tối đa."}
                          </p>

                          {/* Room Specs */}
                          <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-slate-700 mt-3 pt-3 border-t border-slate-100">
                            <span className="flex items-center gap-1.5">
                              <Users className="w-4 h-4 text-slate-400" />
                              {type.suc_chua_nguoi_lon || 2} Người lớn
                              {type.suc_chua_tre_em ? `, ${type.suc_chua_tre_em} Trẻ em` : ""}
                            </span>
                            <span className="flex items-center gap-1.5">
                              <Bed className="w-4 h-4 text-slate-400" /> 1 Giường đôi lớn
                            </span>
                            <span className="flex items-center gap-1.5">
                              <Maximize2 className="w-4 h-4 text-slate-400" /> {type.dien_tich_m2 || 40} m²
                            </span>
                          </div>

                          {/* Room Amenities */}
                          <div className="flex flex-wrap gap-1.5 mt-3">
                            <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium">
                              ✓ Ban công view đẹp
                            </span>
                            <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium">
                              ✓ Bồn tắm Jacuzzi
                            </span>
                            <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium">
                              ✓ Bữa sáng miễn phí
                            </span>
                          </div>
                        </div>

                        {/* Price & Booking Button */}
                        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                          <div>
                            <p className="text-[11px] text-slate-400">Giá 1 đêm từ</p>
                            <p className="text-xl font-black text-indigo-700">
                              {formatVND(type.gia_co_ban_mot_dem)}
                            </p>
                          </div>

                          <button
                            onClick={() => handleBookNow(type)}
                            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-md shadow-indigo-600/25 hover:scale-105 active:scale-95 transition-all"
                          >
                            Chọn phòng & Đặt ngay
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Policies & Quick Info Card */}
        <div className="lg:col-span-4 space-y-6">
          {/* Hotel Policies Card */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <h4 className="text-base font-bold text-slate-900">Chính sách nhận / trả phòng</h4>
            <div className="space-y-3 text-xs text-slate-600">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="font-semibold text-slate-700">Giờ nhận phòng (Check-in)</span>
                <span className="font-extrabold text-indigo-600">Từ 14:00</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="font-semibold text-slate-700">Giờ trả phòng (Check-out)</span>
                <span className="font-extrabold text-indigo-600">Trước 12:00</span>
              </div>
              <div className="space-y-1.5 pt-2">
                <p className="flex items-center gap-1.5 text-slate-700 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Xuất trình CMND/CCCD hoặc Hộ chiếu khi check-in
                </p>
                <p className="flex items-center gap-1.5 text-slate-700 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Check-in nhanh bằng mã QR Code trên vé điện tử
                </p>
                <p className="flex items-center gap-1.5 text-slate-700 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Hỗ trợ giữ hành lý miễn phí trước và sau khi lưu trú
                </p>
              </div>
            </div>
          </div>

          {/* Need Assistance Card */}
          <div className="bg-gradient-to-br from-indigo-900 to-indigo-950 text-white rounded-3xl p-6 shadow-xl space-y-3">
            <h4 className="text-base font-bold">Cần tư vấn đặt phòng?</h4>
            <p className="text-xs text-indigo-200 leading-relaxed">
              Chuyên viên khách sạn sẵn sàng hỗ trợ bạn chọn phòng ưng ý với mức giá tốt nhất.
            </p>
            <div className="pt-2">
              <a
                href="tel:19008888"
                className="w-full inline-flex items-center justify-center py-2.5 rounded-xl bg-amber-400 text-slate-950 font-bold text-xs hover:bg-amber-300 transition-colors"
              >
                Gọi Hotline: 1900 8888
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HotelDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const hotelId = parseInt(id, 10);

  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-400">
          Đang tải thông tin khách sạn & phòng trống...
        </div>
      }
    >
      <HotelDetailContent hotelId={hotelId} />
    </Suspense>
  );
}

