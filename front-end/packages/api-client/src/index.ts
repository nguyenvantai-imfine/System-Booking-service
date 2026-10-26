import type {
  ApiResponse,
  PaginatedResponse,
  Hotel,
  Room,
  Booking,
  User,
  KhachSanBrief,
  KhachSanDetail,
  HotelServicePaginatedResponse,
  GetHotelsParams,
  CreateHotelInput,
  UpdateHotelInput,
  TrangThaiKhachSan,
  VaiTro,
  TrangThaiTaiKhoan,
  NguoiDungProfile,
  TaiKhoanResponse,
  TokenResponse,
  LoginRequest,
  RegisterRequest,
  UserPaginatedResponse,
  GetUsersAdminParams,
  UserActionResponse,
  TrangThaiPhong,
  TienIchPhong,
  QuyTacPhong,
  KhuyenMaiPhong,
  LoaiPhongBrief,
  LoaiPhongDetail,
  CreateLoaiPhongInput,
  PhongItem,
  PaginatedRooms,
  GetRoomsParams,
  BatchCreateRoomsInput,
  TrangThaiBooking,
  ThongTinKhachO,
  ChiTietDatPhong,
  NhatKyBooking,
  DatPhongItem,
  PaginatedBookings,
  GetBookingsParams,
  PhuongThucThanhToan,
  TrangThaiThanhToan,
  ThanhToanItem,
  PaymentResponse,
  CreatePaymentRequest,
  GenerateOtpRequest,
  VerifyOtpRequest,
  OtpResponse,
  SimulateIpnRequest,
  PaginatedPayments,
  PaymentStats,
  GetPaymentsParams,
  ThongBaoItem,
  PaginatedNotifications,
  NotificationStats,
} from "@repo/types";

export interface ApiClientConfig {
  baseUrl: string;
  userServiceUrl?: string;
  roomServiceUrl?: string;
  bookingServiceUrl?: string;
  paymentServiceUrl?: string;
  notificationServiceUrl?: string;
  gatewayUrl?: string;
  getAuthToken?: () => string | null | Promise<string | null>;
}

export class ApiError extends Error {
  statusCode: number;
  data?: unknown;

  constructor(message: string, statusCode: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.data = data;
  }
}

export class ApiClient {
  private baseUrl: string;
  private userServiceUrl: string;
  private roomServiceUrl: string;
  private bookingServiceUrl: string;
  private paymentServiceUrl: string;
  private notificationServiceUrl: string;
  private gatewayUrl?: string;
  private getAuthToken?: () => string | null | Promise<string | null>;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.userServiceUrl = (config.userServiceUrl || "http://localhost:8001/api/v1").replace(/\/$/, "");
    this.roomServiceUrl = (config.roomServiceUrl || "http://localhost:8002/api/v1").replace(/\/$/, "");
    this.bookingServiceUrl = (config.bookingServiceUrl || "http://localhost:8003/api/v1").replace(/\/$/, "");
    this.paymentServiceUrl = (config.paymentServiceUrl || "http://localhost:8004/api/v1").replace(/\/$/, "");
    this.notificationServiceUrl = (config.notificationServiceUrl || "http://localhost:8005/api/v1").replace(/\/$/, "");
    this.gatewayUrl = config.gatewayUrl?.replace(/\/$/, "");
    this.getAuthToken = config.getAuthToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    customBaseUrl?: string
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    const token = this.getAuthToken ? await this.getAuthToken() : "1";
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const base = customBaseUrl || this.baseUrl;
    const url = `${base}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorBody: unknown;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }

      let errorMessage = `API request failed with status ${response.status}`;
      if (typeof errorBody === "object" && errorBody !== null) {
        const bodyObj = errorBody as Record<string, unknown>;
        if (typeof bodyObj.detail === "string" && bodyObj.detail.trim()) {
          errorMessage = bodyObj.detail.trim();
        } else if (Array.isArray(bodyObj.detail) && bodyObj.detail.length > 0) {
          const msgs = bodyObj.detail
            .map((item: any) => item?.msg || item?.message || JSON.stringify(item))
            .filter(Boolean);
          if (msgs.length > 0) {
            errorMessage = msgs.join("; ");
          }
        } else if (typeof bodyObj.message === "string" && bodyObj.message.trim()) {
          errorMessage = bodyObj.message.trim();
        }
      } else if (typeof errorBody === "string" && errorBody.trim()) {
        errorMessage = errorBody.trim();
      }

      throw new ApiError(
        errorMessage,
        response.status,
        errorBody
      );
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json() as Promise<T>;
  }

  // Generic methods
  public get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  public post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  // ============================================================================
  // USER SERVICE / AUTH METHODS (Microservice User API)
  // ============================================================================

  public async login(data: LoginRequest): Promise<TokenResponse> {
    return this.request<TokenResponse>(
      "/auth/login",
      { method: "POST", body: JSON.stringify(data) },
      this.userServiceUrl
    );
  }

  public async register(data: RegisterRequest): Promise<TokenResponse> {
    return this.request<TokenResponse>(
      "/auth/register",
      { method: "POST", body: JSON.stringify(data) },
      this.userServiceUrl
    );
  }

  public async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return this.request<TokenResponse>(
      "/auth/refresh",
      { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) },
      this.userServiceUrl
    );
  }

  public async getMe(): Promise<TaiKhoanResponse> {
    return this.request<TaiKhoanResponse>(
      "/users/me",
      { method: "GET" },
      this.userServiceUrl
    );
  }

  public async updateProfile(
    data: Partial<NguoiDungProfile>
  ): Promise<NguoiDungProfile> {
    return this.request<NguoiDungProfile>(
      "/users/me",
      { method: "PUT", body: JSON.stringify(data) },
      this.userServiceUrl
    );
  }

  public async getAdminUsers(
    params?: GetUsersAdminParams
  ): Promise<UserPaginatedResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.vai_tro && params.vai_tro !== "all") {
      query.set("role", params.vai_tro);
      query.set("vai_tro", params.vai_tro);
    }
    if (params?.trang_thai && params.trang_thai !== "all") {
      query.set("status", params.trang_thai);
      query.set("trang_thai", params.trang_thai);
    }
    if (params?.keyword) {
      query.set("keyword", params.keyword.trim());
    }

    const qs = query.toString();
    return this.request<UserPaginatedResponse>(
      `/admin/users${qs ? `?${qs}` : ""}`,
      { method: "GET" },
      this.userServiceUrl
    );
  }

  public async adminCreateUser(
    data: RegisterRequest
  ): Promise<TaiKhoanResponse> {
    return this.request<TaiKhoanResponse>(
      "/admin/users",
      { method: "POST", body: JSON.stringify(data) },
      this.userServiceUrl
    );
  }

  public async getUserById(userId: number): Promise<TaiKhoanResponse> {
    return this.request<TaiKhoanResponse>(
      `/admin/users/${userId}`,
      { method: "GET" },
      this.userServiceUrl
    );
  }

  public async changeUserStatus(
    userId: number,
    status: TrangThaiTaiKhoan
  ): Promise<TaiKhoanResponse> {
    return this.request<TaiKhoanResponse>(
      `/admin/users/${userId}/status`,
      { method: "PATCH", body: JSON.stringify({ trang_thai: status }) },
      this.userServiceUrl
    );
  }

  public async adminDeleteUser(userId: number): Promise<UserActionResponse> {
    return this.request<UserActionResponse>(
      `/admin/users/${userId}`,
      { method: "DELETE" },
      this.userServiceUrl
    );
  }

  public async deleteMyAccount(): Promise<UserActionResponse> {
    return this.request<UserActionResponse>(
      "/users/me",
      { method: "DELETE" },
      this.userServiceUrl
    );
  }


  // ============================================================================
  // HOTEL SERVICE METHODS (Khách sạn)
  // ============================================================================

  public async getHotels(
    params?: GetHotelsParams
  ): Promise<HotelServicePaginatedResponse<KhachSanBrief>> {
    const query = new URLSearchParams();
    if (params?.keyword) query.set("keyword", params.keyword.trim());
    if (params?.city && params.city !== "all") query.set("city", params.city);
    if (params?.district && params.district !== "all") query.set("district", params.district);
    if (params?.trang_thai && (params.trang_thai as string) !== "all") {
      query.set("trang_thai", params.trang_thai);
    }
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());

    if (params?.amenities && params.amenities.length > 0) {
      params.amenities.forEach((a) => query.append("amenities", a));
    }

    const qs = query.toString();
    return this.get<HotelServicePaginatedResponse<KhachSanBrief>>(`/hotels${qs ? `?${qs}` : ""}`);
  }

  public async getHotelById(id: number | string): Promise<KhachSanDetail> {
    return this.get<KhachSanDetail>(`/hotels/${id}`);
  }

  public async createHotel(data: CreateHotelInput): Promise<KhachSanDetail> {
    return this.post<KhachSanDetail>("/hotels/", data);
  }

  public async updateHotel(
    id: number | string,
    data: UpdateHotelInput
  ): Promise<KhachSanDetail> {
    return this.put<KhachSanDetail>(`/hotels/${id}`, data);
  }

  public async changeHotelStatus(
    id: number | string,
    trang_thai: TrangThaiKhachSan
  ): Promise<KhachSanDetail> {
    return this.patch<KhachSanDetail>(`/hotels/${id}/status`, { trang_thai });
  }

  public async deleteHotel(
    id: number | string
  ): Promise<{ message: string; id_khach_san: number }> {
    return this.delete<{ message: string; id_khach_san: number }>(`/hotels/${id}`);
  }

  public async restoreHotel(id: number | string): Promise<KhachSanDetail> {
    return this.post<KhachSanDetail>(`/hotels/${id}/restore`);
  }

  // ============================================================================
  // ROOM SERVICE METHODS (Microservice Room API)
  // ============================================================================

  public async getRooms(params?: GetRoomsParams): Promise<PaginatedRooms> {
    const query = new URLSearchParams();
    if (params?.hotel_id) query.set("hotel_id", params.hotel_id.toString());
    if (params?.room_type_id) query.set("room_type_id", params.room_type_id.toString());
    if (params?.status && params.status !== "ALL" && params.status !== "all") {
      query.set("status", params.status);
    }
    if (params?.keyword) query.set("keyword", params.keyword.trim());
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());

    const qs = query.toString();
    return this.request<PaginatedRooms>(
      `/rooms${qs ? `?${qs}` : ""}`,
      { method: "GET" },
      this.roomServiceUrl
    );
  }

  public async getRoomsByHotelId(
    hotelId: number | string,
    params?: { status?: string; room_type_id?: number; page?: number; page_size?: number }
  ): Promise<PaginatedRooms> {
    const query = new URLSearchParams();
    if (params?.status && params.status !== "all") query.set("status", params.status);
    if (params?.room_type_id) query.set("room_type_id", params.room_type_id.toString());
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());

    const qs = query.toString();
    return this.request<PaginatedRooms>(
      `/hotels/${hotelId}/rooms${qs ? `?${qs}` : ""}`,
      { method: "GET" },
      this.roomServiceUrl
    );
  }

  public async getRoomById(id: number | string): Promise<PhongItem> {
    return this.request<PhongItem>(
      `/rooms/${id}`,
      { method: "GET" },
      this.roomServiceUrl
    );
  }

  public async createRoom(
    typeId: number | string,
    data: {
      so_phong: string;
      tang?: number;
      trang_thai?: TrangThaiPhong;
      ghi_chu?: string;
    }
  ): Promise<PhongItem> {
    return this.request<PhongItem>(
      `/room-types/${typeId}/rooms`,
      { method: "POST", body: JSON.stringify(data) },
      this.roomServiceUrl
    );
  }

  public async batchCreateRooms(
    typeId: number | string,
    data: BatchCreateRoomsInput
  ): Promise<PhongItem[]> {
    return this.request<PhongItem[]>(
      `/room-types/${typeId}/rooms/batch`,
      { method: "POST", body: JSON.stringify(data) },
      this.roomServiceUrl
    );
  }

  public async changeRoomStatus(
    id: number | string,
    status: TrangThaiPhong,
    ghi_chu?: string
  ): Promise<PhongItem> {
    return this.request<PhongItem>(
      `/rooms/${id}/status`,
      {
        method: "PATCH",
        body: JSON.stringify({ trang_thai: status, ghi_chu }),
      },
      this.roomServiceUrl
    );
  }

  public async deleteRoom(id: number | string): Promise<void> {
    return this.request<void>(
      `/rooms/${id}`,
      { method: "DELETE" },
      this.roomServiceUrl
    );
  }

  public async getRoomTypesByHotel(
    hotelId: number | string
  ): Promise<LoaiPhongDetail[]> {
    return this.request<LoaiPhongDetail[]>(
      `/hotels/${hotelId}/room-types`,
      { method: "GET" },
      this.roomServiceUrl
    );
  }

  public async createRoomType(
    hotelId: number | string,
    data: CreateLoaiPhongInput
  ): Promise<LoaiPhongDetail> {
    return this.request<LoaiPhongDetail>(
      `/hotels/${hotelId}/room-types`,
      { method: "POST", body: JSON.stringify(data) },
      this.roomServiceUrl
    );
  }

  public async getAvailableRooms(params: {
    hotel_id: number;
    check_in: string;
    check_out: string;
    num_guests?: number;
  }): Promise<PhongItem[]> {
    const query = new URLSearchParams({
      hotel_id: params.hotel_id.toString(),
      check_in: params.check_in,
      check_out: params.check_out,
    });
    if (params.num_guests) query.set("num_guests", params.num_guests.toString());

    return this.request<PhongItem[]>(
      `/rooms/available?${query.toString()}`,
      { method: "GET" },
      this.roomServiceUrl
    );
  }

  // ============================================================================
  // BOOKING SERVICE METHODS (Microservice Booking API)
  // ============================================================================

  public async getBookings(params?: GetBookingsParams): Promise<PaginatedBookings> {
    const query = new URLSearchParams();
    if (params?.hotel_id) query.set("hotel_id", params.hotel_id.toString());
    if (params?.status && params.status !== "all") query.set("status", params.status);
    if (params?.keyword) query.set("keyword", params.keyword.trim());
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());

    const qs = query.toString();
    return this.request<PaginatedBookings>(
      `/bookings${qs ? `?${qs}` : ""}`,
      { method: "GET" },
      this.bookingServiceUrl
    );
  }

  public async getBookingDetail(idOrCode: string | number): Promise<DatPhongItem> {
    return this.request<DatPhongItem>(
      `/bookings/${idOrCode}`,
      { method: "GET" },
      this.bookingServiceUrl
    );
  }

  public async createBookingOrder(data: {
    id_khach_san: number;
    ngay_nhan_phong: string;
    ngay_tra_phong: string;
    rooms: Array<{
      id_phong: number;
      id_loai_phong: number;
      so_phong?: string;
      ten_loai_phong?: string;
      gia: number;
    }>;
    khach_o: {
      ho_ten: string;
      email: string;
      sdt: string;
      ghi_chu_dac_biet?: string;
    };
    id_tai_khoan?: number;
  }): Promise<DatPhongItem> {
    return this.request<DatPhongItem>(
      "/bookings",
      { method: "POST", body: JSON.stringify(data) },
      this.bookingServiceUrl
    );
  }

  public async confirmBooking(
    idOrCode: string | number,
    note?: string
  ): Promise<DatPhongItem> {
    const qs = note ? `?note=${encodeURIComponent(note)}` : "";
    return this.request<DatPhongItem>(
      `/bookings/${idOrCode}/confirm${qs}`,
      { method: "PATCH" },
      this.bookingServiceUrl
    );
  }

  public async cancelBooking(
    idOrCode: string | number,
    reason?: string
  ): Promise<DatPhongItem> {
    const qs = reason ? `?reason=${encodeURIComponent(reason)}` : "";
    return this.request<DatPhongItem>(
      `/bookings/${idOrCode}/cancel${qs}`,
      { method: "PATCH" },
      this.bookingServiceUrl
    );
  }

  // ============================================================================
  // PAYMENT SERVICE METHODS (Microservice Payment API)
  // ============================================================================

  public async getPayments(params?: GetPaymentsParams): Promise<PaginatedPayments> {
    const query = new URLSearchParams();
    if (params?.status && params.status !== "all") query.set("status", params.status);
    if (params?.method && params.method !== "all") query.set("method", params.method);
    if (params?.keyword) query.set("keyword", params.keyword.trim());
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());

    const qs = query.toString();
    return this.request<PaginatedPayments>(
      `/payments${qs ? `?${qs}` : ""}`,
      { method: "GET" },
      this.paymentServiceUrl
    );
  }

  public async getPaymentStats(): Promise<PaymentStats> {
    return this.request<PaymentStats>(
      "/payments/stats",
      { method: "GET" },
      this.paymentServiceUrl
    );
  }

  public async createPayment(
    data: CreatePaymentRequest & { idempotency_key?: string; idempotencyKey?: string },
    idempotencyKey?: string
  ): Promise<PaymentResponse> {
    const key = idempotencyKey || data.idempotency_key || data.idempotencyKey;
    const headers: Record<string, string> = {};
    if (key && key.trim()) {
      headers["X-Idempotency-Key"] = key.trim();
    }
    const { idempotency_key, idempotencyKey: _ik, ...payload } = data;
    return this.request<PaymentResponse>(
      "/payments/create-payment",
      {
        method: "POST",
        body: JSON.stringify(payload),
        headers,
      },
      this.paymentServiceUrl
    );
  }

  public async generatePaymentOtp(data: GenerateOtpRequest): Promise<OtpResponse> {
    return this.request<OtpResponse>(
      "/payments/generate-otp",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      this.paymentServiceUrl
    );
  }

  public async verifyPaymentOtp(data: VerifyOtpRequest): Promise<PaymentResponse> {
    return this.request<PaymentResponse>(
      "/payments/verify-otp",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      this.paymentServiceUrl
    );
  }

  public async simulateIpn(data: SimulateIpnRequest): Promise<PaymentResponse> {
    return this.request<PaymentResponse>(
      "/payments/simulate-ipn",
      { method: "POST", body: JSON.stringify(data) },
      this.paymentServiceUrl
    );
  }

  // ============================================================================
  // NOTIFICATION SERVICE ENDPOINTS
  // ============================================================================

  public async getNotifications(params?: {
    status?: string;
    notification_type?: string;
    recipient?: string;
    booking_code?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedNotifications> {
    const query = new URLSearchParams();
    if (params?.status && params.status !== "all") query.set("status", params.status);
    if (params?.notification_type && params.notification_type !== "all") query.set("notification_type", params.notification_type);
    if (params?.recipient) query.set("recipient", params.recipient.trim());
    if (params?.booking_code) query.set("booking_code", params.booking_code.trim());
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());

    const qs = query.toString();
    return this.request<PaginatedNotifications>(
      `/notifications${qs ? `?${qs}` : ""}`,
      { method: "GET" },
      this.notificationServiceUrl
    );
  }

  public async getNotificationStats(): Promise<NotificationStats> {
    return this.request<NotificationStats>(
      "/notifications/stats",
      { method: "GET" },
      this.notificationServiceUrl
    );
  }

  public async getNotificationDetail(id: number): Promise<ThongBaoItem> {
    return this.request<ThongBaoItem>(
      `/notifications/${id}`,
      { method: "GET" },
      this.notificationServiceUrl
    );
  }

  public async markNotificationAsRead(id: number): Promise<ThongBaoItem> {
    return this.request<ThongBaoItem>(
      `/notifications/${id}/read`,
      { method: "PATCH" },
      this.notificationServiceUrl
    );
  }

  public async deleteNotification(id: number): Promise<void> {
    return this.request<void>(
      `/notifications/${id}`,
      { method: "DELETE" },
      this.notificationServiceUrl
    );
  }

  public async sendNotification(data: {
    loai_thong_bao: string;
    nguoi_nhan: string;
    kenh_gui?: string;
    id_tai_khoan?: number;
    ma_booking?: string;
    du_lieu?: Record<string, any>;
  }): Promise<ThongBaoItem> {
    return this.request<ThongBaoItem>(
      "/notifications/send",
      { method: "POST", body: JSON.stringify(data) },
      this.notificationServiceUrl
    );
  }

  // Legacy compat
  public async createBooking(data: Partial<Booking>): Promise<ApiResponse<Booking>> {
    return this.post<ApiResponse<Booking>>("/bookings", data);
  }

  public async getBookingById(id: string): Promise<ApiResponse<Booking>> {
    return this.get<ApiResponse<Booking>>(`/bookings/${id}`);
  }

  public async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.get<ApiResponse<User>>("/users/me");
  }
}

export function createApiClient(config: ApiClientConfig): ApiClient {
  return new ApiClient(config);
}
