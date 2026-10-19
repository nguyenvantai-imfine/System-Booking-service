"use client";

import { useState } from "react";
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
  ChevronDown,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface StatCard {
  title: string;
  value: number;
  icon: React.ElementType;
  color: string;
}

const stats: StatCard[] = [
  { title: "Tổng số người dùng", value: 0, icon: Users, color: "bg-blue-500" },
  {
    title: "Tổng số khách hàng",
    value: 0,
    icon: UserCheck,
    color: "bg-green-500",
  },
  {
    title: "Tổng số Partner",
    value: 0,
    icon: Briefcase,
    color: "bg-purple-500",
  },
  { title: "Tổng số Admin", value: 0, icon: Shield, color: "bg-red-500" },
  {
    title: "Tổng số khách sạn",
    value: 0,
    icon: Building2,
    color: "bg-orange-500",
  },
  { title: "Tổng số phòng", value: 0, icon: Bed, color: "bg-teal-500" },
  {
    title: "Tổng số booking",
    value: 0,
    icon: Calendar,
    color: "bg-indigo-500",
  },
  {
    title: "Booking đang chờ xác nhận",
    value: 0,
    icon: Clock,
    color: "bg-yellow-500",
  },
  {
    title: "Booking đã xác nhận",
    value: 0,
    icon: CheckCircle,
    color: "bg-emerald-500",
  },
  {
    title: "Booking đã hoàn thành",
    value: 0,
    icon: CheckCircle,
    color: "bg-cyan-500",
  },
  { title: "Booking đã hủy", value: 0, icon: XCircle, color: "bg-rose-500" },
  {
    title: "Tổng doanh thu",
    value: 0,
    icon: DollarSign,
    color: "bg-amber-500",
  },
  {
    title: "Doanh thu hôm nay",
    value: 0,
    icon: TrendingUp,
    color: "bg-lime-500",
  },
  {
    title: "Doanh thu tháng này",
    value: 0,
    icon: TrendingUp,
    color: "bg-sky-500",
  },
];

const revenueData = [1];
const bookingTimeData = [];
const bookingStatusData = [];
const hotelRevenueData = [];
const topHotelsData = [];
const topRoomTypesData = [];

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
];

export default function AdminDashboardPage() {
  const [revenueStartDate, setRevenueStartDate] = useState<string>("");
  const [revenueEndDate, setRevenueEndDate] = useState<string>("");
  const [bookingStartDate, setBookingStartDate] = useState<string>("");
  const [bookingEndDate, setBookingEndDate] = useState<string>("");

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 mb-1">
                    {stat.title}
                  </p>
                  <p className="text-3xl font-bold text-gray-900">
                    {stat.value.toLocaleString()}
                  </p>
                </div>
                <div
                  className={`p-3 rounded-lg ${stat.color} bg-opacity-10 flex-shrink-0`}
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

      {/* Biểu đồ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Doanh thu theo ngày/tháng */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
            <h3 className="text-lg font-semibold text-gray-900">
              Doanh thu theo thời gian
            </h3>
            <div className="flex items-center gap-2">
              <input
                type="datetime-local"
                value={revenueStartDate}
                onChange={(e) => setRevenueStartDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-gray-500">đến</span>
              <input
                type="datetime-local"
                value={revenueEndDate}
                onChange={(e) => setRevenueEndDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Số lượng booking theo thời gian */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
            <h3 className="text-lg font-semibold text-gray-900">
              Số lượng booking theo thời gian
            </h3>
            <div className="flex items-center gap-2">
              <input
                type="datetime-local"
                value={bookingStartDate}
                onChange={(e) => setBookingStartDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-gray-500">đến</span>
              <input
                type="datetime-local"
                value={bookingEndDate}
                onChange={(e) => setBookingEndDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bookingTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="bookings" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Booking theo trạng thái */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Booking theo trạng thái
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={bookingStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {bookingStatusData.map((entry, index) => (
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
        </div>

        {/* Doanh thu theo khách sạn */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Doanh thu theo khách sạn
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hotelRevenueData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="hotel" type="category" width={100} />
              <Tooltip />
              <Legend />
              <Bar dataKey="revenue" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Khách sạn được đặt nhiều nhất */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top khách sạn được đặt nhiều nhất
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topHotelsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hotel" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="bookings" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Loại phòng được đặt nhiều nhất */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top loại phòng được đặt nhiều nhất
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={topRoomTypesData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {topRoomTypesData.map((entry, index) => (
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
        </div>
      </div>
    </div>
  );
}
