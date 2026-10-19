"use client";

import { useState } from "react";
import {
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Eye,
  Bed,
  Building2,
  Users,
  DollarSign,
  Power,
  ChevronDown,
  ChevronUp,
  Check,
} from "lucide-react";

interface Room {
  id: string;
  hotel: string;
  roomNumber: string;
  roomType: string;
  price: number;
  capacity: number;
  status: "AVAILABLE" | "OCCUPIED" | "MAINTENANCE" | "INACTIVE";
}

const mockRooms: Room[] = [];

type SortField =
  | "roomNumber"
  | "hotel"
  | "roomType"
  | "price"
  | "capacity"
  | "status";
type SortOrder = "asc" | "desc";

export default function RoomsPage() {
  const [rooms, setRooms] = useState<Room[]>(mockRooms);
  const [searchTerm, setSearchTerm] = useState("");
  const [hotelFilter, setHotelFilter] = useState<string>("all");
  const [roomTypeFilter, setRoomTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("roomNumber");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [selectedRooms, setSelectedRooms] = useState<Set<string>>(new Set());

  // Filter rooms
  const filteredRooms = rooms.filter((room) => {
    const matchesSearch =
      room.roomNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      room.hotel.toLowerCase().includes(searchTerm.toLowerCase()) ||
      room.roomType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesHotel = hotelFilter === "all" || room.hotel === hotelFilter;
    const matchesRoomType =
      roomTypeFilter === "all" || room.roomType === roomTypeFilter;
    const matchesStatus =
      statusFilter === "all" || room.status === statusFilter;
    return matchesSearch && matchesHotel && matchesRoomType && matchesStatus;
  });

  // Sort rooms
  const sortedRooms = [...filteredRooms].sort((a, b) => {
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
      setSelectedRooms(new Set(sortedRooms.map((r) => r.id)));
    } else {
      setSelectedRooms(new Set());
    }
  };

  const handleSelectRoom = (roomId: string) => {
    const newSelected = new Set(selectedRooms);
    if (newSelected.has(roomId)) {
      newSelected.delete(roomId);
    } else {
      newSelected.add(roomId);
    }
    setSelectedRooms(newSelected);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "AVAILABLE":
        return "bg-green-100 text-green-800";
      case "OCCUPIED":
        return "bg-red-100 text-red-800";
      case "MAINTENANCE":
        return "bg-yellow-100 text-yellow-800";
      case "INACTIVE":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "AVAILABLE":
        return <Check className="w-4 h-4" />;
      case "OCCUPIED":
        return <Users className="w-4 h-4" />;
      case "MAINTENANCE":
        return <Power className="w-4 h-4" />;
      case "INACTIVE":
        return <Power className="w-4 h-4" />;
      default:
        return null;
    }
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
              placeholder="Tìm kiếm theo số phòng, khách sạn, loại phòng..."
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
                value={hotelFilter}
                onChange={(e) => setHotelFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tất cả khách sạn</option>
                <option value="Khách sạn A">Khách sạn A</option>
                <option value="Khách sạn B">Khách sạn B</option>
                <option value="Khách sạn C">Khách sạn C</option>
              </select>
            </div>

            <select
              value={roomTypeFilter}
              onChange={(e) => setRoomTypeFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả loại phòng</option>
              <option value="Standard">Standard</option>
              <option value="Deluxe">Deluxe</option>
              <option value="Suite">Suite</option>
              <option value="Presidential">Presidential</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="AVAILABLE">AVAILABLE</option>
              <option value="OCCUPIED">OCCUPIED</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>

            <button
              onClick={() => {
                setSearchTerm("");
                setHotelFilter("all");
                setRoomTypeFilter("all");
                setStatusFilter("all");
              }}
              className="px-3 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Reset
            </button>
          </div>

          {/* Add Room Button */}
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="w-5 h-5" />
            <span>Thêm Phòng</span>
          </button>
        </div>

        {/* Bulk Actions */}
        {selectedRooms.size > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap gap-2">
            <span className="text-sm text-gray-600">
              Đã chọn {selectedRooms.size} phòng
            </span>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-100 text-green-800 rounded-lg hover:bg-green-200">
              <Check className="w-4 h-4" />
              Đặt AVAILABLE
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-100 text-red-800 rounded-lg hover:bg-red-200">
              <Users className="w-4 h-4" />
              Đặt OCCUPIED
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200">
              <Power className="w-4 h-4" />
              Đặt MAINTENANCE
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200">
              <Power className="w-4 h-4" />
              Đặt INACTIVE
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-100 text-red-800 rounded-lg hover:bg-red-200">
              <Trash2 className="w-4 h-4" />
              Xóa phòng
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
                      selectedRooms.size === sortedRooms.length &&
                      sortedRooms.length > 0
                    }
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Room ID
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("hotel")}
                >
                  <div className="flex items-center gap-1">
                    Hotel
                    {sortField === "hotel" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("roomNumber")}
                >
                  <div className="flex items-center gap-1">
                    Room Number
                    {sortField === "roomNumber" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("roomType")}
                >
                  <div className="flex items-center gap-1">
                    Room Type
                    {sortField === "roomType" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("price")}
                >
                  <div className="flex items-center gap-1">
                    Price
                    {sortField === "price" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort("capacity")}
                >
                  <div className="flex items-center gap-1">
                    Capacity
                    {sortField === "capacity" &&
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
                    Status
                    {sortField === "status" &&
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
              {sortedRooms.length === 0 ? (
                <tr>
                  <td
                    colSpan={10}
                    className="px-4 py-12 text-center text-gray-500"
                  >
                    Không có dữ liệu
                  </td>
                </tr>
              ) : (
                sortedRooms.map((room) => (
                  <tr key={room.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedRooms.has(room.id)}
                        onChange={() => handleSelectRoom(room.id)}
                        className="rounded border-gray-300"
                      />
                    </td>
                    <td className="px-4 py-3 text-gray-600">{room.id}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">{room.hotel}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Bed className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-900">
                          {room.roomNumber}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{room.roomType}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <DollarSign className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-900">
                          {room.price.toLocaleString("vi-VN")}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">{room.capacity}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          room.status,
                        )}`}
                      >
                        {room.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors">
                          <Power className="w-4 h-4" />
                        </button>
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
