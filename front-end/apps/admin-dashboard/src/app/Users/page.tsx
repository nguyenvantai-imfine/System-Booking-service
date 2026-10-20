"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Filter,
  Plus,
  Lock,
  Unlock,
  Shield,
  Eye,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X,
  ChevronLeft,
  ChevronRight,
  User as UserIcon,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type {
  TaiKhoanResponse,
  VaiTro,
  TrangThaiTaiKhoan,
  RegisterRequest,
} from "@repo/types";

export default function UsersPage() {
  const router = useRouter();

  // Dữ liệu người dùng từ user-service
  const [users, setUsers] = useState<TaiKhoanResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  // Bộ lọc
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Trạng thái giao diện
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Modal xem chi tiết người dùng
  const [viewingUser, setViewingUser] = useState<TaiKhoanResponse | null>(null);

  // Modal thêm người dùng mới
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newUserForm, setNewUserForm] = useState<RegisterRequest>({
    ten_dang_nhap: "",
    email: "",
    mat_khau: "",
    sdt: "",
    vai_tro: "CUSTOMER",
    ho: "",
    ten: "",
  });

  // Debounce tìm kiếm
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedKeyword(searchTerm);
      setPage(1);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Tự động tắt toast sau 3.5s
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Hàm tải danh sách người dùng từ backend
  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.getAdminUsers({
        page,
        page_size: pageSize,
        keyword: debouncedKeyword || undefined,
        vai_tro: roleFilter !== "all" ? (roleFilter as VaiTro) : undefined,
        trang_thai:
          statusFilter !== "all" ? (statusFilter as TrangThaiTaiKhoan) : undefined,
      });

      setUsers(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      if (err?.statusCode === 401) {
        setError(
          "Phiên đăng nhập đã hết hạn hoặc bạn chưa đăng nhập với vai trò Quản trị viên."
        );
      } else if (err?.statusCode === 403) {
        setError("Chỉ tài khoản Quản trị viên (Admin) mới có quyền xem danh sách này.");
      } else {
        setError("Không thể tải danh sách người dùng. Vui lòng kiểm tra user-service.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [page, debouncedKeyword, roleFilter, statusFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Xác nhận đổi trạng thái
  const [statusConfirm, setStatusConfirm] = useState<{
    user: TaiKhoanResponse;
    nextStatus: TrangThaiTaiKhoan;
  } | null>(null);

  // Xử lý Khóa / Mở khóa tài khoản
  const handleToggleStatus = (user: TaiKhoanResponse) => {
    const nextStatus: TrangThaiTaiKhoan =
      user.trang_thai === "ACTIVE" ? "LOCKED" : "ACTIVE";
    setStatusConfirm({ user, nextStatus });
  };

  const executeStatusChange = async () => {
    if (!statusConfirm) return;
    const { user, nextStatus } = statusConfirm;
    const actionText = nextStatus === "LOCKED" ? "khóa" : "mở khóa";

    try {
      await apiClient.changeUserStatus(user.id_tai_khoan, nextStatus);
      setToastMessage({
        type: "success",
        text: `Đã ${actionText} thành công tài khoản "${user.ten_dang_nhap}".`,
      });
      setStatusConfirm(null);
      fetchUsers();
    } catch (err: any) {
      const msg = err?.data?.detail || "Thao tác thay đổi trạng thái thất bại.";
      setToastMessage({
        type: "error",
        text: msg,
      });
      setStatusConfirm(null);
    }
  };

  // Xử lý tạo tài khoản mới từ Admin
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.register(newUserForm);
      setToastMessage({
        type: "success",
        text: `Đã tạo thành công tài khoản "${newUserForm.ten_dang_nhap}"!`,
      });
      setIsAddModalOpen(false);
      setNewUserForm({
        ten_dang_nhap: "",
        email: "",
        mat_khau: "",
        sdt: "",
        vai_tro: "CUSTOMER",
        ho: "",
        ten: "",
      });
      fetchUsers();
    } catch (err: any) {
      const msg = err?.data?.detail || "Không thể tạo tài khoản. Vui lòng kiểm tra lại.";
      setToastMessage({
        type: "error",
        text: msg,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: TrangThaiTaiKhoan) => {
    switch (status) {
      case "ACTIVE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            Hoạt động
          </span>
        );
      case "LOCKED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            Đã khóa
          </span>
        );
      case "INACTIVE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
            Tạm dừng
          </span>
        );
      default:
        return null;
    }
  };

  const getRoleBadge = (role: VaiTro) => {
    switch (role) {
      case "ADMIN":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <Shield className="w-3 h-3" />
            Quản trị viên
          </span>
        );
      case "PARTNER":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Đối tác (Partner)
          </span>
        );
      case "CUSTOMER":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Khách hàng
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
              ? "bg-green-50 border-green-200 text-green-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          )}
          <span>{toastMessage.text}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="ml-2 hover:opacity-75"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Thông báo lỗi phiên xác thực */}
      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between text-amber-800 text-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => router.push("/login")}
            className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-semibold hover:bg-amber-700 transition"
          >
            Đến trang Đăng Nhập
          </button>
        </div>
      )}

      {/* Thanh công cụ: Tìm kiếm, Bộ lọc & Thao tác */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          {/* Ô tìm kiếm */}
          <div className="relative flex-1 w-full lg:max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm theo tên đăng nhập, email, số điện thoại..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 focus:bg-white transition"
            />
          </div>

          {/* Bộ lọc vai trò & trạng thái */}
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setPage(1);
                }}
                className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="all">Tất cả Vai trò</option>
                <option value="ADMIN">Quản trị viên (Admin)</option>
                <option value="PARTNER">Đối tác (Partner)</option>
                <option value="CUSTOMER">Khách hàng (Customer)</option>
              </select>
            </div>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">Tất cả Trạng thái</option>
              <option value="ACTIVE">Đang hoạt động</option>
              <option value="LOCKED">Đã khóa</option>
              <option value="INACTIVE">Tạm dừng</option>
            </select>

            <button
              onClick={() => {
                setSearchTerm("");
                setRoleFilter("all");
                setStatusFilter("all");
                setPage(1);
              }}
              className="px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded-xl hover:bg-slate-50 transition"
            >
              Đặt lại
            </button>

            <button
              onClick={fetchUsers}
              title="Làm mới dữ liệu"
              className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>

            {/* Nút Thêm người dùng mới */}
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 shadow-sm transition"
            >
              <Plus className="w-4 h-4" />
              <span>Thêm Tài Khoản</span>
            </button>
          </div>
        </div>
      </div>

      {/* Bảng danh sách người dùng */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="px-5 py-3.5">ID</th>
                <th className="px-5 py-3.5">Người dùng</th>
                <th className="px-5 py-3.5">Email</th>
                <th className="px-5 py-3.5">Số điện thoại</th>
                <th className="px-5 py-3.5">Vai trò</th>
                <th className="px-5 py-3.5">Trạng thái</th>
                <th className="px-5 py-3.5">Ngày tạo</th>
                <th className="px-5 py-3.5 text-center">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                    Đang tải danh sách tài khoản...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-500">
                    Không tìm thấy tài khoản người dùng nào phù hợp.
                  </td>
                </tr>
              ) : (
                users.map((user) => {
                  const fullName =
                    [user.nguoi_dung?.ho, user.nguoi_dung?.ten]
                      .filter(Boolean)
                      .join(" ") || user.ten_dang_nhap;

                  const isLocked = user.trang_thai === "LOCKED";

                  return (
                    <tr
                      key={user.id_tai_khoan}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      <td className="px-5 py-4 font-mono text-xs text-slate-500">
                        #{user.id_tai_khoan}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          {user.nguoi_dung?.avatar ? (
                            <img
                              src={user.nguoi_dung.avatar}
                              alt={fullName}
                              className="w-9 h-9 rounded-full object-cover border border-slate-200"
                            />
                          ) : (
                            <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 font-semibold text-xs">
                              {fullName.charAt(0).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <div className="font-medium text-slate-900">
                              {fullName}
                            </div>
                            <div className="text-xs text-slate-400">
                              @{user.ten_dang_nhap}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-slate-600">{user.email}</td>
                      <td className="px-5 py-4 text-slate-600">
                        {user.sdt || "-"}
                      </td>
                      <td className="px-5 py-4">{getRoleBadge(user.vai_tro)}</td>
                      <td className="px-5 py-4">
                        {getStatusBadge(user.trang_thai)}
                      </td>
                      <td className="px-5 py-4 text-slate-500 text-xs">
                        {new Date(user.ngay_tao).toLocaleDateString("vi-VN", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                        })}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center justify-center gap-1.5">
                          {/* Nút Xem chi tiết */}
                          <button
                            onClick={() => setViewingUser(user)}
                            title="Xem chi tiết hồ sơ"
                            className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {/* Nút Khóa / Mở Khóa */}
                          {isLocked ? (
                            <button
                              onClick={() => handleToggleStatus(user)}
                              title="Mở khóa tài khoản"
                              className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition"
                            >
                              <Unlock className="w-3.5 h-3.5" />
                              <span>Mở Khóa</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleToggleStatus(user)}
                              title="Khóa tài khoản"
                              className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition"
                            >
                              <Lock className="w-3.5 h-3.5" />
                              <span>Khóa</span>
                            </button>
                          )}
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
            Hiển thị <span className="font-medium text-slate-700">{users.length}</span>{" "}
            / <span className="font-medium text-slate-700">{total}</span> tài khoản
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

      {/* Modal Xem chi tiết người dùng */}
      {viewingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <UserIcon className="w-5 h-5 text-blue-600" />
                Hồ Sơ Người Dùng #{viewingUser.id_tai_khoan}
              </h3>
              <button
                onClick={() => setViewingUser(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-4 rounded-xl">
                <div>
                  <span className="text-xs text-slate-400 block">Tên đăng nhập</span>
                  <span className="font-semibold text-slate-800">
                    @{viewingUser.ten_dang_nhap}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Email</span>
                  <span className="font-semibold text-slate-800 truncate block">
                    {viewingUser.email}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Số điện thoại</span>
                  <span className="font-medium text-slate-800">
                    {viewingUser.sdt || "Chưa cập nhật"}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Vai trò</span>
                  <div>{getRoleBadge(viewingUser.vai_tro)}</div>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Trạng thái</span>
                  <div>{getStatusBadge(viewingUser.trang_thai)}</div>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Ngày tạo</span>
                  <span className="font-medium text-slate-800">
                    {new Date(viewingUser.ngay_tao).toLocaleString("vi-VN")}
                  </span>
                </div>
              </div>

              {/* Thông tin cá nhân Profile */}
              <div>
                <h4 className="font-semibold text-slate-800 mb-2">
                  Thông Tin Profile
                </h4>
                <div className="space-y-2 border border-slate-100 rounded-xl p-3">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Họ và tên:</span>
                    <span className="font-medium text-slate-800">
                      {[viewingUser.nguoi_dung?.ho, viewingUser.nguoi_dung?.ten]
                        .filter(Boolean)
                        .join(" ") || "Chưa cập nhật"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Giới tính:</span>
                    <span className="font-medium text-slate-800">
                      {viewingUser.nguoi_dung?.gioi_tinh || "Chưa cập nhật"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Địa chỉ:</span>
                    <span className="font-medium text-slate-800">
                      {viewingUser.nguoi_dung?.dia_chi || "Chưa cập nhật"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">CCCD / Định danh:</span>
                    <span className="font-medium text-slate-800">
                      {viewingUser.nguoi_dung?.cccd || "Chưa cập nhật"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setViewingUser(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-semibold transition"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Thêm người dùng mới */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Plus className="w-5 h-5 text-blue-600" />
                Tạo Tài Khoản Người Dùng Mới
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Tên đăng nhập *
                  </label>
                  <input
                    type="text"
                    required
                    value={newUserForm.ten_dang_nhap}
                    onChange={(e) =>
                      setNewUserForm({
                        ...newUserForm,
                        ten_dang_nhap: e.target.value,
                      })
                    }
                    placeholder="ví dụ: user123"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Email *
                  </label>
                  <input
                    type="email"
                    required
                    value={newUserForm.email}
                    onChange={(e) =>
                      setNewUserForm({ ...newUserForm, email: e.target.value })
                    }
                    placeholder="user@example.com"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Mật khẩu *
                  </label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={newUserForm.mat_khau}
                    onChange={(e) =>
                      setNewUserForm({ ...newUserForm, mat_khau: e.target.value })
                    }
                    placeholder="Tối thiểu 6 ký tự"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Số điện thoại
                  </label>
                  <input
                    type="text"
                    value={newUserForm.sdt || ""}
                    onChange={(e) =>
                      setNewUserForm({ ...newUserForm, sdt: e.target.value })
                    }
                    placeholder="0901234567"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Họ đệm
                  </label>
                  <input
                    type="text"
                    value={newUserForm.ho || ""}
                    onChange={(e) =>
                      setNewUserForm({ ...newUserForm, ho: e.target.value })
                    }
                    placeholder="Nguyễn Văn"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Tên
                  </label>
                  <input
                    type="text"
                    value={newUserForm.ten || ""}
                    onChange={(e) =>
                      setNewUserForm({ ...newUserForm, ten: e.target.value })
                    }
                    placeholder="An"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Vai trò tài khoản *
                </label>
                <select
                  value={newUserForm.vai_tro}
                  onChange={(e) =>
                    setNewUserForm({
                      ...newUserForm,
                      vai_tro: e.target.value as "CUSTOMER" | "PARTNER",
                    })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="CUSTOMER">Khách hàng (CUSTOMER)</option>
                  <option value="PARTNER">Chủ khách sạn (PARTNER)</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-semibold transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold disabled:opacity-50 transition"
                >
                  {isSubmitting ? "Đang tạo..." : "Tạo Tài Khoản"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Xác nhận Khóa / Mở khóa tài khoản */}
      {statusConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-sm w-full p-6 space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center gap-3">
              {statusConfirm.nextStatus === "LOCKED" ? (
                <div className="p-3 bg-rose-100 text-rose-600 rounded-xl">
                  <Lock className="w-6 h-6" />
                </div>
              ) : (
                <div className="p-3 bg-emerald-100 text-emerald-600 rounded-xl">
                  <Unlock className="w-6 h-6" />
                </div>
              )}
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {statusConfirm.nextStatus === "LOCKED"
                    ? "Khóa tài khoản"
                    : "Mở khóa tài khoản"}
                </h3>
                <p className="text-xs text-slate-500">
                  @{statusConfirm.user.ten_dang_nhap}
                </p>
              </div>
            </div>

            <p className="text-sm text-slate-600">
              Bạn có chắc chắn muốn{" "}
              {statusConfirm.nextStatus === "LOCKED" ? "khóa" : "mở khóa"} tài khoản{" "}
              <strong className="text-slate-800">
                {statusConfirm.user.email}
              </strong>
              ?
            </p>

            <div className="flex justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setStatusConfirm(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={executeStatusChange}
                className={`px-4 py-2 rounded-xl text-xs font-semibold text-white transition ${
                  statusConfirm.nextStatus === "LOCKED"
                    ? "bg-rose-600 hover:bg-rose-700"
                    : "bg-emerald-600 hover:bg-emerald-700"
                }`}
              >
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

