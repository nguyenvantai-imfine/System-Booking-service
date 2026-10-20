"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search,
  Filter,
  Plus,
  Trash2,
  Bed,
  Building2,
  Users,
  DollarSign,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  X,
  RefreshCw,
  SlidersHorizontal,
  Layers,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type {
  PhongItem,
  TrangThaiPhong,
  KhachSanBrief,
  LoaiPhongDetail,
  BatchCreateRoomsInput,
  CreateLoaiPhongInput,
} from "@repo/types";

type SortField = "so_phong" | "hotel" | "roomType" | "price" | "capacity" | "status";
type SortOrder = "asc" | "desc";

export default function RoomsPage() {
  // Dữ liệu danh sách phòng
  const [rooms, setRooms] = useState<PhongItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Dữ liệu tham chiếu khách sạn & loại phòng
  const [hotels, setHotels] = useState<KhachSanBrief[]>([]);
  const [roomTypes, setRoomTypes] = useState<LoaiPhongDetail[]>([]);

  // Bộ lọc & Tìm kiếm
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [hotelFilter, setHotelFilter] = useState<string>("all");
  const [roomTypeFilter, setRoomTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("so_phong");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

  // Trạng thái giao diện
  const [isLoading, setIsLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Modal tạo hàng loạt phòng (Batch Create)
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [batchForm, setBatchForm] = useState<{
    hotel_id: number;
    type_id: number;
    prefix: string;
    tang: number;
    from_number: number;
    to_number: number;
  }>({
    hotel_id: 1,
    type_id: 1,
    prefix: "P.",
    tang: 1,
    from_number: 101,
    to_number: 110,
  });

  // Modal tạo loại phòng mới (Create Room Type)
  const [isTypeModalOpen, setIsTypeModalOpen] = useState(false);
  const [newTypeForm, setNewTypeForm] = useState<CreateLoaiPhongInput & { hotel_id: number }>({
    hotel_id: 1,
    ten_loai_phong: "",
    mo_ta: "",
    suc_chua_nguoi_lon: 2,
    suc_chua_tre_em: 1,
    gia_co_ban_mot_dem: 1000000,
    dien_tich_m2: 30,
  });

  // Debounce tìm kiếm
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedKeyword(searchTerm);
      setPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Tự tắt thông báo toast sau 3s
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Tải danh sách khách sạn
  useEffect(() => {
    const loadHotels = async () => {
      try {
        const res = await apiClient.getHotels({ page: 1, page_size: 100 });
        setHotels(res.items);
        if (res.items.length > 0) {
          setBatchForm((prev) => ({ ...prev, hotel_id: res.items[0].id_khach_san }));
          setNewTypeForm((prev) => ({ ...prev, hotel_id: res.items[0].id_khach_san }));
        }
      } catch (err) {
        console.error("Lỗi khi tải danh sách khách sạn:", err);
      }
    };
    loadHotels();
  }, []);

  // Tải danh sách loại phòng khi thay đổi khách sạn được chọn
  useEffect(() => {
    const loadRoomTypes = async () => {
      try {
        const hotelId = hotelFilter !== "all" ? Number(hotelFilter) : batchForm.hotel_id;
        if (hotelId) {
          const types = await apiClient.getRoomTypesByHotel(hotelId);
          setRoomTypes(types);
          if (types.length > 0) {
            setBatchForm((prev) => ({ ...prev, type_id: types[0].id_loai_phong }));
          }
        }
      } catch (err) {
        console.error("Lỗi tải loại phòng:", err);
      }
    };
    loadRoomTypes();
  }, [hotelFilter, batchForm.hotel_id]);

  // Hàm tải dữ liệu danh sách phòng từ Room Service
  const fetchRooms = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.getRooms({
        hotel_id: hotelFilter !== "all" ? Number(hotelFilter) : undefined,
        room_type_id: roomTypeFilter !== "all" ? Number(roomTypeFilter) : undefined,
        status: statusFilter !== "all" ? (statusFilter as TrangThaiPhong) : undefined,
        keyword: debouncedKeyword || undefined,
        page,
        page_size: pageSize,
      });

      setRooms(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Không thể tải danh sách phòng từ Room Service.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [page, hotelFilter, roomTypeFilter, statusFilter, debouncedKeyword]);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  // Thao tác đổi trạng thái phòng trực tiếp
  const handleChangeStatus = async (room: PhongItem, newStatus: TrangThaiPhong) => {
    try {
      await apiClient.changeRoomStatus(room.id_phong, newStatus);
      setToastMessage({
        type: "success",
        text: `Đã đổi trạng thái phòng ${room.so_phong} sang "${newStatus}".`,
      });
      fetchRooms();
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Đổi trạng thái phòng thất bại.",
      });
    }
  };

  // Thao tác xóa phòng
  const handleDeleteRoom = async (room: PhongItem) => {
    if (!confirm(`Bạn có chắc muốn xóa phòng "${room.so_phong}"?`)) return;
    try {
      await apiClient.deleteRoom(room.id_phong);
      setToastMessage({
        type: "success",
        text: `Đã xóa phòng "${room.so_phong}" thành công.`,
      });
      fetchRooms();
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Xóa phòng thất bại.",
      });
    }
  };

  // Xử lý tạo hàng loạt phòng
  const handleBatchCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const input: BatchCreateRoomsInput = {
        prefix: batchForm.prefix,
        tang: Number(batchForm.tang),
        from_number: Number(batchForm.from_number),
        to_number: Number(batchForm.to_number),
      };
      const created = await apiClient.batchCreateRooms(batchForm.type_id, input);
      setToastMessage({
        type: "success",
        text: `Đã tạo thành công ${created.length} phòng vật lý mới!`,
      });
      setIsBatchModalOpen(false);
      fetchRooms();
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Tạo hàng loạt phòng thất bại.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Xử lý tạo loại phòng mới
  const handleCreateRoomType = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.createRoomType(newTypeForm.hotel_id, {
        ten_loai_phong: newTypeForm.ten_loai_phong,
        mo_ta: newTypeForm.mo_ta,
        suc_chua_nguoi_lon: Number(newTypeForm.suc_chua_nguoi_lon),
        suc_chua_tre_em: Number(newTypeForm.suc_chua_tre_em),
        gia_co_ban_mot_dem: Number(newTypeForm.gia_co_ban_mot_dem),
        dien_tich_m2: Number(newTypeForm.dien_tich_m2),
      });
      setToastMessage({
        type: "success",
        text: `Đã tạo hạng phòng "${newTypeForm.ten_loai_phong}" thành công!`,
      });
      setIsTypeModalOpen(false);
      // Tải lại danh sách loại phòng
      const types = await apiClient.getRoomTypesByHotel(newTypeForm.hotel_id);
      setRoomTypes(types);
    } catch (err: any) {
      setToastMessage({
        type: "error",
        text: err?.data?.detail || "Không thể tạo loại phòng mới.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Sắp xếp
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const getHotelName = (hotelId: number) => {
    const found = hotels.find((h) => h.id_khach_san === hotelId);
    return found ? found.ten_khach_san : `Khách sạn #${hotelId}`;
  };

  const getStatusBadge = (status: TrangThaiPhong) => {
    switch (status) {
      case "AVAILABLE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            AVAILABLE (Trống)
          </span>
        );
      case "OCCUPIED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
            OCCUPIED (Đang ở)
          </span>
        );
      case "MAINTENANCE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            MAINTENANCE (Bảo trì)
          </span>
        );
      case "INACTIVE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
            INACTIVE (Tạm ngưng)
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Toast thông báo */}
      {toastMessage && (
        <div
          className={`fixed bottom-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border text-sm transition-all ${
            toastMessage.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          )}
          <span>{toastMessage.text}</span>
          <button onClick={() => setToastMessage(null)} className="ml-2 hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Bộ lọc và Nút Thao tác */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          {/* Ô tìm kiếm */}
          <div className="relative flex-1 w-full lg:max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm theo số phòng, hạng phòng, ghi chú..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 focus:bg-white transition"
            />
          </div>

          {/* Bộ lọc Khách sạn, Loại phòng & Trạng thái */}
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            {/* Lọc Khách sạn */}
            <div className="flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-slate-400" />
              <select
                value={hotelFilter}
                onChange={(e) => {
                  setHotelFilter(e.target.value);
                  setRoomTypeFilter("all");
                  setPage(1);
                }}
                className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="all">Tất cả Khách sạn</option>
                {hotels.map((h) => (
                  <option key={h.id_khach_san} value={h.id_khach_san}>
                    {h.ten_khach_san}
                  </option>
                ))}
              </select>
            </div>

            {/* Lọc Hạng phòng */}
            <div className="flex items-center gap-1.5">
              <Bed className="w-4 h-4 text-slate-400" />
              <select
                value={roomTypeFilter}
                onChange={(e) => {
                  setRoomTypeFilter(e.target.value);
                  setPage(1);
                }}
                className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="all">Tất cả Hạng phòng</option>
                {roomTypes.map((rt) => (
                  <option key={rt.id_loai_phong} value={rt.id_loai_phong}>
                    {rt.ten_loai_phong}
                  </option>
                ))}
              </select>
            </div>

            {/* Lọc Trạng thái */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">Tất cả Trạng thái</option>
              <option value="AVAILABLE">AVAILABLE (Trống)</option>
              <option value="OCCUPIED">OCCUPIED (Đang ở)</option>
              <option value="MAINTENANCE">MAINTENANCE (Bảo trì)</option>
              <option value="INACTIVE">INACTIVE (Tạm ngưng)</option>
            </select>

            <button
              onClick={() => {
                setSearchTerm("");
                setHotelFilter("all");
                setRoomTypeFilter("all");
                setStatusFilter("all");
                setPage(1);
              }}
              className="px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded-xl hover:bg-slate-50 transition"
            >
              Reset
            </button>

            <button
              onClick={fetchRooms}
              title="Làm mới dữ liệu"
              className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>

            {/* Nút Tạo Hạng Phòng Mới */}
            <button
              onClick={() => setIsTypeModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 border border-blue-600 text-blue-600 hover:bg-blue-50 rounded-xl text-sm font-semibold transition"
            >
              <Layers className="w-4 h-4" />
              <span>+ Hạng Phòng</span>
            </button>

            {/* Nút Tạo Hàng Loạt Phòng Vật Lý */}
            <button
              onClick={() => setIsBatchModalOpen(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 shadow-sm transition"
            >
              <Plus className="w-4 h-4" />
              <span>Sinh Phòng Tự Động</span>
            </button>
          </div>
        </div>
      </div>

      {/* Bảng Quản lý Danh Sách Phòng */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="px-5 py-3.5">ID</th>
                <th className="px-5 py-3.5">Khách sạn</th>
                <th
                  className="px-5 py-3.5 cursor-pointer hover:bg-slate-100"
                  onClick={() => handleSort("so_phong")}
                >
                  <div className="flex items-center gap-1">
                    Số phòng
                    {sortField === "so_phong" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      ))}
                  </div>
                </th>
                <th className="px-5 py-3.5">Hạng phòng</th>
                <th className="px-5 py-3.5">Giá / Đêm</th>
                <th className="px-5 py-3.5">Sức chứa</th>
                <th className="px-5 py-3.5">Trạng thái</th>
                <th className="px-5 py-3.5 text-center">Đổi Trạng Thái Nhanh</th>
                <th className="px-5 py-3.5 text-center">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="px-5 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                    Đang tải danh sách phòng...
                  </td>
                </tr>
              ) : rooms.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-5 py-12 text-center text-slate-500">
                    Không tìm thấy phòng nào phù hợp với bộ lọc.
                  </td>
                </tr>
              ) : (
                rooms.map((room) => {
                  const price =
                    room.loai_phong?.gia_co_ban_mot_dem !== undefined
                      ? Number(room.loai_phong.gia_co_ban_mot_dem).toLocaleString("vi-VN") +
                        " đ"
                      : "Liên hệ";

                  const capacity = room.loai_phong
                    ? `${room.loai_phong.suc_chua_nguoi_lon} lớn, ${room.loai_phong.suc_chua_tre_em} nhỏ`
                    : "2 người";

                  return (
                    <tr
                      key={room.id_phong}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      <td className="px-5 py-4 font-mono text-xs text-slate-500">
                        #{room.id_phong}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-slate-400" />
                          <span className="font-medium text-slate-800">
                            {getHotelName(room.id_khach_san)}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <Bed className="w-4 h-4 text-blue-600" />
                          <div>
                            <span className="font-bold text-slate-900">
                              {room.so_phong}
                            </span>
                            {room.tang && (
                              <span className="ml-1.5 text-xs text-slate-400">
                                (Tầng {room.tang})
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-slate-700 font-medium">
                        {room.loai_phong?.ten_loai_phong || "Chưa phân loại"}
                      </td>
                      <td className="px-5 py-4 font-semibold text-slate-900">
                        {price}
                      </td>
                      <td className="px-5 py-4 text-slate-600 text-xs">
                        <div className="flex items-center gap-1">
                          <Users className="w-3.5 h-3.5 text-slate-400" />
                          <span>{capacity}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">{getStatusBadge(room.trang_thai)}</td>

                      {/* Dropdown Đổi trạng thái trực tiếp */}
                      <td className="px-5 py-4 text-center">
                        <select
                          value={room.trang_thai}
                          onChange={(e) =>
                            handleChangeStatus(room, e.target.value as TrangThaiPhong)
                          }
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                        >
                          <option value="AVAILABLE">AVAILABLE (Trống)</option>
                          <option value="OCCUPIED">OCCUPIED (Đang ở)</option>
                          <option value="MAINTENANCE">MAINTENANCE (Bảo trì)</option>
                          <option value="INACTIVE">INACTIVE (Tạm ngưng)</option>
                        </select>
                      </td>

                      {/* Thao tác */}
                      <td className="px-5 py-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => handleDeleteRoom(room)}
                            title="Xóa phòng"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Phân trang */}
        <div className="px-5 py-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <div>
            Hiển thị <span className="font-semibold text-slate-800">{rooms.length}</span> /{" "}
            <span className="font-semibold text-slate-800">{total}</span> phòng vật lý
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page <= 1 || isLoading}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Trang <span className="font-semibold text-slate-800">{page}</span> /{" "}
              {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page >= totalPages || isLoading}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* MODAL TẠO HÀNG LOẠT PHÒNG VẬT LÝ (Batch Create Rooms) */}
      {isBatchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Plus className="w-5 h-5 text-blue-600" />
                Sinh Hàng Loạt Phòng Vật Lý
              </h3>
              <button
                onClick={() => setIsBatchModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleBatchCreate} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Chọn Khách Sạn *
                </label>
                <select
                  value={batchForm.hotel_id}
                  onChange={(e) =>
                    setBatchForm({ ...batchForm, hotel_id: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {hotels.map((h) => (
                    <option key={h.id_khach_san} value={h.id_khach_san}>
                      {h.ten_khach_san}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Chọn Hạng Phòng *
                </label>
                <select
                  value={batchForm.type_id}
                  onChange={(e) =>
                    setBatchForm({ ...batchForm, type_id: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {roomTypes.map((rt) => (
                    <option key={rt.id_loai_phong} value={rt.id_loai_phong}>
                      {rt.ten_loai_phong} (
                      {Number(rt.gia_co_ban_mot_dem).toLocaleString("vi-VN")} đ)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Tiền tố (Prefix)
                  </label>
                  <input
                    type="text"
                    value={batchForm.prefix}
                    onChange={(e) =>
                      setBatchForm({ ...batchForm, prefix: e.target.value })
                    }
                    placeholder="P."
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Tầng (Floor)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={batchForm.tang}
                    onChange={(e) =>
                      setBatchForm({ ...batchForm, tang: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Từ số phòng *
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={batchForm.from_number}
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        from_number: Number(e.target.value),
                      })
                    }
                    placeholder="201"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Đến số phòng *
                  </label>
                  <input
                    type="number"
                    required
                    min={batchForm.from_number}
                    value={batchForm.to_number}
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        to_number: Number(e.target.value),
                      })
                    }
                    placeholder="210"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="p-3 bg-blue-50 rounded-xl text-xs text-blue-700">
                Hệ thống sẽ tạo tự động{" "}
                <strong>
                  {Math.max(0, batchForm.to_number - batchForm.from_number + 1)}
                </strong>{" "}
                phòng: ví dụ từ{" "}
                <strong>
                  {batchForm.prefix}
                  {batchForm.from_number}
                </strong>{" "}
                đến{" "}
                <strong>
                  {batchForm.prefix}
                  {batchForm.to_number}
                </strong>
                .
              </div>

              <div className="flex justify-end gap-3 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setIsBatchModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-semibold transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold disabled:opacity-50 transition"
                >
                  {isSubmitting ? "Đang tạo..." : "Xác Nhận Tạo"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL TẠO HẠNG PHÒNG MỚI */}
      {isTypeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-600" />
                Thêm Mới Hạng Phòng
              </h3>
              <button
                onClick={() => setIsTypeModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRoomType} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Thuộc Khách Sạn *
                </label>
                <select
                  value={newTypeForm.hotel_id}
                  onChange={(e) =>
                    setNewTypeForm({
                      ...newTypeForm,
                      hotel_id: Number(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {hotels.map((h) => (
                    <option key={h.id_khach_san} value={h.id_khach_san}>
                      {h.ten_khach_san}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Tên Hạng Phòng *
                </label>
                <input
                  type="text"
                  required
                  value={newTypeForm.ten_loai_phong}
                  onChange={(e) =>
                    setNewTypeForm({
                      ...newTypeForm,
                      ten_loai_phong: e.target.value,
                    })
                  }
                  placeholder="ví dụ: Grand Suite King Bed"
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Giá một đêm (VND) *
                  </label>
                  <input
                    type="number"
                    required
                    min={10000}
                    step={10000}
                    value={newTypeForm.gia_co_ban_mot_dem}
                    onChange={(e) =>
                      setNewTypeForm({
                        ...newTypeForm,
                        gia_co_ban_mot_dem: Number(e.target.value),
                      })
                    }
                    placeholder="1500000"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Diện tích (m²)
                  </label>
                  <input
                    type="number"
                    min={10}
                    value={newTypeForm.dien_tich_m2 || 30}
                    onChange={(e) =>
                      setNewTypeForm({
                        ...newTypeForm,
                        dien_tich_m2: Number(e.target.value),
                      })
                    }
                    placeholder="35"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Người lớn
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={newTypeForm.suc_chua_nguoi_lon}
                    onChange={(e) =>
                      setNewTypeForm({
                        ...newTypeForm,
                        suc_chua_nguoi_lon: Number(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Trẻ em
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={newTypeForm.suc_chua_tre_em}
                    onChange={(e) =>
                      setNewTypeForm({
                        ...newTypeForm,
                        suc_chua_tre_em: Number(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Mô tả hạng phòng
                </label>
                <textarea
                  rows={2}
                  value={newTypeForm.mo_ta || ""}
                  onChange={(e) =>
                    setNewTypeForm({ ...newTypeForm, mo_ta: e.target.value })
                  }
                  placeholder="Mô tả tiện ích, hướng nhìn..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setIsTypeModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-semibold transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold disabled:opacity-50 transition"
                >
                  {isSubmitting ? "Đang tạo..." : "Lưu Hạng Phòng"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
