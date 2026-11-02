"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Users,
  Building2,
  Bed,
  Calendar,
  DollarSign,
  Clock,
  CheckCircle,
  XCircle,
  TrendingUp,
  UserCheck,
  Shield,
  Briefcase,
  RefreshCw,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { apiClient } from "@/lib/api";

interface StatCard {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  source: string;
}

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
];

const formatVND = (amount: number) => {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(amount);
};

export default function AdminDashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [unavailableServices, setUnavailableServices] = useState<string[]>([]);
  const [bookingStatusesIncomplete, setBookingStatusesIncomplete] = useState(false);

  // Dữ liệu thống kê thời gian thực
  const [statsData, setStatsData] = useState({
    totalUsers: 0,
    totalCustomers: 0,
    totalPartners: 0,
    totalAdmins: 0,
    totalHotels: 0,
    totalRooms: 0,
    totalBookings: 0,
    pendingBookings: 0,
    confirmedBookings: 0,
    completedBookings: 0,
    cancelledBookings: 0,
    totalRevenue: 0,
    todayRevenue: 0,
    monthRevenue: null as number | null,
  });

  const [bookingStatusChart, setBookingStatusChart] = useState<any[]>([]);

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setUnavailableServices([]);
    setBookingStatusesIncomplete(false);
    const failedServices: string[] = [];
    try {
      // 1. Lấy dữ liệu Người dùng từ user-service
      let usersList: any[] = [];
      let totalUsers = 0;
      let totalCustomers = 0;
      let totalPartners = 0;
      let totalAdmins = 0;

      try {
        const usersRes = await apiClient.getAdminUsers({ page: 1, page_size: 100 });
        usersList = usersRes.items || [];
        totalUsers = usersRes.total || usersList.length;
        totalCustomers = usersList.filter((u: any) => u.vai_tro === "CUSTOMER").length;
        totalPartners = usersList.filter((u: any) => u.vai_tro === "PARTNER").length;
        totalAdmins = usersList.filter((u: any) => u.vai_tro === "ADMIN").length;
      } catch (e) {
        console.warn("Không thể tải người dùng:", e);
        failedServices.push("User");
      }

      // 2. Lấy dữ liệu Khách sạn từ hotel-service
      let totalHotels = 0;
      try {
        const hotelsRes = await apiClient.getHotels({ page: 1, page_size: 50 });
        totalHotels = hotelsRes.total ?? hotelsRes.items.length;
      } catch (e) {
        console.warn("Không thể tải khách sạn:", e);
        failedServices.push("Hotel");
      }

      // 3. Lấy dữ liệu Phòng từ room-service
      let totalRooms = 0;
      try {
        const roomsRes = await apiClient.getRooms({ page: 1, page_size: 100 });
        totalRooms = roomsRes.total || (roomsRes.items || []).length;
      } catch (e) {
        console.warn("Không thể tải phòng:", e);
        failedServices.push("Room");
      }

      // 4. Lấy dữ liệu Đơn đặt phòng từ booking-service
      let totalBookings = 0;
      let pendingBookings = 0;
      let confirmedBookings = 0;
      let completedBookings = 0;
      let cancelledBookings = 0;
      let bookingsList: any[] = [];

      try {
        const bookingsRes = await apiClient.getBookings({ page: 1, page_size: 100 });
        bookingsList = bookingsRes.items || [];
        totalBookings = bookingsRes.total ?? bookingsList.length;
        if (totalBookings > bookingsList.length) {
          setBookingStatusesIncomplete(true);
        }

        pendingBookings = bookingsList.filter(
          (b: any) => b.trang_thai === "PENDING_PAYMENT"
        ).length;
        confirmedBookings = bookingsList.filter(
          (b: any) => b.trang_thai === "CONFIRMED"
        ).length;
        completedBookings = bookingsList.filter(
          (b: any) => b.trang_thai === "COMPLETED"
        ).length;
        cancelledBookings = bookingsList.filter(
          (b: any) => b.trang_thai === "CANCELLED"
        ).length;
      } catch (e) {
        console.warn("Không thể tải đơn đặt:", e);
        failedServices.push("Booking");
      }

      // 5. Lấy dữ liệu Doanh thu từ payment-service
      let totalRevenue = 0;
      let todayRevenue = 0;
      let monthRevenue: number | null = null;

      try {
        const paymentStats: any = await apiClient.getPaymentStats();
        totalRevenue =
          paymentStats.total_revenue ||
          paymentStats.tong_doanh_thu ||
          0;

        // Lấy doanh thu hôm nay thực tế từ backend stats API
        todayRevenue =
          paymentStats.today_revenue ??
          paymentStats.doanh_thu_hom_nay ??
          0;
      } catch (e) {
        console.warn("Không thể tải doanh thu:", e);
        failedServices.push("Payment");
      }
      setUnavailableServices(failedServices);

      // Cập nhật State tổng thể
      setStatsData({
        totalUsers,
        totalCustomers,
        totalPartners,
        totalAdmins,
        totalHotels,
        totalRooms,
        totalBookings,
        pendingBookings,
        confirmedBookings,
        completedBookings,
        cancelledBookings,
        totalRevenue,
        todayRevenue,
        monthRevenue,
      });

      // Tạo dữ liệu biểu đồ trạng thái booking
      const statusChart = [
        { name: "Đã xác nhận", value: confirmedBookings },
        { name: "Chờ thanh toán", value: pendingBookings },
        { name: "Đã hoàn thành", value: completedBookings },
        { name: "Đã hủy", value: cancelledBookings },
      ].filter((item) => item.value > 0);
      setBookingStatusChart(statusChart);

      setLastUpdated(new Date().toLocaleTimeString("vi-VN"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const cards: StatCard[] = [
    {
      title: "Tổng số người dùng",
      value: statsData.totalUsers,
      icon: Users,
      color: "bg-blue-500",
      source: "User",
    },
    {
      title: "Tổng số khách hàng",
      value: statsData.totalCustomers,
      icon: UserCheck,
      color: "bg-green-500",
      source: "User",
    },
    {
      title: "Tổng số Partner",
      value: statsData.totalPartners,
      icon: Briefcase,
      color: "bg-purple-500",
      source: "User",
    },
    {
      title: "Tổng số Admin",
      value: statsData.totalAdmins,
      icon: Shield,
      color: "bg-red-500",
      source: "User",
    },
    {
      title: "Tổng số khách sạn",
      value: statsData.totalHotels,
      icon: Building2,
      color: "bg-orange-500",
      source: "Hotel",
    },
    {
      title: "Tổng số phòng",
      value: statsData.totalRooms,
      icon: Bed,
      color: "bg-teal-500",
      source: "Room",
    },
    {
      title: "Tổng số booking",
      value: statsData.totalBookings,
      icon: Calendar,
      color: "bg-indigo-500",
      source: "Booking",
    },
    {
      title: "Booking đang chờ xác nhận",
      value: statsData.pendingBookings,
      icon: Clock,
      color: "bg-yellow-500",
      source: "Booking statuses",
    },
    {
      title: "Booking đã xác nhận",
      value: statsData.confirmedBookings,
      icon: CheckCircle,
      color: "bg-emerald-500",
      source: "Booking statuses",
    },
    {
      title: "Booking đã hoàn thành",
      value: statsData.completedBookings,
      icon: CheckCircle,
      color: "bg-cyan-500",
      source: "Booking statuses",
    },
    {
      title: "Booking đã hủy",
      value: statsData.cancelledBookings,
      icon: XCircle,
      color: "bg-rose-500",
      source: "Booking statuses",
    },
    {
      title: "Tổng doanh thu",
      value: formatVND(statsData.totalRevenue),
      icon: DollarSign,
      color: "bg-amber-500",
      source: "Payment",
    },
    {
      title: "Doanh thu hôm nay",
      value: formatVND(statsData.todayRevenue),
      icon: TrendingUp,
      color: "bg-lime-500",
      source: "Payment",
    },
    {
      title: "Doanh thu tháng này",
      value: statsData.monthRevenue === null ? "API chưa cung cấp" : formatVND(statsData.monthRevenue),
      icon: TrendingUp,
      color: "bg-sky-500",
      source: "Payment",
    },
  ];

  return (
    <div className="p-6">
      {/* Tiêu đề & Nút làm mới */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Tổng quan Hệ thống (Admin Overview)
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Dữ liệu tổng hợp từ 6 Microservices: User, Hotel, Room, Booking, Payment, Notification.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-gray-400">
              Cập nhật lúc: {lastUpdated}
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            disabled={isLoading}
            className="flex items-center gap-2 px-3.5 py-2 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 shadow-sm transition disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoading ? "animate-spin text-blue-600" : ""}`}
            />
            <span>{isLoading ? "Đang tải..." : "Làm mới dữ liệu"}</span>
          </button>
        </div>
      </div>

      {(unavailableServices.length > 0 || bookingStatusesIncomplete) && (
        <div
          role="alert"
          className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        >
          {unavailableServices.length > 0 &&
            `Không tải được dữ liệu từ: ${unavailableServices.join(", ")}. Các chỉ số liên quan được hiển thị bằng dấu —.`}
          {bookingStatusesIncomplete &&
            " Danh sách booking được phân trang nên các tổng theo trạng thái chỉ tải một phần."}
        </div>
      )}

      {/* Grid 14 Thẻ Thống Kê */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        {cards.map((stat, index) => {
          const Icon = stat.icon;
          const value = isLoading
            ? "…"
            : unavailableServices.includes(stat.source) ||
                (stat.source === "Booking statuses" &&
                  (unavailableServices.includes("Booking") || bookingStatusesIncomplete))
            ? "—"
            : stat.value;
          return (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0 pr-3">
                  <p className="text-xs font-medium text-gray-500 mb-1 truncate">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 tracking-tight">
                    {typeof value === "number" ? value.toLocaleString() : value}
                  </p>
                </div>
                <div
                  className={`p-3 rounded-xl ${stat.color} bg-opacity-10 flex-shrink-0`}
                >
                  <Icon
                    className={`w-6 h-6 ${stat.color.replace("bg-", "text-")}`}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Biểu đồ Phân tích */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Doanh thu theo thời gian */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Doanh thu tuần này (VND)
          </h3>
          <p className="flex h-[280px] items-center justify-center text-sm text-gray-500">
            API hiện chưa cung cấp dữ liệu doanh thu theo ngày.
          </p>
        </div>

        {/* Số lượng booking theo ngày */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Số lượng đơn đặt theo ngày
          </h3>
          <p className="flex h-[280px] items-center justify-center text-sm text-gray-500">
            API hiện chưa cung cấp thống kê booking theo ngày.
          </p>
        </div>

        {/* Booking theo trạng thái */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Phân bổ Booking theo Trạng thái
          </h3>
          {unavailableServices.includes("Booking") || bookingStatusesIncomplete ? (
            <p className="flex h-[280px] items-center justify-center text-sm text-gray-500">
              Không thể tải thống kê booking.
            </p>
          ) : bookingStatusChart.length === 0 ? (
            <p className="flex h-[280px] items-center justify-center text-sm text-gray-500">
              Chưa có dữ liệu booking để thống kê.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={bookingStatusChart}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, percent }) =>
                    `${name}: ${((percent || 0) * 100).toFixed(0)}%`
                  }
                  outerRadius={85}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {bookingStatusChart.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Doanh thu theo khách sạn */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Doanh thu theo Khách sạn
          </h3>
          <p className="flex h-[280px] items-center justify-center text-sm text-gray-500">
            API hiện chưa cung cấp doanh thu theo khách sạn.
          </p>
        </div>
      </div>
    </div>
  );
}
