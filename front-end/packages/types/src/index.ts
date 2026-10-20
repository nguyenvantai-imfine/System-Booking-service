// User & Authentication Types
export enum UserRole {
  ADMIN = "admin",
  PARTNER = "partner",
  CUSTOMER = "customer",
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  role: UserRole;
  avatarUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// Hotel & Room Types
export type HotelStatus = "active" | "inactive" | "pending_approval";

export interface Address {
  street: string;
  city: string;
  state?: string;
  country: string;
  postalCode?: string;
  latitude?: number;
  longitude?: number;
}

export interface Hotel {
  id: string;
  ownerId: string;
  name: string;
  description: string;
  address: Address;
  starRating: number;
  ratingAverage: number;
  ratingCount: number;
  images: string[];
  amenities: string[];
  status: HotelStatus;
  createdAt: string;
  updatedAt: string;
}

export type RoomStatus = "available" | "occupied" | "maintenance" | "reserved";

export interface Room {
  id: string;
  hotelId: string;
  name: string;
  roomNumber?: string;
  type: string;
  capacity: number;
  pricePerNight: number;
  description?: string;
  amenities: string[];
  images: string[];
  status: RoomStatus;
  createdAt: string;
  updatedAt: string;
}

// Booking Types
export type BookingStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "refunded";

export interface BookingGuest {
  fullName: string;
  email: string;
  phone: string;
}

export interface Booking {
  id: string;
  userId: string;
  hotelId: string;
  roomId: string;
  checkInDate: string;
  checkOutDate: string;
  numberOfGuests: number;
  totalPrice: number;
  guest: BookingGuest;
  specialRequests?: string;
  status: BookingStatus;
  paymentId?: string;
  createdAt: string;
  updatedAt: string;
}

// Payment Types
export type PaymentStatus = "pending" | "processing" | "succeeded" | "failed" | "refunded";

export type PaymentMethod = "credit_card" | "momo" | "vnpay" | "bank_transfer" | "cash";

export interface Payment {
  id: string;
  bookingId: string;
  userId: string;
  amount: number;
  currency: string;
  method: PaymentMethod;
  status: PaymentStatus;
  transactionId?: string;
  paidAt?: string;
  createdAt: string;
  updatedAt: string;
}

// Notification Types
export type NotificationType =
  | "booking_confirmation"
  | "payment_success"
  | "booking_cancellation"
  | "system";

export interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: NotificationType;
  read: boolean;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

// API Response Models
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  totalItems: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMeta;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  statusCode: number;
  errors?: Record<string, string[]>;
}

// ==============================================================================
// HOTEL SERVICE SPECIFIC TYPES (Microservice Hotel API)
// ==============================================================================
export type TrangThaiKhachSan = "HOAT_DONG" | "TAM_DUNG" | "CHO_DUYET" | "DA_XOA";

export interface KhachSanBrief {
  id_khach_san: number;
  id_tai_khoan: number;
  ten_khach_san: string;
  email_khach_san?: string | null;
  sdt_khach_san?: string | null;
  trang_thai: TrangThaiKhachSan;
  dia_chi?: string | null;
  phuong_xa?: string | null;
  quan_huyen?: string | null;
  thanh_pho?: string | null;
  tinh?: string | null;
  quoc_gia?: string | null;
  kinh_do?: number | null;
  vi_do?: number | null;
  anh_dai_dien?: string | null;
  is_deleted: boolean;
  ngay_tao: string;
}

export interface KhachSanHinhAnh {
  id_hinh_anh: number;
  id_khach_san: number;
  duong_dan_anh: string;
  loai_anh?: string | null;
  la_anh_chinh: boolean;
  thu_tu: number;
  ngay_tao: string;
}

export interface KhachSanThongTin {
  id_thong_tin: number;
  id_khach_san: number;
  loai_thong_tin: string;
  noi_dung?: string | null;
}

export interface KhachSanQuyTac {
  id_quy_tac: number;
  id_khach_san: number;
  loai_chinh_sach: string;
  ten: string;
  gia_tri_chon?: string | null;
  mo_ta?: string | null;
}

export interface ChiTietTienNghi {
  id_tien_nghi: number;
  id_danh_muc: number;
  ten_tien_ich: string;
}

export interface DanhMucTienIch {
  id_danh_muc: number;
  id_khach_san: number;
  ten_danh_muc: string;
  icon_danh_muc?: string | null;
  chi_tiet_tien_nghi: ChiTietTienNghi[];
}

export interface KhachSanDetail extends KhachSanBrief {
  deleted_at?: string | null;
  ngay_cap_nhat: string;
  ten_nguoi_lien_he?: string | null;
  sdt_nguoi_lien_he?: string | null;
  ma_buu_chinh?: string | null;
  hinh_anh: KhachSanHinhAnh[];
  thong_tin: KhachSanThongTin[];
  quy_tac: KhachSanQuyTac[];
  danh_muc_tien_ich: DanhMucTienIch[];
}

export interface HotelServicePaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GetHotelsParams {
  keyword?: string;
  city?: string;
  district?: string;
  trang_thai?: TrangThaiKhachSan;
  amenities?: string[];
  page?: number;
  page_size?: number;
}

export interface CreateHotelInput {
  id_tai_khoan?: number;
  ten_khach_san: string;
  email_khach_san?: string;
  sdt_khach_san?: string;
  trang_thai?: TrangThaiKhachSan;
  dia_chi?: string;
  phuong_xa?: string;
  quan_huyen?: string;
  thanh_pho?: string;
  tinh?: string;
  quoc_gia?: string;
  ten_nguoi_lien_he?: string;
  sdt_nguoi_lien_he?: string;
  ma_buu_chinh?: string;
  kinh_do?: number;
  vi_do?: number;
  hinh_anh?: Array<{
    duong_dan_anh: string;
    loai_anh?: string;
    la_anh_chinh?: boolean;
    thu_tu?: number;
  }>;
  thong_tin?: Array<{ loai_thong_tin: string; noi_dung?: string }>;
  quy_tac?: Array<{ loai_chinh_sach?: string; ten: string; gia_tri_chon?: string; mo_ta?: string }>;
  danh_muc_tien_ich?: Array<{
    ten_danh_muc: string;
    icon_danh_muc?: string;
    chi_tiet_tien_nghi?: Array<{ ten_tien_ich: string }>;
  }>;
}

export interface UpdateHotelInput extends Partial<CreateHotelInput> {}

// ==============================================================================
// USER SERVICE & AUTH SPECIFIC TYPES (Microservice User API)
// ==============================================================================
export type VaiTro = "ADMIN" | "PARTNER" | "CUSTOMER";
export type TrangThaiTaiKhoan = "ACTIVE" | "LOCKED" | "INACTIVE";

export interface NguoiDungProfile {
  id_nguoi_dung: number;
  id_tai_khoan: number;
  ho?: string | null;
  ten?: string | null;
  ngay_sinh?: string | null;
  gioi_tinh?: string | null;
  dia_chi?: string | null;
  avatar?: string | null;
  cccd?: string | null;
}

export interface TaiKhoanResponse {
  id_tai_khoan: number;
  ten_dang_nhap: string;
  email: string;
  sdt?: string | null;
  vai_tro: VaiTro;
  trang_thai: TrangThaiTaiKhoan;
  ngay_tao: string;
  nguoi_dung?: NguoiDungProfile | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: TaiKhoanResponse;
}

export interface LoginRequest {
  ten_dang_nhap_hoac_email: string;
  mat_khau: string;
}

export interface RegisterRequest {
  ten_dang_nhap: string;
  email: string;
  mat_khau: string;
  sdt?: string;
  vai_tro?: "CUSTOMER" | "PARTNER";
  ho?: string;
  ten?: string;
}

export interface UserPaginatedResponse {
  items: TaiKhoanResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GetUsersAdminParams {
  page?: number;
  page_size?: number;
  vai_tro?: VaiTro | "all";
  trang_thai?: TrangThaiTaiKhoan | "all";
  keyword?: string;
}

// ==============================================================================
// ROOM SERVICE SPECIFIC TYPES (Microservice Room API)
// ==============================================================================
export type TrangThaiPhong = "AVAILABLE" | "OCCUPIED" | "MAINTENANCE" | "INACTIVE";

export interface TienIchPhong {
  id_tien_ich: number;
  id_loai_phong: number;
  ten_tien_ich: string;
  bieu_tuong?: string | null;
}

export interface QuyTacPhong {
  id_quy_tac: number;
  id_loai_phong: number;
  tieu_de: string;
  cho_phep: boolean;
  ghi_chu?: string | null;
}

export interface KhuyenMaiPhong {
  id_khuyen_mai: number;
  id_loai_phong: number;
  ma_khuyen_mai: string;
  ngay_bat_dau: string;
  ngay_ket_thuc: string;
  phan_tram_giam: number;
  mo_ta?: string | null;
}

export interface LoaiPhongBrief {
  id_loai_phong: number;
  id_khach_san: number;
  ten_loai_phong: string;
  mo_ta?: string | null;
  suc_chua_nguoi_lon: number;
  suc_chua_tre_em: number;
  gia_co_ban_mot_dem: number;
  dien_tich_m2?: number | null;
  so_luong_phong: number;
}

export interface LoaiPhongDetail extends LoaiPhongBrief {
  ngay_tao: string;
  ngay_cap_nhat: string;
  tien_ich: TienIchPhong[];
  quy_tac: QuyTacPhong[];
  khuyen_mai: KhuyenMaiPhong[];
}

export interface CreateLoaiPhongInput {
  ten_loai_phong: string;
  mo_ta?: string;
  suc_chua_nguoi_lon?: number;
  suc_chua_tre_em?: number;
  gia_co_ban_mot_dem: number;
  dien_tich_m2?: number;
  tien_ich?: Array<{ ten_tien_ich: string; bieu_tuong?: string }>;
  quy_tac?: Array<{ tieu_de: string; cho_phep?: boolean; ghi_chu?: string }>;
  khuyen_mai?: Array<{
    ma_khuyen_mai: string;
    ngay_bat_dau: string;
    ngay_ket_thuc: string;
    phan_tram_giam: number;
    mo_ta?: string;
  }>;
}

export interface PhongItem {
  id_phong: number;
  id_loai_phong: number;
  id_khach_san: number;
  so_phong: string;
  tang?: number | null;
  trang_thai: TrangThaiPhong;
  ghi_chu?: string | null;
  ngay_tao: string;
  ngay_cap_nhat: string;
  loai_phong?: LoaiPhongBrief | null;
}

export interface PaginatedRooms {
  items: PhongItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GetRoomsParams {
  hotel_id?: number;
  room_type_id?: number;
  status?: TrangThaiPhong | "ALL" | "all";
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface BatchCreateRoomsInput {
  prefix?: string;
  tang?: number;
  from_number?: number;
  to_number?: number;
  room_numbers?: string[];
}

// ==============================================================================
// BOOKING SERVICE SPECIFIC TYPES (Microservice Booking API)
// ==============================================================================
export type TrangThaiBooking =
  | "PENDING_PAYMENT"
  | "CONFIRMED"
  | "CANCELLED"
  | "COMPLETED"
  | "REFUNDED";

export interface ThongTinKhachO {
  id_khach_o: number;
  id_dat_phong: number;
  ho_ten: string;
  email: string;
  sdt: string;
  ghi_chu_dac_biet?: string | null;
}

export interface ChiTietDatPhong {
  id_chi_tiet: number;
  id_dat_phong: number;
  id_phong: number;
  id_loai_phong: number;
  so_phong?: string | null;
  ten_loai_phong?: string | null;
  gia_tai_thoi_diem_dat: number;
}

export interface NhatKyBooking {
  id_nhat_ky: number;
  trang_thai_cu?: string | null;
  trang_thai_moi: string;
  ly_do?: string | null;
  thoi_gian: string;
}

export interface DatPhongItem {
  id_dat_phong: number;
  ma_booking: string;
  id_tai_khoan: number;
  id_khach_san: number;
  ngay_nhan_phong: string;
  ngay_tra_phong: string;
  tong_tien: number;
  trang_thai: TrangThaiBooking;
  han_giu_cho: string;
  ngay_tao: string;
  ngay_cap_nhat: string;
  chi_tiet: ChiTietDatPhong[];
  khach_o?: ThongTinKhachO | null;
  nhat_ky: NhatKyBooking[];
}

export interface PaginatedBookings {
  items: DatPhongItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GetBookingsParams {
  hotel_id?: number;
  status?: TrangThaiBooking | "all";
  keyword?: string;
  page?: number;
  page_size?: number;
}

// ==============================================================================
// PAYMENT SERVICE SPECIFIC TYPES (Microservice Payment API)
// ==============================================================================
export type PhuongThucThanhToan = "VNPAY" | "MOMO" | "CREDIT_CARD" | "CASH";
export type TrangThaiThanhToan = "PENDING" | "SUCCESS" | "FAILED" | "REFUNDED";

export interface ThanhToanItem {
  id_thanh_toan: number;
  id_dat_phong: number;
  ma_booking: string;
  so_tien: number;
  phuong_thuc: PhuongThucThanhToan;
  trang_thai: TrangThaiThanhToan;
  ma_giao_dich_gateway: string;
  payment_url?: string | null;
  ngay_tao: string;
  ngay_thanh_toan?: string | null;
  ghi_chu?: string | null;
}

export interface PaginatedPayments {
  items: ThanhToanItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaymentStats {
  total_revenue: number;
  total_transactions: number;
  success_count: number;
  pending_count: number;
  failed_count: number;
}

export interface GetPaymentsParams {
  status?: string;
  method?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

// ==============================================================================
// NOTIFICATION SERVICE SPECIFIC TYPES (Microservice Notification API)
// ==============================================================================
export type LoaiThongBao =
  | "BOOKING_CONFIRMED"
  | "PAYMENT_SUCCESS"
  | "BOOKING_CANCELLED"
  | "SYSTEM";

export type TrangThaiThongBao = "SENT" | "FAILED" | "PENDING";

export interface NoiDungThongBaoItem {
  id_noi_dung: number;
  tieu_de: string;
  noi_dung_html: string;
  noi_dung_text?: string | null;
  du_lieu_dinh_kem?: string | null;
}

export interface ThongBaoItem {
  id_thong_bao: number;
  id_tai_khoan?: number | null;
  loai_thong_bao: LoaiThongBao;
  kenh_gui: string;
  nguoi_nhan: string;
  trang_thai: TrangThaiThongBao;
  ma_booking?: string | null;
  ngay_tao: string;
  ngay_gui?: string | null;
  ghi_chu_loi?: string | null;
  noi_dung?: NoiDungThongBaoItem | null;
}

export interface PaginatedNotifications {
  items: ThongBaoItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface NotificationStats {
  total_notifications: number;
  sent_count: number;
  failed_count: number;
  pending_count: number;
}


