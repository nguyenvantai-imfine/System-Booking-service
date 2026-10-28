import html
import json
import urllib.parse
from typing import Dict, Any
from jinja2 import Environment

_HTML_ESCAPE_TEMPLATE = Environment(autoescape=True).from_string("{{ value }}")


def escape_html(value: Any) -> str:
    return _HTML_ESCAPE_TEMPLATE.render(value=value)

def render_booking_confirmed_email(data: Dict[str, Any]) -> tuple[str, str, str]:
    """
    Render template email cho sự kiện: Đặt phòng thành công / Xác nhận thanh toán.
    Trả về: (subject, html_content, text_content)
    """
    ma_booking = data.get("ma_booking", "BK-UNKNOWN")
    ten_khach = data.get("ten_khach", "Quý khách")
    ten_khach_san = data.get("ten_khach_san", "Khách sạn Quốc Tế")
    dia_chi = data.get("dia_chi", "Việt Nam")
    ngay_nhan = data.get("ngay_nhan_phong", "---")
    ngay_tra = data.get("ngay_tra_phong", "---")
    tong_tien = data.get("tong_tien", 0)
    formatted_price = f"{int(tong_tien):,} đ".replace(",", ".")
    phong_list = data.get("danh_sach_phong", [])
    if isinstance(phong_list, str):
        try:
            phong_list = json.loads(phong_list)
        except Exception:
            phong_list = []

    # XSS Protection: HTML escape tất cả biến động từ client
    safe_ma_booking = html.escape(str(ma_booking))
    safe_ten_khach = html.escape(str(ten_khach))
    safe_ten_khach_san = html.escape(str(ten_khach_san))
    safe_dia_chi = html.escape(str(dia_chi))
    safe_ngay_nhan = html.escape(str(ngay_nhan))
    safe_ngay_tra = html.escape(str(ngay_tra))
    safe_formatted_price = html.escape(str(formatted_price))

    phong_rows_html = ""
    for p in phong_list:
<<<<<<< HEAD
        so_phong = html.escape(str(p.get("so_phong", "Phòng tiêu chuẩn")))
        ten_loai = html.escape(str(p.get("ten_loai_phong", "Hạng phòng Deluxe")))
        gia = html.escape(f"{int(p.get('gia_tai_thoi_diem_dat', 0)):,} đ".replace(",", "."))
=======
        so_phong = escape_html(p.get("so_phong", "Phòng tiêu chuẩn"))
        ten_loai = escape_html(p.get("ten_loai_phong", "Hạng phòng Deluxe"))
        gia = f"{int(p.get('gia_tai_thoi_diem_dat', 0)):,} đ".replace(",", ".")
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
        phong_rows_html += f"""
        <tr>
            <td style="padding: 10px 12px; border-bottom: 1px solid #edf2f7; font-weight: 600; color: #1a202c;">{so_phong}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #edf2f7; color: #4a5568;">{ten_loai}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #edf2f7; text-align: right; font-weight: 600; color: #2d3748;">{gia}</td>
        </tr>
        """

    if not phong_rows_html:
        phong_rows_html = f"""
        <tr>
<<<<<<< HEAD
            <td colspan="3" style="padding: 12px; text-align: center; color: #718096;">Thông tin phòng theo mã đặt chỗ #{safe_ma_booking}</td>
=======
            <td colspan="3" style="padding: 12px; text-align: center; color: #718096;">Thông tin phòng theo mã đặt chỗ #{escape_html(ma_booking)}</td>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
        </tr>
        """

    # QuickChart QR API tạo mã QR check-in tiện lợi
    qr_encoded = urllib.parse.quote(f"CHECKIN-{ma_booking}")
    qr_url = f"https://quickchart.io/qr?text={qr_encoded}&size=150&ecLevel=M"
    safe_qr_url = html.escape(qr_url)

    subject = f"🎉 Xác nhận đơn đặt phòng #{ma_booking} thành công - {ten_khach_san}"
    safe_subject = html.escape(subject)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
<<<<<<< HEAD
    <title>{safe_subject}</title>
=======
    <title>{escape_html(subject)}</title>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
</head>
<body style="margin: 0; padding: 0; background-color: #f7fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #2d3748;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f7fafc; padding: 30px 15px;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
                    <!-- HEADER -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 35px 30px; text-align: center; color: #ffffff;">
                            <div style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 6px;">✨ HOTEL BOOKING</div>
                            <div style="font-size: 15px; opacity: 0.9; font-weight: 500;">Xác Nhận Đặt Phòng Trực Tuyến Thành Công</div>
                        </td>
                    </tr>

                    <!-- NỘI DUNG CHÍNH -->
                    <tr>
                        <td style="padding: 30px;">
                            <div style="font-size: 16px; color: #2d3748; margin-bottom: 20px;">
<<<<<<< HEAD
                                Xin chào <strong>{safe_ten_khach}</strong>,<br>
=======
                                Xin chào <strong>{escape_html(ten_khach)}</strong>,<br>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                                Cảm ơn bạn đã lựa chọn dịch vụ của chúng tôi! Đơn đặt phòng của bạn đã được xác nhận thành công.
                            </div>

                            <!-- BANNER MÃ BOOKING -->
                            <div style="background-color: #eff6ff; border: 1.5px dashed #3b82f6; border-radius: 12px; padding: 18px; text-align: center; margin-bottom: 25px;">
                                <div style="font-size: 12px; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">MÃ ĐẶT PHÒNG (BOOKING CODE)</div>
<<<<<<< HEAD
                                <div style="font-size: 28px; font-weight: 800; color: #1e40af; font-family: 'Courier New', Courier, monospace;">{safe_ma_booking}</div>
=======
                                <div style="font-size: 28px; font-weight: 800; color: #1e40af; font-family: 'Courier New', Courier, monospace;">{escape_html(ma_booking)}</div>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                                <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Trình mã này hoặc quét mã QR dưới đây khi làm thủ tục nhận phòng</div>
                            </div>

                            <!-- THÔNG TIN LƯU TRÚ -->
                            <div style="margin-bottom: 25px;">
                                <div style="font-size: 15px; font-weight: 700; color: #1e293b; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 12px;">🏨 Thông Tin Khách Sạn & Lưu Trú</div>
                                <table width="100%" border="0" cellspacing="0" cellpadding="6" style="font-size: 14px;">
                                    <tr>
                                        <td width="35%" style="color: #64748b; font-weight: 500;">Khách sạn:</td>
<<<<<<< HEAD
                                        <td style="color: #0f172a; font-weight: 700;">{safe_ten_khach_san}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; font-weight: 500;">Địa chỉ:</td>
                                        <td style="color: #334155;">{safe_dia_chi}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; font-weight: 500;">Ngày nhận phòng:</td>
                                        <td style="color: #047857; font-weight: 700;">{safe_ngay_nhan} (Sau 14:00)</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; font-weight: 500;">Ngày trả phòng:</td>
                                        <td style="color: #b91c1c; font-weight: 700;">{safe_ngay_tra} (Trước 12:00)</td>
=======
                                        <td style="color: #0f172a; font-weight: 700;">{escape_html(ten_khach_san)}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; font-weight: 500;">Địa chỉ:</td>
                                        <td style="color: #334155;">{escape_html(dia_chi)}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; font-weight: 500;">Ngày nhận phòng:</td>
                                        <td style="color: #047857; font-weight: 700;">{escape_html(ngay_nhan)} (Sau 14:00)</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; font-weight: 500;">Ngày trả phòng:</td>
                                        <td style="color: #b91c1c; font-weight: 700;">{escape_html(ngay_tra)} (Trước 12:00)</td>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                                    </tr>
                                </table>
                            </div>

                            <!-- DANH SÁCH PHÒNG -->
                            <div style="margin-bottom: 25px;">
                                <div style="font-size: 15px; font-weight: 700; color: #1e293b; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 12px;">🛏️ Chi Tiết Phòng Đã Đặt</div>
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="font-size: 13px; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background-color: #f8fafc; color: #64748b; font-weight: 700; text-transform: uppercase; font-size: 11px;">
                                            <th style="padding: 8px 12px; text-align: left;">Số phòng</th>
                                            <th style="padding: 8px 12px; text-align: left;">Hạng phòng</th>
                                            <th style="padding: 8px 12px; text-align: right;">Đơn giá</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {phong_rows_html}
                                    </tbody>
                                </table>
                            </div>

                            <!-- TỔNG TIỀN VÀ MÃ QR CHECK-IN -->
                            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border-radius: 12px; padding: 18px; margin-bottom: 25px;">
                                <tr>
                                    <td width="60%" valign="middle">
                                        <div style="font-size: 13px; color: #64748b; margin-bottom: 4px;">Tổng tiền đã thanh toán:</div>
                                        <div style="font-size: 24px; font-weight: 800; color: #059669;">{safe_formatted_price}</div>
                                        <div style="font-size: 11px; color: #10b981; font-weight: 600; margin-top: 2px;">✔ Đã xác nhận thanh toán an toàn</div>
                                    </td>
                                    <td width="40%" align="center" valign="middle">
<<<<<<< HEAD
                                        <img src="{safe_qr_url}" alt="Mã QR Check-in" width="110" height="110" style="display: block; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff; padding: 4px;" />
=======
                                        <img src="{escape_html(qr_url)}" alt="Mã QR Check-in" width="110" height="110" style="display: block; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff; padding: 4px;" />
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                                        <div style="font-size: 10px; color: #64748b; margin-top: 4px; font-weight: 600;">QUÉT MÃ CHECK-IN</div>
                                    </td>
                                </tr>
                            </table>

                            <!-- QUY ĐỊNH NHẬN PHÒNG -->
                            <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 10px; padding: 14px; font-size: 12px; color: #92400e; line-height: 1.6; margin-bottom: 20px;">
                                <strong>Lưu ý nhận phòng:</strong> Quý khách vui lòng xuất trình CCCD/Hộ chiếu trùng khớp với tên trên đơn đặt phòng và mã QR/Booking code này tại quầy lễ tân khi làm thủ tục check-in.
                            </div>
                        </td>
                    </tr>

                    <!-- FOOTER -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 25px; text-align: center; font-size: 12px; color: #94a3b8;">
                            <div style="font-weight: 600; color: #64748b; margin-bottom: 6px;">Hotline hỗ trợ 24/7: 1900 8888 | Email: hotro@hotelbooking.com</div>
                            <div>© 2026 Hotel Booking Service System. All rights reserved.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    text_content = f"""
XÁC NHẬN ĐẶT PHÒNG THÀNH CÔNG #{ma_booking}
Khách hàng: {ten_khach}
Khách sạn: {ten_khach_san} - Địa chỉ: {dia_chi}
Ngày nhận phòng: {ngay_nhan} (Sau 14:00)
Ngày trả phòng: {ngay_tra} (Trước 12:00)
Tổng tiền: {formatted_price}
Mã đặt chỗ: {ma_booking}
Vui lòng xuất trình mã này tại quầy lễ tân khi làm thủ tục nhận phòng.
Hotline hỗ trợ: 1900 8888
"""
    return subject, html_content, text_content


def render_booking_cancelled_email(data: Dict[str, Any]) -> tuple[str, str, str]:
    """
    Render template email cho sự kiện: Hủy đơn đặt phòng.
    """
    ma_booking = data.get("ma_booking", "BK-UNKNOWN")
    ten_khach = data.get("ten_khach", "Quý khách")
    ten_khach_san = data.get("ten_khach_san", "Khách sạn Quốc Tế")
    ly_do = data.get("ly_do", "Quá thời hạn giữ chỗ 15 phút hoặc yêu cầu từ quản trị viên")

    subject = f"⚠️ Thông báo hủy đơn đặt phòng #{ma_booking} - {ten_khach_san}"
    safe_subject = html.escape(subject)
    safe_ma_booking = html.escape(str(ma_booking))
    safe_ten_khach = html.escape(str(ten_khach))
    safe_ten_khach_san = html.escape(str(ten_khach_san))
    safe_ly_do = html.escape(str(ly_do))

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
<<<<<<< HEAD
    <title>{safe_subject}</title>
=======
    <title>{escape_html(subject)}</title>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
</head>
<body style="margin: 0; padding: 0; background-color: #f7fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #2d3748;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f7fafc; padding: 30px 15px;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0;">
                    <tr>
                        <td style="background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%); padding: 30px; text-align: center; color: #ffffff;">
                            <div style="font-size: 24px; font-weight: 800;">ĐƠN ĐẶT PHÒNG ĐÃ BỊ HỦY</div>
<<<<<<< HEAD
                            <div style="font-size: 14px; opacity: 0.9; margin-top: 4px;">Mã đặt phòng: {safe_ma_booking}</div>
=======
                            <div style="font-size: 14px; opacity: 0.9; margin-top: 4px;">Mã đặt phòng: {escape_html(ma_booking)}</div>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; font-size: 14px; line-height: 1.6;">
<<<<<<< HEAD
                            Xin chào <strong>{safe_ten_khach}</strong>,<br><br>
                            Chúng tôi xin thông báo đơn đặt phòng <strong>#{safe_ma_booking}</strong> tại <strong>{safe_ten_khach_san}</strong> đã được hủy và phòng đã được mở lại cho các khách hàng khác.<br><br>
                            <div style="background-color: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; padding: 12px; color: #991b1b;">
                                <strong>Lý do hủy:</strong> {safe_ly_do}
=======
                            Xin chào <strong>{escape_html(ten_khach)}</strong>,<br><br>
                            Chúng tôi xin thông báo đơn đặt phòng <strong>#{escape_html(ma_booking)}</strong> tại <strong>{escape_html(ten_khach_san)}</strong> đã được hủy và phòng đã được mở lại cho các khách hàng khác.<br><br>
                            <div style="background-color: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; padding: 12px; color: #991b1b;">
                                <strong>Lý do hủy:</strong> {escape_html(ly_do)}
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                            </div>
                            <br>
                            Nếu bạn có thắc mắc hoặc cần hỗ trợ thêm, vui lòng liên hệ tổng đài <strong>1900 8888</strong> để được trợ giúp.
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                            © 2026 Hotel Booking Service System. All rights reserved.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    text_content = f"""
THÔNG BÁO HỦY ĐƠN ĐẶT PHÒNG #{ma_booking}
Xin chào {ten_khach},
Đơn đặt phòng #{ma_booking} tại {ten_khach_san} đã được hủy.
Lý do: {ly_do}
Hotline hỗ trợ: 1900 8888
"""
    return subject, html_content, text_content


def render_otp_email(data: Dict[str, Any]) -> tuple[str, str, str]:
    """
    Render template email cho sự kiện: Gửi mã OTP xác thực thanh toán.
    Trả về: (subject, html_content, text_content)
    """
    otp_code = str(data.get("otp_code", "------"))
    expires_in = data.get("expires_in_seconds", 180)
    minutes = max(1, expires_in // 60)
    ma_txn = data.get("ma_giao_dich_gateway", "")
    ma_booking = data.get("ma_booking", "")
    ten_khach = data.get("ten_khach", "Quý khách")

    subject = f"🔐 Mã OTP xác thực giao dịch thanh toán: {otp_code}"
    safe_subject = html.escape(subject)
    safe_otp_code = html.escape(str(otp_code))
    safe_ma_txn = html.escape(str(ma_txn))
    safe_ma_booking = html.escape(str(ma_booking))
    safe_ten_khach = html.escape(str(ten_khach))

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
<<<<<<< HEAD
    <title>{safe_subject}</title>
=======
    <title>{escape_html(subject)}</title>
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 35px 15px;">
        <tr>
            <td align="center">
                <table width="100%" max-width="580" border="0" cellspacing="0" cellpadding="0" style="max-width: 580px; background-color: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
                    <!-- HEADER -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%); padding: 35px 30px; text-align: center; color: #ffffff;">
                            <div style="font-size: 24px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 6px;">✨ HOTEL BOOKING SERVICE</div>
                            <div style="font-size: 15px; opacity: 0.92; font-weight: 500;">Mã Xác Thực Giao Dịch Thanh Toán (OTP)</div>
                        </td>
                    </tr>

                    <!-- NỘI DUNG CHÍNH -->
                    <tr>
                        <td style="padding: 35px 30px;">
                            <div style="font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 12px;">
<<<<<<< HEAD
                                Xin chào {safe_ten_khach},
=======
                                Xin chào {escape_html(ten_khach)},
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                            </div>
                            <div style="font-size: 14px; line-height: 1.6; color: #475569; margin-bottom: 24px;">
                                Bạn vừa yêu cầu mã xác thực bảo mật 2 lớp (OTP) để hoàn tất thanh toán đơn đặt phòng trực tuyến. Vui lòng sử dụng mã xác thực dưới đây để tiếp tục:
                            </div>

                            <!-- KHỐI MÃ OTP CỠ LỚN -->
                            <div style="background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%); border: 2px dashed #3b82f6; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 24px;">
                                <div style="font-size: 12px; font-weight: 700; color: #1e40af; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                                    Mã xác thực một lần (OTP)
                                </div>
                                <div style="font-size: 40px; font-weight: 900; letter-spacing: 10px; color: #1d4ed8; font-family: 'SF Mono', Consolas, 'Courier New', monospace; padding: 6px 0;">
<<<<<<< HEAD
                                    {safe_otp_code}
=======
                                    {escape_html(otp_code)}
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                                </div>
                                <div style="display: inline-block; background-color: #fee2e2; border: 1px solid #fecaca; color: #b91c1c; font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 9999px; margin-top: 10px;">
                                    ⏱️ Mã có hiệu lực trong vòng {escape_html(minutes)} phút ({escape_html(expires_in)} giây)
                                </div>
                            </div>

                            <!-- THÔNG TIN ĐƠN HÀNG KÈM THEO -->
                            <div style="background-color: #f8fafc; border-radius: 12px; padding: 14px 18px; margin-bottom: 24px; font-size: 13px; color: #64748b; border: 1px solid #e2e8f0;">
                                <div style="margin-bottom: 4px;"><strong style="color: #334155;">Mục đích:</strong> Xác thực thanh toán đơn đặt phòng</div>
<<<<<<< HEAD
                                {f'<div style="margin-bottom: 4px;"><strong style="color: #334155;">Mã đặt phòng:</strong> {safe_ma_booking}</div>' if ma_booking else ''}
                                {f'<div><strong style="color: #334155;">Mã giao dịch:</strong> <code style="font-family: monospace; color: #2563eb;">{safe_ma_txn}</code></div>' if ma_txn else ''}
=======
                                {f'<div style="margin-bottom: 4px;"><strong style="color: #334155;">Mã đặt phòng:</strong> {escape_html(ma_booking)}</div>' if ma_booking else ''}
                                {f'<div><strong style="color: #334155;">Mã giao dịch:</strong> <code style="font-family: monospace; color: #2563eb;">{escape_html(ma_txn)}</code></div>' if ma_txn else ''}
>>>>>>> 2708e038e84913f727dc4c52b8e5cfe91426ba6b
                            </div>

                            <!-- HƯỚNG DẪN BẢO MẬT -->
                            <div style="background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 16px; font-size: 13px; line-height: 1.6; color: #92400e;">
                                <div style="font-weight: 700; margin-bottom: 6px;">
                                    🛡️ Hướng dẫn bảo mật quan trọng:
                                </div>
                                <ul style="margin: 0; padding-left: 20px;">
                                    <li>Tuyệt đối <strong>KHÔNG</strong> chia sẻ mã OTP này cho bất kỳ ai, bao gồm cả nhân viên hỗ trợ khách sạn hoặc nhân viên ngân hàng.</li>
                                    <li>Mã này chỉ có hiệu lực duy nhất một lần và sẽ tự động vô hiệu hóa sau <strong>3 phút</strong>.</li>
                                    <li>Nếu bạn <strong>không</strong> thực hiện yêu cầu này, vui lòng bỏ qua email và liên hệ ngay tổng đài hỗ trợ <strong>1900 8888</strong> để được hỗ trợ khóa giao dịch kịp thời.</li>
                                </ul>
                            </div>
                        </td>
                    </tr>

                    <!-- FOOTER -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 30px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                            <div style="margin-bottom: 6px;">Hotline hỗ trợ 24/7: <strong style="color: #64748b;">1900 8888</strong> | Email: <strong style="color: #64748b;">support@hotelbooking.com</strong></div>
                            <div>© 2026 Hotel Booking Service System. All rights reserved.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    text_content = f"""
XÁC THỰC GIAO DỊCH THANH TOÁN (OTP)
Xin chào {ten_khach},
Mã OTP xác thực thanh toán của bạn là: {otp_code}
Hiệu lực: {minutes} phút ({expires_in} giây).
Mã giao dịch: {ma_txn}
Mã đặt phòng: {ma_booking}

LƯU Ý BẢO MẬT:
- Tuyệt đối không chia sẻ mã này cho bất kỳ ai.
- Nếu không phải bạn yêu cầu, vui lòng liên hệ hotline 1900 8888 ngay lập tức.
© 2026 Hotel Booking Service System.
"""
    return subject, html_content, text_content
