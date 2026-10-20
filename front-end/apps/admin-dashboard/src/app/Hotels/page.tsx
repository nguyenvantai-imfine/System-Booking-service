"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Search,
  Filter,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Check,
  X,
  Building2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  RefreshCw,
  Loader2,
  MapPin,
  Phone,
  Mail,
  User,
  CheckCircle2,
  SlidersHorizontal,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type {
  KhachSanBrief,
  KhachSanDetail,
  TrangThaiKhachSan,
  CreateHotelInput,
} from "@repo/types";

type SortField =
  | "ten_khach_san"
  | "thanh_pho"
  | "trang_thai"
  | "ngay_tao"
  | "id_khach_san";
type SortOrder = "asc" | "desc";

export default function HotelsPage() {
  // ── States danh sách & bộ lọc ───────────────────────────────────────────────
  const [hotels, setHotels] = useState<KhachSanBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const [sortField, setSortField] = useState<SortField>("id_khach_san");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [selectedHotels, setSelectedHotels] = useState<Set<number>>(new Set());

  // ── States tương tác & Modal ────────────────────────────────────────────────
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // Modal Thêm khách sạn
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [submittingAdd, setSubmittingAdd] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    ten_khach_san: "",
    email_khach_san: "",
    sdt_khach_san: "",
    dia_chi: "",
    thanh_pho: "Hà Nội",
    quan_huyen: "",
    ten_nguoi_lien_he: "",
    sdt_nguoi_lien_he: "",
  });

  // Modal Chi tiết khách sạn
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<KhachSanDetail | null>(
    null
  );

  // Modal Xác nhận xóa
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    hotelId?: number;
    hotelName?: string;
    isBulk?: boolean;
  }>({ isOpen: false });

  // ── Tự động ẩn toast sau 3.5s ───────────────────────────────────────────────
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // ── Debounce 400ms cho ô tìm kiếm ───────────────────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // ── Hàm Fetch danh sách Khách Sạn từ Backend ────────────────────────────────
  const fetchHotels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getHotels({
        keyword: debouncedSearch || undefined,
        city: cityFilter !== "all" ? cityFilter : undefined,
        trang_thai:
          statusFilter !== "all"
            ? (statusFilter as TrangThaiKhachSan)
            : undefined,
        page: 1,
        page_size: 100,
      });
      setHotels(res.items || []);
    } catch (err: unknown) {
      console.error("Lỗi tải danh sách khách sạn:", err);
      const msg =
        err instanceof Error
          ? err.message
          : "Không thể kết nối đến Hotel Service.";
      setError(
        `${msg}. Vui lòng kiểm tra xem Backend FastAPI (cổng 8000) đã được khởi chạy chưa.`
      );
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, cityFilter, statusFilter]);

  useEffect(() => {
    fetchHotels();
  }, [fetchHotels]);

  // ── Sắp xếp dữ liệu ────────────────────────────────────────────────────────
  const sortedHotels = [...hotels].sort((a, b) => {
    const aValue = a[sortField] ?? "";
    const bValue = b[sortField] ?? "";
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

  // ── Chọn Checkbox ──────────────────────────────────────────────────────────
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedHotels(new Set(sortedHotels.map((h) => h.id_khach_san)));
    } else {
      setSelectedHotels(new Set());
    }
  };

  const handleSelectHotel = (hotelId: number) => {
    const newSelected = new Set(selectedHotels);
    if (newSelected.has(hotelId)) {
      newSelected.delete(hotelId);
    } else {
      newSelected.add(hotelId);
    }
    setSelectedHotels(newSelected);
  };

  // ── Đổi trạng thái 1 khách sạn ─────────────────────────────────────────────
  const handleChangeStatus = async (
    id: number,
    newStatus: TrangThaiKhachSan
  ) => {
    setActionLoading(true);
    try {
      await apiClient.changeHotelStatus(id, newStatus);
      setToast({
        type: "success",
        message: `Đã cập nhật trạng thái khách sạn #${id} sang "${getTrangThaiLabel(newStatus)}" thành công!`,
      });
      await fetchHotels();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác thất bại";
      setToast({ type: "error", message: `Lỗi đổi trạng thái: ${msg}` });
    } finally {
      setActionLoading(false);
    }
  };

  // ── Xóa mềm 1 khách sạn ────────────────────────────────────────────────────
  const handleDeleteHotel = async (id: number) => {
    setActionLoading(true);
    try {
      await apiClient.deleteHotel(id);
      setToast({
        type: "success",
        message: `Đã xóa mềm khách sạn #${id} thành công!`,
      });
      setSelectedHotels((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      await fetchHotels();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác thất bại";
      setToast({ type: "error", message: `Lỗi xóa khách sạn: ${msg}` });
    } finally {
      setActionLoading(false);
      setDeleteConfirm({ isOpen: false });
    }
  };

  // ── Thao tác hàng loạt (Bulk Actions) ───────────────────────────────────────
  const handleBulkStatusChange = async (newStatus: TrangThaiKhachSan) => {
    if (selectedHotels.size === 0) return;
    setActionLoading(true);
    try {
      const ids = Array.from(selectedHotels);
      await Promise.all(
        ids.map((id) => apiClient.changeHotelStatus(id, newStatus))
      );
      setToast({
        type: "success",
        message: `Đã cập nhật ${ids.length} khách sạn sang "${getTrangThaiLabel(newStatus)}" thành công!`,
      });
      setSelectedHotels(new Set());
      await fetchHotels();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác thất bại";
      setToast({ type: "error", message: `Lỗi cập nhật hàng loạt: ${msg}` });
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedHotels.size === 0) return;
    setActionLoading(true);
    try {
      const ids = Array.from(selectedHotels);
      await Promise.all(ids.map((id) => apiClient.deleteHotel(id)));
      setToast({
        type: "success",
        message: `Đã xóa mềm ${ids.length} khách sạn thành công!`,
      });
      setSelectedHotels(new Set());
      await fetchHotels();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác thất bại";
      setToast({ type: "error", message: `Lỗi xóa hàng loạt: ${msg}` });
    } finally {
      setActionLoading(false);
      setDeleteConfirm({ isOpen: false });
    }
  };

  // ── Xem chi tiết khách sạn ─────────────────────────────────────────────────
  const handleOpenDetail = async (id: number) => {
    setIsDetailModalOpen(true);
    setDetailLoading(true);
    try {
      const detail = await apiClient.getHotelById(id);
      setSelectedDetail(detail);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi tải chi tiết";
      setToast({ type: "error", message: `Không thể tải chi tiết: ${msg}` });
      setIsDetailModalOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // ── Xử lý Form Thêm Khách Sạn ──────────────────────────────────────────────
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.ten_khach_san.trim()) {
      setFormError("Vui lòng nhập Tên khách sạn");
      return;
    }

    const phoneRegex = /^(\+?[0-9]{6,15})$/;
    if (
      formData.sdt_khach_san &&
      !phoneRegex.test(formData.sdt_khach_san.trim().replace(/[\s.-]/g, ""))
    ) {
      setFormError(
        "SĐT khách sạn không hợp lệ (yêu cầu từ 6 đến 15 chữ số)"
      );
      return;
    }
    if (
      formData.sdt_nguoi_lien_he &&
      !phoneRegex.test(formData.sdt_nguoi_lien_he.trim().replace(/[\s.-]/g, ""))
    ) {
      setFormError(
        "SĐT người liên hệ không hợp lệ (yêu cầu từ 6 đến 15 chữ số)"
      );
      return;
    }

    setSubmittingAdd(true);
    try {
      const payload: CreateHotelInput = {
        id_tai_khoan: 1, // Demo Admin / Partner 1
        ten_khach_san: formData.ten_khach_san.trim(),
        email_khach_san: formData.email_khach_san.trim() || undefined,
        sdt_khach_san: formData.sdt_khach_san.trim() || undefined,
        dia_chi: formData.dia_chi.trim() || undefined,
        thanh_pho: formData.thanh_pho.trim() || undefined,
        tinh: formData.thanh_pho.trim() || undefined,
        quan_huyen: formData.quan_huyen.trim() || undefined,
        ten_nguoi_lien_he: formData.ten_nguoi_lien_he.trim() || undefined,
        sdt_nguoi_lien_he: formData.sdt_nguoi_lien_he.trim() || undefined,
        trang_thai: "HOAT_DONG",
      };

      await apiClient.createHotel(payload);

      setToast({
        type: "success",
        message: `Khách sạn "${payload.ten_khach_san}" đã được tạo thành công vào CSDL!`,
      });

      setIsAddModalOpen(false);
      setFormData({
        ten_khach_san: "",
        email_khach_san: "",
        sdt_khach_san: "",
        dia_chi: "",
        thanh_pho: "Hà Nội",
        quan_huyen: "",
        ten_nguoi_lien_he: "",
        sdt_nguoi_lien_he: "",
      });

      await fetchHotels();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi tạo khách sạn";
      setFormError(`Không thể tạo khách sạn: ${msg}`);
    } finally {
      setSubmittingAdd(false);
    }
  };

  // ── Helper định dạng trạng thái ────────────────────────────────────────────
  const getTrangThaiLabel = (status: TrangThaiKhachSan) => {
    switch (status) {
      case "HOAT_DONG":
        return "Hoạt động";
      case "TAM_DUNG":
        return "Tạm dừng";
      case "CHO_DUYET":
        return "Chờ duyệt";
      case "DA_XOA":
        return "Đã xóa";
      default:
        return status;
    }
  };

  const getStatusBadgeStyle = (status: TrangThaiKhachSan) => {
    switch (status) {
      case "HOAT_DONG":
        return "bg-emerald-50 text-emerald-700 border border-emerald-200/60";
      case "CHO_DUYET":
        return "bg-amber-50 text-amber-700 border border-amber-200/60";
      case "TAM_DUNG":
        return "bg-slate-100 text-slate-700 border border-slate-200";
      case "DA_XOA":
        return "bg-rose-50 text-rose-700 border border-rose-200/60";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* ── Toast Notification ─────────────────────────────────────────────── */}
      {toast && (
        <div
          className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-lg border text-sm font-medium transition-all transform animate-in slide-in-from-top-3 ${
            toast.type === "success"
              ? "bg-white text-emerald-800 border-emerald-200"
              : "bg-white text-rose-800 border-rose-200"
          }`}
        >
          {toast.type === "success" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          )}
          <span>{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="ml-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Header Title & Stats ───────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
            Quản Lý Khách Sạn
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Kết nối trực tiếp API Hotel Service • Tổng số:{" "}
            <span className="font-semibold text-gray-900">{hotels.length}</span>{" "}
            khách sạn
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchHotels}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50"
            title="Làm mới dữ liệu"
          >
            <RefreshCw
              className={`w-4 h-4 ${loading ? "animate-spin text-blue-600" : ""}`}
            />
            <span className="hidden sm:inline">Làm mới</span>
          </button>

          <button
            onClick={() => {
              setFormError(null);
              setIsAddModalOpen(true);
            }}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Thêm Khách Sạn</span>
          </button>
        </div>
      </div>

      {/* ── Error Banner ───────────────────────────────────────────────────── */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-rose-800">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
          <button
            onClick={fetchHotels}
            className="px-3.5 py-1.5 text-xs font-medium bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors flex-shrink-0"
          >
            Thử lại kết nối
          </button>
        </div>
      )}

      {/* ── Filter Bar & Actions ───────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-5 space-y-4">
        <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
          {/* Ô Tìm kiếm với Debounce 400ms */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm theo tên khách sạn, địa chỉ, người liên hệ..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50/60 border border-gray-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Bộ lọc Thành phố & Trạng thái */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-1.5 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl">
              <MapPin className="w-4 h-4 text-gray-400" />
              <select
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
                className="bg-transparent text-sm text-gray-700 font-medium focus:outline-none cursor-pointer"
              >
                <option value="all">Tất cả thành phố</option>
                <option value="Hà Nội">Hà Nội</option>
                <option value="Hồ Chí Minh">TP. Hồ Chí Minh</option>
                <option value="Đà Nẵng">Đà Nẵng</option>
                <option value="Nha Trang">Nha Trang</option>
                <option value="Phú Quốc">Phú Quốc</option>
                <option value="Đà Lạt">Đà Lạt</option>
                <option value="Vũng Tàu">Vũng Tàu</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl">
              <SlidersHorizontal className="w-4 h-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-transparent text-sm text-gray-700 font-medium focus:outline-none cursor-pointer"
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="HOAT_DONG">Hoạt động</option>
                <option value="CHO_DUYET">Chờ duyệt</option>
                <option value="TAM_DUNG">Tạm dừng</option>
              </select>
            </div>

            {(searchTerm || cityFilter !== "all" || statusFilter !== "all") && (
              <button
                onClick={() => {
                  setSearchTerm("");
                  setCityFilter("all");
                  setStatusFilter("all");
                }}
                className="px-3 py-2 text-sm text-gray-500 hover:text-gray-800 border border-dashed border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
              >
                Đặt lại lọc
              </button>
            )}
          </div>
        </div>

        {/* ── Bulk Actions Bar ─────────────────────────────────────────────── */}
        {selectedHotels.size > 0 && (
          <div className="pt-3 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3 animate-in fade-in">
            <span className="text-sm font-medium text-gray-600">
              Đang chọn:{" "}
              <span className="font-semibold text-blue-600">
                {selectedHotels.size}
              </span>{" "}
              khách sạn
            </span>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => handleBulkStatusChange("HOAT_DONG")}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                Duyệt / Kích hoạt
              </button>

              <button
                onClick={() => handleBulkStatusChange("TAM_DUNG")}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                <EyeOff className="w-3.5 h-3.5" />
                Tạm dừng / Ẩn
              </button>

              <button
                onClick={() =>
                  setDeleteConfirm({
                    isOpen: true,
                    isBulk: true,
                  })
                }
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200 rounded-lg hover:bg-rose-100 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Xóa đã chọn
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Table Data ─────────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                <th className="px-4 py-3.5 w-12 text-center">
                  <input
                    type="checkbox"
                    checked={
                      sortedHotels.length > 0 &&
                      selectedHotels.size === sortedHotels.length
                    }
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                </th>

                <th
                  onClick={() => handleSort("ten_khach_san")}
                  className="px-4 py-3.5 cursor-pointer hover:text-blue-600 select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Khách Sạn</span>
                    {sortField === "ten_khach_san" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ))}
                  </div>
                </th>

                <th className="px-4 py-3.5">Liên hệ</th>

                <th
                  onClick={() => handleSort("thanh_pho")}
                  className="px-4 py-3.5 cursor-pointer hover:text-blue-600 select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Địa Điểm</span>
                    {sortField === "thanh_pho" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ))}
                  </div>
                </th>

                <th
                  onClick={() => handleSort("trang_thai")}
                  className="px-4 py-3.5 cursor-pointer hover:text-blue-600 select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Trạng Thái</span>
                    {sortField === "trang_thai" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ))}
                  </div>
                </th>

                <th
                  onClick={() => handleSort("ngay_tao")}
                  className="px-4 py-3.5 cursor-pointer hover:text-blue-600 select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Ngày Tạo</span>
                    {sortField === "ngay_tao" &&
                      (sortOrder === "asc" ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ))}
                  </div>
                </th>

                <th className="px-4 py-3.5 text-right pr-6">Hành Động</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-100 text-sm">
              {loading ? (
                // ── Loading Skeleton ─────────────────────────────────────────
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-4 py-4 text-center">
                      <div className="w-4 h-4 bg-gray-200 rounded mx-auto" />
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-200 rounded-xl" />
                        <div className="space-y-2">
                          <div className="w-36 h-4 bg-gray-200 rounded" />
                          <div className="w-20 h-3 bg-gray-100 rounded" />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="w-28 h-4 bg-gray-200 rounded" />
                    </td>
                    <td className="px-4 py-4">
                      <div className="w-24 h-4 bg-gray-200 rounded" />
                    </td>
                    <td className="px-4 py-4">
                      <div className="w-20 h-6 bg-gray-200 rounded-full" />
                    </td>
                    <td className="px-4 py-4">
                      <div className="w-20 h-4 bg-gray-200 rounded" />
                    </td>
                    <td className="px-4 py-4 text-right pr-6">
                      <div className="w-16 h-8 bg-gray-200 rounded ml-auto" />
                    </td>
                  </tr>
                ))
              ) : sortedHotels.length === 0 ? (
                // ── Empty State ──────────────────────────────────────────────
                <tr>
                  <td colSpan={7} className="px-4 py-16 text-center">
                    <div className="max-w-sm mx-auto flex flex-col items-center">
                      <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4">
                        <Building2 className="w-7 h-7" />
                      </div>
                      <h3 className="text-base font-semibold text-gray-900">
                        Chưa có khách sạn nào
                      </h3>
                      <p className="text-sm text-gray-500 mt-1 mb-5">
                        Không tìm thấy khách sạn phù hợp với tiêu chí lọc, hoặc
                        CSDL chưa có dữ liệu.
                      </p>
                      <button
                        onClick={() => setIsAddModalOpen(true)}
                        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
                      >
                        <Plus className="w-4 h-4" />
                        Thêm Khách Sạn Đầu Tiên
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                // ── Rows Data ────────────────────────────────────────────────
                sortedHotels.map((hotel) => (
                  <tr
                    key={hotel.id_khach_san}
                    className="hover:bg-slate-50/70 transition-colors group"
                  >
                    <td className="px-4 py-3.5 text-center">
                      <input
                        type="checkbox"
                        checked={selectedHotels.has(hotel.id_khach_san)}
                        onChange={() =>
                          handleSelectHotel(hotel.id_khach_san)
                        }
                        className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      />
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-50/80 border border-blue-100 flex items-center justify-center flex-shrink-0 text-blue-600 overflow-hidden">
                          {hotel.anh_dai_dien ? (
                            <img
                              src={hotel.anh_dai_dien}
                              alt={hotel.ten_khach_san}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <Building2 className="w-5 h-5" />
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                            {hotel.ten_khach_san}
                          </div>
                          <div className="text-xs text-gray-400 mt-0.5">
                            ID: #{hotel.id_khach_san} • Partner #
                            {hotel.id_tai_khoan}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="space-y-1 text-xs text-gray-600">
                        {hotel.sdt_khach_san && (
                          <div className="flex items-center gap-1.5">
                            <Phone className="w-3.5 h-3.5 text-gray-400" />
                            <span>{hotel.sdt_khach_san}</span>
                          </div>
                        )}
                        {hotel.email_khach_san && (
                          <div className="flex items-center gap-1.5">
                            <Mail className="w-3.5 h-3.5 text-gray-400" />
                            <span className="truncate max-w-[160px]">
                              {hotel.email_khach_san}
                            </span>
                          </div>
                        )}
                        {!hotel.sdt_khach_san && !hotel.email_khach_san && (
                          <span className="text-gray-400 italic">Chưa có</span>
                        )}
                      </div>
                    </td>

                    <td className="px-4 py-3.5 text-gray-600">
                      <div className="font-medium text-gray-900 text-xs">
                        {hotel.thanh_pho || hotel.tinh || "Chưa rõ"}
                      </div>
                      <div className="text-xs text-gray-400 truncate max-w-[180px] mt-0.5">
                        {hotel.dia_chi || "Chưa có địa chỉ chi tiết"}
                      </div>
                    </td>

                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusBadgeStyle(
                          hotel.trang_thai
                        )}`}
                      >
                        {getTrangThaiLabel(hotel.trang_thai)}
                      </span>
                    </td>

                    <td className="px-4 py-3.5 text-xs text-gray-500 whitespace-nowrap">
                      {new Date(hotel.ngay_tao).toLocaleDateString("vi-VN", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </td>

                    <td className="px-4 py-3.5 text-right pr-6 whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* Xem chi tiết */}
                        <button
                          onClick={() =>
                            handleOpenDetail(hotel.id_khach_san)
                          }
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Xem chi tiết"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {/* Duyệt / Kích hoạt sang HOAT_DONG */}
                        {hotel.trang_thai !== "HOAT_DONG" && (
                          <button
                            onClick={() =>
                              handleChangeStatus(
                                hotel.id_khach_san,
                                "HOAT_DONG"
                              )
                            }
                            disabled={actionLoading}
                            className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                            title="Kích hoạt hoạt động"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}

                        {/* Tạm dừng / Ẩn sang TAM_DUNG */}
                        {hotel.trang_thai === "HOAT_DONG" && (
                          <button
                            onClick={() =>
                              handleChangeStatus(
                                hotel.id_khach_san,
                                "TAM_DUNG"
                              )
                            }
                            disabled={actionLoading}
                            className="p-1.5 text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                            title="Tạm dừng / Ẩn khách sạn"
                          >
                            <EyeOff className="w-4 h-4" />
                          </button>
                        )}

                        {/* Xóa mềm */}
                        <button
                          onClick={() =>
                            setDeleteConfirm({
                              isOpen: true,
                              hotelId: hotel.id_khach_san,
                              hotelName: hotel.ten_khach_san,
                            })
                          }
                          disabled={actionLoading}
                          className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Xóa mềm khách sạn"
                        >
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

      {/* ── Modal Thêm Mới Khách Sạn ────────────────────────────────────────── */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden border border-gray-100 animate-in zoom-in-95">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900">
                  Thêm Khách Sạn Mới
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Tạo trực tiếp vào CSDL qua API Hotel Service
                </p>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                  Tên Khách Sạn <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Khách Sạn Grand Mường Thanh"
                  value={formData.ten_khach_san}
                  onChange={(e) =>
                    setFormData({ ...formData, ten_khach_san: e.target.value })
                  }
                  className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    Email Khách Sạn
                  </label>
                  <input
                    type="email"
                    placeholder="contact@hotel.com"
                    value={formData.email_khach_san}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        email_khach_san: e.target.value,
                      })
                    }
                    className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    Số Điện Thoại
                  </label>
                  <input
                    type="tel"
                    placeholder="0912345678"
                    value={formData.sdt_khach_san}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        sdt_khach_san: e.target.value,
                      })
                    }
                    className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    Tỉnh / Thành Phố
                  </label>
                  <select
                    value={formData.thanh_pho}
                    onChange={(e) =>
                      setFormData({ ...formData, thanh_pho: e.target.value })
                    }
                    className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none bg-white cursor-pointer"
                  >
                    <option value="Hà Nội">Hà Nội</option>
                    <option value="Hồ Chí Minh">TP. Hồ Chí Minh</option>
                    <option value="Đà Nẵng">Đà Nẵng</option>
                    <option value="Nha Trang">Nha Trang</option>
                    <option value="Phú Quốc">Phú Quốc</option>
                    <option value="Đà Lạt">Đà Lạt</option>
                    <option value="Vũng Tàu">Vũng Tàu</option>
                    <option value="Hải Phòng">Hải Phòng</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    Quận / Huyện
                  </label>
                  <input
                    type="text"
                    placeholder="Ví dụ: Hoàn Kiếm, Hải Châu..."
                    value={formData.quan_huyen}
                    onChange={(e) =>
                      setFormData({ ...formData, quan_huyen: e.target.value })
                    }
                    className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                  Địa Chỉ Cụ Thể (Số nhà, đường)
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: 123 Đường Trần Phú"
                  value={formData.dia_chi}
                  onChange={(e) =>
                    setFormData({ ...formData, dia_chi: e.target.value })
                  }
                  className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2 border-t border-gray-100">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    Người Quản Lý / Đại Diện
                  </label>
                  <input
                    type="text"
                    placeholder="Nguyễn Văn A"
                    value={formData.ten_nguoi_lien_he}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        ten_nguoi_lien_he: e.target.value,
                      })
                    }
                    className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                    SĐT Người Quản Lý
                  </label>
                  <input
                    type="tel"
                    placeholder="0987654321"
                    value={formData.sdt_nguoi_lien_he}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        sdt_nguoi_lien_he: e.target.value,
                      })
                    }
                    className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>

              <div className="pt-4 flex items-center justify-end gap-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  disabled={submittingAdd}
                  className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
                >
                  Hủy Bỏ
                </button>

                <button
                  type="submit"
                  disabled={submittingAdd}
                  className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors shadow-sm disabled:opacity-50"
                >
                  {submittingAdd && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                  <span>
                    {submittingAdd ? "Đang Lưu..." : "Thêm Khách Sạn"}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal Xem Chi Tiết Khách Sạn ───────────────────────────────────── */}
      {isDetailModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-100">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
              <div>
                <h3 className="text-lg font-bold text-gray-900">
                  Chi Tiết Khách Sạn
                </h3>
                <p className="text-xs text-gray-500">
                  Mã định danh ID: #{selectedDetail?.id_khach_san}
                </p>
              </div>
              <button
                onClick={() => setIsDetailModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading ? (
              <div className="p-12 text-center flex flex-col items-center">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
                <p className="text-sm text-gray-500">Đang nạp dữ liệu chi tiết...</p>
              </div>
            ) : selectedDetail ? (
              <div className="p-6 space-y-6">
                <div>
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-900">
                      {selectedDetail.ten_khach_san}
                    </h2>
                    <span
                      className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeStyle(
                        selectedDetail.trang_thai
                      )}`}
                    >
                      {getTrangThaiLabel(selectedDetail.trang_thai)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1 flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span>
                      {selectedDetail.dia_chi || "Chưa có địa chỉ"}, {selectedDetail.quan_huyen},{" "}
                      {selectedDetail.thanh_pho || selectedDetail.tinh}
                    </span>
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl text-sm">
                  <div>
                    <span className="text-xs text-gray-400 block">Số Điện Thoại</span>
                    <span className="font-medium text-gray-900">
                      {selectedDetail.sdt_khach_san || "Chưa cập nhật"}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-gray-400 block">Email</span>
                    <span className="font-medium text-gray-900">
                      {selectedDetail.email_khach_san || "Chưa cập nhật"}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-gray-400 block">Người Quản Lý</span>
                    <span className="font-medium text-gray-900">
                      {selectedDetail.ten_nguoi_lien_he || "Chưa cập nhật"} (
                      {selectedDetail.sdt_nguoi_lien_he || "N/A"})
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-gray-400 block">Ngày Tạo</span>
                    <span className="font-medium text-gray-900">
                      {new Date(selectedDetail.ngay_tao).toLocaleString("vi-VN")}
                    </span>
                  </div>
                </div>

                {/* Tiện nghi */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                    Tiện Nghi ({selectedDetail.danh_muc_tien_ich?.length || 0} danh mục)
                  </h4>
                  {selectedDetail.danh_muc_tien_ich?.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {selectedDetail.danh_muc_tien_ich.map((dm) => (
                        <span
                          key={dm.id_danh_muc}
                          className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium"
                        >
                          {dm.ten_danh_muc}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400 italic">Chưa có tiện nghi được thêm.</p>
                  )}
                </div>

                {/* Hình ảnh */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                    Hình Ảnh ({selectedDetail.hinh_anh?.length || 0})
                  </h4>
                  {selectedDetail.hinh_anh?.length > 0 ? (
                    <div className="grid grid-cols-3 gap-2">
                      {selectedDetail.hinh_anh.map((anh) => (
                        <img
                          key={anh.id_hinh_anh}
                          src={anh.duong_dan_anh}
                          alt="Khách sạn"
                          className="w-full h-24 object-cover rounded-xl border border-gray-200"
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400 italic">Chưa có hình ảnh nào được tải lên.</p>
                  )}
                </div>
              </div>
            ) : null}

            <div className="px-6 py-4 border-t border-gray-100 flex justify-end">
              <button
                onClick={() => setIsDetailModalOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal Xác Nhận Xóa Mềm ─────────────────────────────────────────── */}
      {deleteConfirm.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 text-center border border-gray-100 animate-in zoom-in-95">
            <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Trash2 className="w-6 h-6" />
            </div>

            <h3 className="text-lg font-bold text-gray-900">
              {deleteConfirm.isBulk
                ? "Xác nhận xóa các khách sạn đã chọn?"
                : "Xác nhận xóa khách sạn?"}
            </h3>

            <p className="text-sm text-gray-500 mt-2 mb-6">
              {deleteConfirm.isBulk
                ? `Hành động này sẽ xóa mềm ${selectedHotels.size} khách sạn đã chọn khỏi danh sách khả dụng.`
                : `Hành động này sẽ xóa mềm khách sạn "${deleteConfirm.hotelName}" (ID: #${deleteConfirm.hotelId}) khỏi danh sách hiển thị.`}
            </p>

            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setDeleteConfirm({ isOpen: false })}
                disabled={actionLoading}
                className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
              >
                Hủy bỏ
              </button>

              <button
                onClick={() => {
                  if (deleteConfirm.isBulk) {
                    handleBulkDelete();
                  } else if (deleteConfirm.hotelId) {
                    handleDeleteHotel(deleteConfirm.hotelId);
                  }
                }}
                disabled={actionLoading}
                className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors shadow-sm disabled:opacity-50"
              >
                {actionLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>{actionLoading ? "Đang xóa..." : "Xác nhận xóa"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
