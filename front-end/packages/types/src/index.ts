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
