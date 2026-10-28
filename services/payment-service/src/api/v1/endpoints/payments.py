from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.api.v1.dependencies import get_db, get_current_user_payload, require_admin
from src.schemas import (
    CreatePaymentRequest,
    SimulateIpnRequest,
    PaymentResponse,
    PaymentPaginatedResponse,
    PaymentStatsResponse,
    GenerateOtpRequest,
    VerifyOtpRequest,
    OtpResponse,
)
from src.services import PaymentService

router = APIRouter(prefix="/payments", tags=["💳 Quản lý Thanh Toán"])

# 1. Khởi tạo giao dịch thanh toán cho đơn đặt phòng
@router.post(
    "/create-payment",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Khởi tạo giao dịch thanh toán (Hỗ trợ Idempotency qua X-Idempotency-Key)",
)
def create_payment(
    payload: CreatePaymentRequest,
    x_idempotency_key: Optional[str] = Header(
        None,
        alias="X-Idempotency-Key",
        description="Khóa chống trùng lặp giao dịch (Idempotency Key)",
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    return PaymentService.create_payment(
        db=db, payload=payload, idempotency_key=x_idempotency_key
    )

# 2. Sinh mã OTP xác thực thanh toán
@router.post(
    "/generate-otp",
    response_model=OtpResponse,
    status_code=status.HTTP_200_OK,
    summary="Sinh mã OTP xác thực thanh toán",
    description="Tạo mã OTP 6 chữ số (hiệu lực 3 phút) cho giao dịch đang chờ thanh toán (PENDING), lưu DB và phát sự kiện gửi email qua RabbitMQ / Notification Service.",
)
async def generate_otp(
    payload: GenerateOtpRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    return await PaymentService.generate_otp(db, payload)

# 3. Xác thực mã OTP và hoàn tất thanh toán
@router.post(
    "/verify-otp",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Xác thực OTP và hoàn tất thanh toán",
    description="Xác thực mã OTP 6 chữ số, cập nhật trạng thái giao dịch sang SUCCESS, gọi đồng bộ Booking Service chuyển đơn sang CONFIRMED và kích hoạt gửi vé điện tử kèm mã QR.",
)
async def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    return await PaymentService.verify_otp(db, payload)

# 4. Mô phỏng IPN Callback từ cổng thanh toán (Sandbox)
@router.post(
    "/simulate-ipn",
    response_model=PaymentResponse,
    summary="Mô phỏng IPN Callback cổng thanh toán (Sandbox Testing / IPN Secret)",
)
async def simulate_ipn(
    payload: SimulateIpnRequest,
    db: Session = Depends(get_db),
    x_ipn_secret: Optional[str] = Header(
        None,
        alias="X-IPN-Secret",
        description="Khóa bí mật IPN Webhook (nếu có cấu hình)",
    ),
):
    return await PaymentService.simulate_ipn(db, payload)

# 5. Lấy danh sách toàn bộ giao dịch thanh toán
@router.get(
    "",
    response_model=PaymentPaginatedResponse,
    summary="Danh sách giao dịch thanh toán (kèm phân trang & bộ lọc - Yêu cầu ADMIN)",
)
def get_payments(
    status: Optional[str] = Query(None, description="PENDING, SUCCESS, FAILED, REFUNDED"),
    method: Optional[str] = Query(None, description="VNPAY, MOMO, CREDIT_CARD, CASH"),
    keyword: Optional[str] = Query(None, description="Tìm theo mã booking hoặc mã giao dịch"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    items, total, total_pages = PaymentService.get_payments(
        db=db,
        status_filter=status,
        method_filter=method,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

# 6. Thống kê tổng doanh thu & giao dịch
@router.get(
    "/stats",
    response_model=PaymentStatsResponse,
    summary="Thống kê tổng doanh thu và số lượng giao dịch (Yêu cầu ADMIN)",
)
def get_payment_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return PaymentService.get_stats(db)

# 5. Giao diện Sandbox Checkout HTML
@router.get(
    "/sandbox-checkout",
    response_class=HTMLResponse,
    summary="Trang thanh toán giả lập Sandbox",
)
def sandbox_checkout(
    txn: str = Query(..., description="Mã giao dịch gateway"),
    amount: float = Query(0, description="Số tiền"),
    booking: str = Query("", description="Mã booking"),
):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Cổng Thanh Toán Giả Lập Sandbox</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen p-4">
        <div class="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-6 border border-slate-200">
            <div class="text-center">
                <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-2 text-xl font-bold">💳</div>
                <h2 class="text-xl font-bold text-slate-800">Cổng Thanh Toán Sandbox</h2>
                <p class="text-xs text-slate-500">Mô phỏng thanh toán trực tuyến (VNPAY / MoMo)</p>
            </div>
            
            <div class="bg-slate-50 rounded-xl p-4 space-y-2 text-sm border border-slate-200">
                <div class="flex justify-between">
                    <span class="text-slate-500">Mã đơn đặt phòng:</span>
                    <span class="font-bold text-slate-800">{booking}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">Mã giao dịch:</span>
                    <span class="font-mono text-xs text-blue-600">{txn}</span>
                </div>
                <div class="flex justify-between border-t pt-2">
                    <span class="text-slate-600 font-semibold">Số tiền thanh toán:</span>
                    <span class="text-lg font-bold text-emerald-600">{amount:,.0f} VND</span>
                </div>
            </div>

            <!-- Khu vực thanh toán trực tiếp hoặc xác thực OTP -->
            <div class="border-t pt-4 space-y-3">
                <div class="text-xs font-bold text-slate-500 uppercase tracking-wider text-center">Phương thức 1: Xác thực OTP bảo mật</div>
                <div class="space-y-2">
                    <div class="flex gap-2">
                        <input id="emailInput" type="email" placeholder="Nhập email nhận OTP..." value="customer@hotel.com" class="flex-1 px-3 py-2 border rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <button onclick="requestOtp()" class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-xl transition whitespace-nowrap">
                            Gửi OTP
                        </button>
                    </div>
                    <div id="otpInputGroup" class="hidden flex gap-2">
                        <input id="otpCodeInput" type="text" maxlength="6" placeholder="Mã 6 số..." class="w-28 text-center px-3 py-2 border rounded-xl text-xs font-mono font-bold tracking-widest focus:outline-none focus:ring-2 focus:ring-emerald-500">
                        <button onclick="submitVerifyOtp()" class="flex-1 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs rounded-xl transition">
                            Xác thực OTP
                        </button>
                    </div>
                </div>
            </div>

            <div class="border-t pt-4 space-y-3">
                <div class="text-xs font-bold text-slate-500 uppercase tracking-wider text-center">Phương thức 2: Mô phỏng IPN trực tiếp</div>
                <div class="flex gap-2">
                    <button onclick="simulate('SUCCESS')" class="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs shadow-sm transition">
                        ✓ Thành công
                    </button>
                    <button onclick="simulate('FAILED')" class="flex-1 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-xl text-xs border border-rose-200 transition">
                        ✕ Hủy đơn
                    </button>
                </div>
            </div>

            <div id="result" class="text-center text-xs font-semibold hidden p-3 rounded-lg"></div>
        </div>

        <script>
            async function requestOtp() {{
                const resEl = document.getElementById('result');
                const email = document.getElementById('emailInput').value.trim();
                if (!email) {{
                    alert('Vui lòng nhập email');
                    return;
                }}
                resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-blue-50 text-blue-700';
                resEl.innerText = 'Đang sinh mã OTP và gửi qua Email / RabbitMQ...';

                try {{
                    const resp = await fetch('/api/v1/payments/generate-otp', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            ma_giao_dich_gateway: '{txn}',
                            email: email
                        }})
                    }});
                    const data = await resp.json();
                    if (resp.ok) {{
                        document.getElementById('otpInputGroup').className = 'flex gap-2';
                        resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-blue-50 text-blue-800 border border-blue-200';
                        resEl.innerText = data.message + ' (Hiệu lực 3 phút).';
                    }} else {{
                        resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-rose-50 text-rose-800 border border-rose-200';
                        resEl.innerText = 'Lỗi: ' + (data.detail || 'Không thể tạo OTP');
                    }}
                }} catch (e) {{
                    resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-rose-50 text-rose-800';
                    resEl.innerText = 'Lỗi kết nối: ' + e;
                }}
            }}

            async function submitVerifyOtp() {{
                const resEl = document.getElementById('result');
                const otp = document.getElementById('otpCodeInput').value.trim();
                if (!otp || otp.length !== 6) {{
                    alert('Vui lòng nhập đủ 6 chữ số OTP');
                    return;
                }}
                resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-blue-50 text-blue-700';
                resEl.innerText = 'Đang xác thực OTP...';

                try {{
                    const resp = await fetch('/api/v1/payments/verify-otp', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            ma_giao_dich_gateway: '{txn}',
                            otp_code: otp
                        }})
                    }});
                    const data = await resp.json();
                    if (resp.ok) {{
                        resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-emerald-50 text-emerald-800 border border-emerald-200';
                        resEl.innerText = 'Xác thực OTP thành công! Đơn đặt phòng ' + data.ma_booking + ' đã chuyển sang CONFIRMED.';
                    }} else {{
                        resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-rose-50 text-rose-800 border border-rose-200';
                        resEl.innerText = 'Lỗi: ' + (data.detail || 'Xác thực OTP thất bại');
                    }}
                }} catch (e) {{
                    resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-rose-50 text-rose-800';
                    resEl.innerText = 'Lỗi kết nối: ' + e;
                }}
            }}

            async function simulate(status) {{
                const resEl = document.getElementById('result');
                resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-blue-50 text-blue-700';
                resEl.innerText = 'Đang xử lý callback IPN...';

                try {{
                    const resp = await fetch('/api/v1/payments/simulate-ipn', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            ma_giao_dich_gateway: '{txn}',
                            trang_thai: status,
                            note: status === 'SUCCESS' ? 'Khách đã thanh toán thành công tại Sandbox' : 'Khách hủy thanh toán tại Sandbox'
                        }})
                    }});
                    const data = await resp.json();
                    if (status === 'SUCCESS') {{
                        resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-emerald-50 text-emerald-800 border border-emerald-200';
                        resEl.innerText = 'Thanh toán thành công! Đơn đặt phòng ' + data.ma_booking + ' đã tự động chuyển sang CONFIRMED.';
                    }} else {{
                        resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-rose-50 text-rose-800 border border-rose-200';
                        resEl.innerText = 'Giao dịch đã bị hủy.';
                    }}
                }} catch (e) {{
                    resEl.className = 'text-center text-xs font-semibold p-3 rounded-lg block bg-rose-50 text-rose-800';
                    resEl.innerText = 'Lỗi kết nối cổng thanh toán: ' + e;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
