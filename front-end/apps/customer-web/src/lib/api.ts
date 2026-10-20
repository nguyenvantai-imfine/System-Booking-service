import { createApiClient } from "@repo/api-client";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_HOTEL_API_URL || "http://localhost:8000/api/v1";

export const USER_API_BASE_URL =
  process.env.NEXT_PUBLIC_USER_API_URL || "http://localhost:8001/api/v1";

export const ROOM_API_BASE_URL =
  process.env.NEXT_PUBLIC_ROOM_API_URL || "http://localhost:8002/api/v1";

export const BOOKING_API_BASE_URL =
  process.env.NEXT_PUBLIC_BOOKING_API_URL || "http://localhost:8003/api/v1";

export const PAYMENT_API_BASE_URL =
  process.env.NEXT_PUBLIC_PAYMENT_API_URL || "http://localhost:8004/api/v1";

export const NOTIFICATION_API_BASE_URL =
  process.env.NEXT_PUBLIC_NOTIFICATION_API_URL || "http://localhost:8005/api/v1";

export const GATEWAY_API_BASE_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080/api/v1";

export const apiClient = createApiClient({
  baseUrl: API_BASE_URL,
  userServiceUrl: USER_API_BASE_URL,
  roomServiceUrl: ROOM_API_BASE_URL,
  bookingServiceUrl: BOOKING_API_BASE_URL,
  paymentServiceUrl: PAYMENT_API_BASE_URL,
  notificationServiceUrl: NOTIFICATION_API_BASE_URL,
  gatewayUrl: GATEWAY_API_BASE_URL,
  getAuthToken: () => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("customer_token");
      if (stored) return stored;
    }
    return null;
  },
});
