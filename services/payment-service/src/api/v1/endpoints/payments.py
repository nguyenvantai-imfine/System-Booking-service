from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.api.v1.dependencies import get_db
from src.schemas import (
    CreatePaymentRequest,
    SimulateIpnRequest,
    PaymentResponse,
    PaymentPaginatedResponse,
    PaymentStatsResponse,
)
from src.services import PaymentService

router = APIRouter(prefix="/payments", tags=["💳 Quản lý Thanh Toán"])

# 1. Khởi tạo giao dịch thanh toán cho đơn đặt phòng
@router.post(
    "/create-payment",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Khởi tạo giao dịch thanh toán",
)
def create_payment(
    payload: CreatePaymentRequest,
    db: Session = Depends(get_db),
):
    return PaymentService.create_payment(db, payload)

# 2. Mô phỏng IPN Callback từ cổng thanh toán (Sandbox)
@router.post(
    "/simulate-ipn",
    response_model=PaymentResponse,
    summary="Mô phỏng IPN Callback cổng thanh toán (Tự động kích hoạt CONFIRMED đơn booking)",
)
async def simulate_ipn(
    payload: SimulateIpnRequest,
    db: Session = Depends(get_db),
):
    return await PaymentService.simulate_ipn(db, payload)

# 3. Lấy danh sách toàn bộ giao dịch thanh toán
@router.get(
    "",
    response_model=PaymentPaginatedResponse,
    summary="Danh sách giao dịch thanh toán (kèm phân trang & bộ lọc)",
)
def get_payments(
    status: Optional[str] = Query(None, description="PENDING, SUCCESS, FAILED, REFUNDED"),
    method: Optional[str] = Query(None, description="VNPAY, MOMO, CREDIT_CARD, CASH"),
    keyword: Optional[str] = Query(None, description="Tìm theo mã booking hoặc mã giao dịch"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
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

# 4. Thống kê tổng doanh thu & giao dịch
@router.get(
    "/stats",
    response_model=PaymentStatsResponse,
    summary="Thống kê tổng doanh thu và số lượng giao dịch",
)
def get_payment_stats(db: Session = Depends(get_db)):
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

            <div class="space-y-3">
                <button onclick="simulate('SUCCESS')" class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow-sm transition">
                    ✓ Thanh Toán Thành Công
                </button>
                <button onclick="simulate('FAILED')" class="w-full py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-xl border border-rose-200 transition">
                    ✕ Hủy Giao Dịch
                </button>
            </div>

            <div id="result" class="text-center text-xs font-semibold hidden p-3 rounded-lg"></div>
        </div>

        <script>
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
