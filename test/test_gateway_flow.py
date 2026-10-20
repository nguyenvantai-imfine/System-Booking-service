import urllib.request
import json

def post_json(url, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer 1'})
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode('utf-8'))

# 1. Tao don dat phong qua Gateway
print('>>> Step 1: Tao booking qua Gateway 8080...')
bk_req = {
    'id_khach_san': 1,
    'id_tai_khoan': 4,
    'ngay_nhan_phong': '2026-12-01',
    'ngay_tra_phong': '2026-12-04',
    'rooms': [{'id_phong': 1, 'id_loai_phong': 1, 'so_phong': 'P.101', 'ten_loai_phong': 'Deluxe Ocean View', 'gia': 1200000}],
    'khach_o': {
        'ho_ten': 'Nguyen Gateway Tester',
        'email': 'tester.gateway@gmail.com',
        'sdt': '0988776655',
        'ghi_chu_dac_biet': 'Yeu cau view bien va check-in som'
    }
}
booking = post_json('http://127.0.0.1:8080/api/v1/bookings', bk_req)
ma_booking = booking['ma_booking']
id_dat_phong = booking['id_dat_phong']
trang_thai = booking['trang_thai']
print(f'>>> Tao booking thanh cong! Ma: {ma_booking}, ID: {id_dat_phong}, Trang thai: {trang_thai}')

# 2. Tao thanh toan qua Gateway
print('>>> Step 2: Tao giao dich thanh toan qua Gateway 8080...')
pm_req = {
    'id_dat_phong': id_dat_phong,
    'ma_booking': ma_booking,
    'so_tien': booking['tong_tien'],
    'phuong_thuc': 'VNPAY',
    'ghi_chu': 'Thanh toan don dat phong qua Gateway VNPAY'
}
payment = post_json('http://127.0.0.1:8080/api/v1/payments/create-payment', pm_req)
ma_txn = payment['ma_giao_dich_gateway']
print(f'>>> Tao payment thanh cong! Ma TXN: {ma_txn}')

# 3. Mo phong IPN SUCCESS qua Gateway
print('>>> Step 3: Mo phong Callback IPN SUCCESS qua Gateway...')
ipn_req = {
    'ma_giao_dich_gateway': ma_txn,
    'trang_thai': 'SUCCESS',
    'note': 'Giao dich VNPAY thanh cong 100%'
}
ipn_res = post_json('http://127.0.0.1:8080/api/v1/payments/simulate-ipn', ipn_req)
print(f'>>> IPN Callback xu ly xong! Trang thai GD: {ipn_res["trang_thai"]}')

# 4. Kiem tra Notification Service qua Gateway
print('>>> Step 4: Kiem tra danh sach thong bao da gui qua Gateway...')
url_noti = f'http://127.0.0.1:8080/api/v1/notifications?booking_code={ma_booking}'
req_noti = urllib.request.Request(url_noti, headers={'Authorization': 'Bearer 1'})
res_noti = json.loads(urllib.request.urlopen(req_noti).read().decode('utf-8'))
print(f'>>> So luong thong bao tim thay cho {ma_booking}: {len(res_noti["items"])}')
for item in res_noti['items']:
    print(f'    - ID: {item["id_thong_bao"]} | Loai: {item["loai_thong_bao"]} | Nguoi nhan: {item["nguoi_nhan"]} | Trang thai: {item["trang_thai"]}')

print('>>> TEST COMPLETED SUCCESSFULLY!')
