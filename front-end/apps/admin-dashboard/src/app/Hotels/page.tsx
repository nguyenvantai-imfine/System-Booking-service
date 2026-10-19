"use client";

import { useState } from "react";
import {
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Check,
  X,
  Star,
  Building2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface Hotel {
  id: string;
  name: string;
  partner: string;
  address: string;
  city: string;
  roomCount: number;
  rating: number;
  status: "Pending" | "Approved" | "Rejected" | "Hidden" | "Active";
  createdAt: string;
}

const mockHotels: Hotel[] = [];

type SortField =
  | "name"
  | "city"
  | "rating"
  | "roomCount"
  | "status"
  | "createdAt";
type SortOrder = "asc" | "desc";

export default function HotelsPage() {
  const [hotels, setHotels] = useState<Hotel[]>(mockHotels);
  const [searchTerm, setSearchTerm] = useState("");
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [selectedHotels, setSelectedHotels] = useState<Set<string>>(new Set());

  // Filter hotels
  const filteredHotels = hotels.filter((hotel) => {
    const matchesSearch =
      hotel.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hotel.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hotel.partner.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCity = cityFilter === "all" || hotel.city === cityFilter;
    const matchesStatus =
      statusFilter === "all" || hotel.status === statusFilter;
    return matchesSearch && matchesCity && matchesStatus;
  });

  // Sort hotels
  const sortedHotels = [...filteredHotels].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
    if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedHotels(new Set(sortedHotels.map((h) => h.id)));
    } else {
      setSelectedHotels(new Set());
    }
  };

  const handleSelectHotel = (hotelId: string) => {
    const newSelected = new Set(selectedHotels);
    if (newSelected.has(hotelId)) {
      newSelected.delete(hotelId);
    } else {
      newSelected.add(hotelId);
    }
    setSelectedHotels(newSelected);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Active":
        return "bg-green-100 text-green-800";
      case "Pending":
        return "bg-yellow-100 text-yellow-800";
      case "Approved":
        return "bg-blue-100 text-blue-800";
      case "Rejected":
        return "bg-red-100 text-red-800";
      case "Hidden":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-1">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`w-4 h-4 ${
              i < rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300"
            }`}
          />
        ))}
        <span className="ml-1 text-sm text-gray-600">({rating})</span>
      </div>
    );
  };

  return (
    <div className="p-6">
      {/* Filters and Actions */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          {/* Search */}
          <div className="relative flex-1 w-full lg:max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm kiếm theo tên, địa chỉ, partner..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả thành phố</option>
                <option value="Hà Nội">Hà Nội</option>
                <option value="TP. Hồ Chí Minh">TP. Hồ Chí Minh</option>
                <option value="Đà Nẵng">Đà Nẵng</option>
                <option value="Nha Trang">Nha Trang</option>
                <option value="Phú Quốc">Phú Quốc</option>
              </select>
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="Active">Active</option>
              <option value="Pending">Pending</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
              <option value="Hidden">Hidden</option>
            </select>

            <button
              onClick={() => {
                setSearchTerm("");
                setCityFilter("all");
                setStatusFilter("all");
              }}
              className="px-3 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Reset
            </button>
          </div>

          {/* Add Hotel Button */}
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="w-5 h-5" />
            <span>Thêm Khách Sạn</span>
          </button>
        </div>

        {/* Bulk Actions */}
        {selectedHotels.size > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap gap-2">
            <span className="text-sm text-gray-600">
              Đã chọn {selectedHotels.size} khách sạn
            </span>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200">
              <Check className="w-4 h-4" />
              Duyệt khách sạn
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-100 text-red-800 rounded-lg hover:bg-red-200">
              <X className="w-4 h-4" />
              Từ chối khách sạn
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200">
              <EyeOff className="w-4 h-4" />
              Ẩn khách sạn
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-100 text-green-800 rounded-lg hover:bg-green-200">
              <Eye className="w-4 h-4" />
              Hiện khách sạn
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-100 text-red-800 rounded-lg hover:bg-red-200">
              <Trash2 className="w-4 h-4" />
              Xóa khách sạn
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={
                      selectedHotels.size === sortedHotels.length &&
                      sortedHotels.length > 0
                    }
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("name")}
                >
                  <div className="flex items-center gap-1">
                    Tên khách sạn
                    {sortField === "name" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Sở hữu
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Địa chỉ
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("city")}
                >
                  <div className="flex items-center gap-1">
                    Thành phố
                    {sortField === "city" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("roomCount")}
                >
                  <div className="flex items-center gap-1">
                    Số phòng
                    {sortField === "roomCount" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("rating")}
                >
                  <div className="flex items-center gap-1">
                    Rating
                    {sortField === "rating" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("status")}
                >
                  <div className="flex items-center gap-1">
                    Trạng thái
                    {sortField === "status" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("createdAt")}
                >
                  <div className="flex items-center gap-1">
                    Ngày tạo
                    {sortField === "createdAt" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sortedHotels.length === 0 ? (
                <tr>
                  <td
                    colSpan={10}
                    className="px-4 py-12 text-center text-gray-500"
                  >
                    Không có dữ liệu
                  </td>
                </tr>
              ) : (
                sortedHotels.map((hotel) => (
                  <tr key={hotel.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedHotels.has(hotel.id)}
                        onChange={() => handleSelectHotel(hotel.id)}
                        className="rounded border-gray-300"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">
                            {hotel.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {hotel.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{hotel.partner}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-xs truncate">
                      {hotel.address}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{hotel.city}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {hotel.roomCount}
                    </td>
                    <td className="px-4 py-3">{renderStars(hotel.rating)}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          hotel.status,
                        )}`}
                      >
                        {hotel.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {new Date(hotel.createdAt).toLocaleDateString("vi-VN")}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                          <Edit className="w-4 h-4" />
                        </button>
                        {hotel.status === "Pending" && (
                          <>
                            <button className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                              <Check className="w-4 h-4" />
                            </button>
                            <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        {hotel.status === "Active" ||
                        hotel.status === "Approved" ? (
                          <button className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                            <EyeOff className="w-4 h-4" />
                          </button>
                        ) : (
                          <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
