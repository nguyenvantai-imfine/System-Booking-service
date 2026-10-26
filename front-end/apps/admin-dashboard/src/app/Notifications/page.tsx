"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Bell,
  Check,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Mail,
  RefreshCw,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@repo/ui/button";
import type { ThongBaoItem, TrangThaiThongBao } from "@repo/types";
import { apiClient } from "@/lib/api";

const PAGE_SIZE = 15;

const notificationTypeLabels: Record<string, string> = {
  BOOKING_CONFIRMED: "Xác nhận đặt phòng",
  PAYMENT_SUCCESS: "Thanh toán thành công",
  BOOKING_CANCELLED: "Hủy đặt phòng",
  OTP: "Mã OTP",
  SYSTEM: "Hệ thống",
};

const deliveryStatusLabels: Record<TrangThaiThongBao, string> = {
  SENT: "Đã gửi",
  FAILED: "Thất bại",
  PENDING: "Đang chờ",
};

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<ThongBaoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    if (!toastMessage) return;
    const timer = setTimeout(() => setToastMessage(null), 3500);
    return () => clearTimeout(timer);
  }, [toastMessage]);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await apiClient.getNotifications({
        status: statusFilter === "all" ? undefined : statusFilter,
        page,
        page_size: PAGE_SIZE,
      });
      setNotifications(result.items);
      setTotal(result.total);
      setTotalPages(result.total_pages || 1);
    } catch (error) {
      setToastMessage({
        type: "error",
        text: getErrorMessage(error, "Không thể tải danh sách thông báo."),
      });
    } finally {
      setIsLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    void fetchNotifications();
  }, [fetchNotifications]);

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const handleMarkAsRead = async (notification: ThongBaoItem) => {
    setBusyId(notification.id_thong_bao);
    try {
      const updated = await apiClient.markNotificationAsRead(
        notification.id_thong_bao,
      );
      setNotifications((current) =>
        current.map((item) =>
          item.id_thong_bao === updated.id_thong_bao ? updated : item,
        ),
      );
      setToastMessage({
        type: "success",
        text: `Đã đánh dấu thông báo #${notification.id_thong_bao} là đã đọc.`,
      });
    } catch (error) {
      setToastMessage({
        type: "error",
        text: getErrorMessage(error, "Không thể đánh dấu thông báo đã đọc."),
      });
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (notification: ThongBaoItem) => {
    const confirmed = window.confirm(
      `Bạn có chắc muốn xóa thông báo #${notification.id_thong_bao}?`,
    );
    if (!confirmed) return;

    setBusyId(notification.id_thong_bao);
    try {
      await apiClient.deleteNotification(notification.id_thong_bao);
      setNotifications((current) =>
        current.filter(
          (item) => item.id_thong_bao !== notification.id_thong_bao,
        ),
      );
      const nextTotal = Math.max(0, total - 1);
      setTotal(nextTotal);
      setTotalPages(Math.max(1, Math.ceil(nextTotal / PAGE_SIZE)));
      if (notifications.length === 1 && page > 1) {
        setPage((current) => Math.max(1, current - 1));
      }
      setToastMessage({
        type: "success",
        text: `Đã xóa thông báo #${notification.id_thong_bao}.`,
      });
    } catch (error) {
      setToastMessage({
        type: "error",
        text: getErrorMessage(error, "Không thể xóa thông báo."),
      });
    } finally {
      setBusyId(null);
    }
  };

  const getDeliveryStatusBadge = (status: TrangThaiThongBao) => {
    const styles: Record<TrangThaiThongBao, string> = {
      SENT: "bg-emerald-50 text-emerald-700 border-emerald-200",
      FAILED: "bg-rose-50 text-rose-700 border-rose-200",
      PENDING: "bg-amber-50 text-amber-700 border-amber-200",
    };

    return (
      <span
        className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[status]}`}
      >
        {deliveryStatusLabels[status]}
      </span>
    );
  };

  return (
    <div className="space-y-6 p-6">
      {toastMessage && (
        <div
          role="status"
          aria-live="polite"
          className={`fixed bottom-5 right-5 z-50 flex max-w-md items-center gap-2 rounded-xl border px-4 py-3 text-sm shadow-lg ${
            toastMessage.type === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-rose-200 bg-rose-50 text-rose-800"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle className="h-5 w-5 shrink-0 text-emerald-600" />
          ) : (
            <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />
          )}
          <span>{toastMessage.text}</span>
          <button
            type="button"
            onClick={() => setToastMessage(null)}
            aria-label="Đóng thông báo"
            className="ml-2 hover:opacity-75"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <span className="rounded-xl bg-blue-100 p-2.5 text-blue-700">
              <Bell className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Quản lý thông báo
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Theo dõi trạng thái gửi và quản lý thông báo của tài khoản.
              </p>
            </div>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => void fetchNotifications()}
          disabled={isLoading}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
          />
          Làm mới
        </Button>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Tổng thông báo theo bộ lọc
          </p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{total}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Chưa đọc trên trang này
          </p>
          <p className="mt-2 text-3xl font-bold text-blue-700">
            {notifications.filter((item) => !item.is_read).length}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Đã đọc trên trang này
          </p>
          <p className="mt-2 text-3xl font-bold text-emerald-700">
            {notifications.filter((item) => item.is_read).length}
          </p>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-semibold text-slate-900">Danh sách thông báo</h2>
            <p className="mt-1 text-xs text-slate-500">
              Hiển thị {notifications.length} / {total} thông báo
            </p>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span>Trạng thái gửi</span>
            <select
              value={statusFilter}
              onChange={(event) => handleStatusFilterChange(event.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả</option>
              <option value="SENT">Đã gửi</option>
              <option value="PENDING">Đang chờ</option>
              <option value="FAILED">Thất bại</option>
            </select>
          </label>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3 font-semibold">ID</th>
                <th className="px-5 py-3 font-semibold">Loại thông báo</th>
                <th className="px-5 py-3 font-semibold">Kênh gửi</th>
                <th className="px-5 py-3 font-semibold">Trạng thái gửi</th>
                <th className="px-5 py-3 font-semibold">Trạng thái đọc</th>
                <th className="px-5 py-3 text-center font-semibold">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-14 text-center text-slate-500">
                    <span className="inline-flex items-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Đang tải thông báo...
                    </span>
                  </td>
                </tr>
              ) : notifications.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-14 text-center">
                    <Mail className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                    <p className="font-medium text-slate-600">
                      Không có thông báo nào
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      Thử thay đổi bộ lọc hoặc tải lại danh sách.
                    </p>
                  </td>
                </tr>
              ) : (
                notifications.map((notification) => (
                  <tr
                    key={notification.id_thong_bao}
                    className={`transition-colors hover:bg-slate-50 ${
                      notification.is_read ? "" : "bg-blue-50/30"
                    }`}
                  >
                    <td className="whitespace-nowrap px-5 py-4 font-mono text-xs text-slate-500">
                      #{notification.id_thong_bao}
                    </td>
                    <td className="px-5 py-4">
                      <div className="font-medium text-slate-800">
                        {notificationTypeLabels[notification.loai_thong_bao] ??
                          notification.loai_thong_bao}
                      </div>
                      <div className="mt-1 text-xs text-slate-400">
                        {notification.loai_thong_bao}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-center gap-2 text-slate-700">
                        <Mail className="h-4 w-4 text-slate-400" />
                        {notification.kenh_gui === "IN_APP"
                          ? "In-App"
                          : notification.kenh_gui === "EMAIL"
                            ? "Email"
                            : notification.kenh_gui}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {getDeliveryStatusBadge(notification.trang_thai)}
                    </td>
                    <td className="px-5 py-4">
                      {notification.is_read ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                          <Check className="h-4 w-4" />
                          Đã đọc
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700">
                          <span className="h-2 w-2 rounded-full bg-blue-500" />
                          Chưa đọc
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-center gap-2">
                        {!notification.is_read && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            disabled={busyId === notification.id_thong_bao}
                            onClick={() => void handleMarkAsRead(notification)}
                            title="Đánh dấu đã đọc"
                          >
                            <Check className="mr-1.5 h-4 w-4" />
                            Đánh dấu đã đọc
                          </Button>
                        )}
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                          disabled={busyId === notification.id_thong_bao}
                          onClick={() => void handleDelete(notification)}
                          title="Xóa thông báo"
                        >
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">Xóa</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 px-5 py-4 text-xs text-slate-500">
          <span>
            Trang <span className="font-semibold text-slate-800">{page}</span>{" "}
            / {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page <= 1 || isLoading}
              aria-label="Trang trước"
              className="rounded-lg border border-slate-200 p-1.5 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() =>
                setPage((current) => Math.min(totalPages, current + 1))
              }
              disabled={page >= totalPages || isLoading}
              aria-label="Trang sau"
              className="rounded-lg border border-slate-200 p-1.5 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
