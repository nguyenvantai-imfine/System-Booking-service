"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  MapPin,
  Calendar,
  Users,
  Search,
  ChevronDown,
  Plus,
  Minus,
} from "lucide-react";
import { getTodayDateString } from "@/lib/utils";

interface SearchBarProps {
  initialCity?: string;
  initialCheckIn?: string;
  initialCheckOut?: string;
  initialAdults?: number;
  initialChildren?: number;
  initialRooms?: number;
  compact?: boolean;
}

export function SearchBar({
  initialCity = "",
  initialCheckIn = "",
  initialCheckOut = "",
  initialAdults = 2,
  initialChildren = 0,
  initialRooms = 1,
  compact = false,
}: SearchBarProps) {
  const router = useRouter();

  const [city, setCity] = useState(initialCity);
  const [checkIn, setCheckIn] = useState(
    initialCheckIn || getTodayDateString(0)
  );
  const [checkOut, setCheckOut] = useState(
    initialCheckOut || getTodayDateString(1)
  );
  const [adults, setAdults] = useState(initialAdults);
  const [children, setChildren] = useState(initialChildren);
  const [rooms, setRooms] = useState(initialRooms);

  const [showGuestPopover, setShowGuestPopover] = useState(false);
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);

  const popularDestinations = [
    "Đà Nẵng",
    "Hà Nội",
    "TP. Hồ Chí Minh",
    "Phú Quốc",
    "Nha Trang",
    "Đà Lạt",
    "Vũng Tàu",
    "Sa Pa",
  ];

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowGuestPopover(false);
    setShowCitySuggestions(false);

    const query = new URLSearchParams();
    if (city.trim()) query.set("city", city.trim());
    if (checkIn) query.set("check_in", checkIn);
    if (checkOut) query.set("check_out", checkOut);
    if (adults) query.set("adults", adults.toString());
    if (children) query.set("children", children.toString());
    if (rooms) query.set("rooms", rooms.toString());

    router.push(`/search?${query.toString()}`);
  };

  return (
    <form
      onSubmit={handleSearchSubmit}
      className={`w-full bg-white rounded-2xl md:rounded-3xl shadow-xl shadow-indigo-900/10 border border-slate-200/80 p-2 sm:p-3 relative z-30 ${
        compact ? "py-2" : "py-3 md:py-4"
      }`}
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-3 items-center">
        {/* Destination Input */}
        <div className="md:col-span-4 relative">
          <div
            onClick={() => setShowCitySuggestions(true)}
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 cursor-pointer border border-transparent focus-within:border-indigo-500 focus-within:bg-indigo-50/30 transition-all"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
              <MapPin className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Điểm đến / Khách sạn
              </label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                onFocus={() => setShowCitySuggestions(true)}
                placeholder="Ví dụ: Đà Nẵng, Hà Nội..."
                className="w-full text-sm font-semibold text-slate-900 placeholder-slate-400 focus:outline-none bg-transparent truncate"
              />
            </div>
          </div>

          {/* Quick Destination Dropdown */}
          {showCitySuggestions && (
            <div
              className="absolute left-0 top-full mt-2 w-72 rounded-2xl bg-white border border-slate-200 shadow-2xl p-3 z-50 animate-in fade-in-50 duration-150"
              onMouseLeave={() => setShowCitySuggestions(false)}
            >
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider px-2 py-1">
                Điểm đến phổ biến
              </p>
              <div className="grid grid-cols-2 gap-1.5 mt-1">
                {popularDestinations.map((dest) => (
                  <button
                    key={dest}
                    type="button"
                    onClick={() => {
                      setCity(dest);
                      setShowCitySuggestions(false);
                    }}
                    className="flex items-center gap-1.5 px-2.5 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 text-left transition-colors"
                  >
                    <MapPin className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                    <span className="truncate">{dest}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Date Range Inputs */}
        <div className="md:col-span-4 grid grid-cols-2 gap-2 border-y md:border-y-0 md:border-x border-slate-100 py-1 md:py-0 md:px-2">
          {/* Check-in */}
          <div className="flex items-center gap-2.5 px-2.5 py-2 rounded-xl hover:bg-slate-50 cursor-pointer">
            <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center shrink-0">
              <Calendar className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Nhận phòng
              </label>
              <input
                type="date"
                required
                value={checkIn}
                min={getTodayDateString(0)}
                onChange={(e) => {
                  setCheckIn(e.target.value);
                  if (e.target.value >= checkOut) {
                    const next = new Date(e.target.value);
                    next.setDate(next.getDate() + 1);
                    setCheckOut(next.toISOString().split("T")[0]);
                  }
                }}
                className="w-full text-xs font-bold text-slate-900 focus:outline-none bg-transparent"
              />
            </div>
          </div>

          {/* Check-out */}
          <div className="flex items-center gap-2.5 px-2.5 py-2 rounded-xl hover:bg-slate-50 cursor-pointer">
            <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center shrink-0">
              <Calendar className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Trả phòng
              </label>
              <input
                type="date"
                required
                value={checkOut}
                min={checkIn || getTodayDateString(1)}
                onChange={(e) => setCheckOut(e.target.value)}
                className="w-full text-xs font-bold text-slate-900 focus:outline-none bg-transparent"
              />
            </div>
          </div>
        </div>

        {/* Guests & Room Popover */}
        <div className="md:col-span-3 relative">
          <div
            onClick={() => setShowGuestPopover(!showGuestPopover)}
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
              <Users className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Số khách & Phòng
              </label>
              <p className="text-xs font-bold text-slate-900 truncate">
                {adults} Người lớn{children > 0 ? `, ${children} Trẻ em` : ""}, {rooms} Phòng
              </p>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
          </div>

          {/* Guest Selector Popover */}
          {showGuestPopover && (
            <div
              className="absolute right-0 top-full mt-2 w-72 rounded-2xl bg-white border border-slate-200 shadow-2xl p-4 z-50 space-y-4 animate-in fade-in-50 duration-150"
              onMouseLeave={() => setShowGuestPopover(false)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-slate-800">Người lớn</p>
                  <p className="text-xs text-slate-400">Từ 12 tuổi trở lên</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    disabled={adults <= 1}
                    onClick={() => setAdults(adults - 1)}
                    className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-sm font-bold w-4 text-center">{adults}</span>
                  <button
                    type="button"
                    disabled={adults >= 10}
                    onClick={() => setAdults(adults + 1)}
                    className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div>
                  <p className="text-sm font-bold text-slate-800">Trẻ em</p>
                  <p className="text-xs text-slate-400">Dưới 12 tuổi</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    disabled={children <= 0}
                    onClick={() => setChildren(children - 1)}
                    className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-sm font-bold w-4 text-center">{children}</span>
                  <button
                    type="button"
                    disabled={children >= 6}
                    onClick={() => setChildren(children + 1)}
                    className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div>
                  <p className="text-sm font-bold text-slate-800">Số phòng</p>
                  <p className="text-xs text-slate-400">Số lượng phòng cần đặt</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    disabled={rooms <= 1}
                    onClick={() => setRooms(rooms - 1)}
                    className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-sm font-bold w-4 text-center">{rooms}</span>
                  <button
                    type="button"
                    disabled={rooms >= 5}
                    onClick={() => setRooms(rooms + 1)}
                    className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setShowGuestPopover(false)}
                className="w-full py-2 bg-indigo-50 text-indigo-700 rounded-xl font-bold text-xs hover:bg-indigo-100 transition-colors"
              >
                Xác nhận
              </button>
            </div>
          )}
        </div>

        {/* Submit Search Button */}
        <div className="md:col-span-1 flex justify-center">
          <button
            type="submit"
            className="w-full md:w-14 h-12 md:h-14 rounded-xl md:rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center shadow-lg shadow-indigo-600/30 hover:scale-105 active:scale-95 transition-all font-bold gap-2 md:gap-0"
          >
            <Search className="w-5 h-5" />
            <span className="md:hidden text-sm">Tìm kiếm</span>
          </button>
        </div>
      </div>
    </form>
  );
}
