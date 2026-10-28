import { createApiClient } from "@repo/api-client";

export const GATEWAY_API_BASE_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ||
  process.env.NEXT_PUBLIC_GATEWAY_API_URL ||
  "http://localhost:8080/api/v1";

export const API_BASE_URL = GATEWAY_API_BASE_URL;
export const USER_API_BASE_URL = GATEWAY_API_BASE_URL;
export const ROOM_API_BASE_URL = GATEWAY_API_BASE_URL;
export const BOOKING_API_BASE_URL = GATEWAY_API_BASE_URL;
export const PAYMENT_API_BASE_URL = GATEWAY_API_BASE_URL;
export const NOTIFICATION_API_BASE_URL = GATEWAY_API_BASE_URL;

export const apiClient = createApiClient({
  baseUrl: GATEWAY_API_BASE_URL,
  gatewayUrl: GATEWAY_API_BASE_URL,
  userServiceUrl: GATEWAY_API_BASE_URL,
  roomServiceUrl: GATEWAY_API_BASE_URL,
  bookingServiceUrl: GATEWAY_API_BASE_URL,
  paymentServiceUrl: GATEWAY_API_BASE_URL,
  notificationServiceUrl: GATEWAY_API_BASE_URL,
  getAuthToken: () => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("auth_token");
      if (stored) return stored;
    }
    return null;
  },
});
