import type {
  ApiResponse,
  PaginatedResponse,
  Hotel,
  Room,
  Booking,
  User,
} from "@repo/types";

export interface ApiClientConfig {
  baseUrl: string;
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
  private getAuthToken?: () => string | null | Promise<string | null>;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.getAuthToken = config.getAuthToken;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.getAuthToken) {
      const token = await this.getAuthToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const url = `${this.baseUrl}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

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
      throw new ApiError(
        `API request failed with status ${response.status}`,
        response.status,
        errorBody
      );
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
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  // Pre-typed Service Methods
  public async getHotels(params?: {
    city?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Hotel>> {
    const query = new URLSearchParams();
    if (params?.city) query.set("city", params.city);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.limit) query.set("limit", params.limit.toString());
    const qs = query.toString();
    return this.get<PaginatedResponse<Hotel>>(`/hotels${qs ? `?${qs}` : ""}`);
  }

  public async getHotelById(id: string): Promise<ApiResponse<Hotel>> {
    return this.get<ApiResponse<Hotel>>(`/hotels/${id}`);
  }

  public async getRoomsByHotelId(hotelId: string): Promise<ApiResponse<Room[]>> {
    return this.get<ApiResponse<Room[]>>(`/hotels/${hotelId}/rooms`);
  }

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
