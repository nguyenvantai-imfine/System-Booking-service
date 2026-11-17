"""V6 existing-operation acceptance. Writes only new isolated acceptance fixtures."""
import json
from datetime import date,timedelta
from pathlib import Path
import subprocess
import uuid
import httpx
from run_isolated_acceptance import CONFIG,ROOT,connect

checks=[]
def verify(name,condition=True):
    if not condition:raise AssertionError(name)
    checks.append(name);print('PASS: '+name,flush=True)

def run():
    assert CONFIG['MSSQL_PORT']=='11433'
    host=subprocess.check_output(['docker','inspect','--format','{{.Config.Hostname}}','luxestay-acceptance-sqlserver-1'],text=True).strip()
    with connect('master') as db:assert db.execute('SELECT @@SERVERNAME').fetchone()[0].lower()==host.lower()
    client=httpx.Client(base_url='http://127.0.0.1:18080/api/v1',timeout=15,follow_redirects=True)
    def call(method,path,token=None,status=200,**kwargs):
        response=client.request(method,path,headers={'Authorization':'Bearer '+token} if token else {},**kwargs)
        assert response.status_code==status,f'{method} {path}: expected {status}, got {response.status_code}'
        return response.json() if response.content else None
    def login(name,password='123456',status=200):return call('POST','/auth/login',status=status,json={'ten_dang_nhap_hoac_email':name,'mat_khau':password})
    admin=login('admin')['access_token'];partner=login('partner1')['access_token'];suffix=uuid.uuid4().hex[:9]
    users=[]
    for index in range(2):
        payload={'ten_dang_nhap':f'v6_{suffix}_{index}','email':f'v6_{suffix}_{index}@example.com','mat_khau':'Closure-test-password','vai_tro':'CUSTOMER'}
        users.append(call('POST','/auth/register',status=201,json=payload))
    customer=users[0]['access_token'];other=users[1]['access_token'];uid=users[0]['user']['id_tai_khoan']
    call('POST','/auth/register',status=400,json=payload)
    call('POST','/auth/register',status=422,json={'email':'invalid'})
    refreshed=call('POST','/auth/refresh',json={'refresh_token':users[0]['refresh_token']})
    assert call('GET','/users/me',refreshed['access_token'])['id_tai_khoan']==uid
    call('POST','/auth/refresh',status=401,json={'refresh_token':customer})
    profile=call('PUT','/users/me',customer,json={'ho':'Closure','ten':'Customer','sdt':'0901112223'})
    assert profile['profile']['ho']=='Closure'
    call('GET',f'/users/{uid}',other,status=403)
    verify('User registration validation, refresh, profile persistence and ownership')
    managed=call('POST','/admin/users',admin,status=201,json={'ten_dang_nhap':'managed_'+suffix,'email':'managed_'+suffix+'@example.com','mat_khau':'Closure-test-password','vai_tro':'CUSTOMER'})
    mid=managed['id_tai_khoan']
    listed=call('GET','/admin/users',admin,params={'keyword':'managed_'+suffix,'page_size':1})
    assert listed['total']==1 and listed['items'][0]['id_tai_khoan']==mid
    call('GET','/admin/users',customer,status=403)
    before_lock=login('managed_'+suffix,'Closure-test-password')
    call('PATCH',f'/admin/users/{mid}/status',admin,json={'trang_thai':'LOCKED'})
    login('managed_'+suffix,'Closure-test-password',403)
    call('POST','/auth/refresh',status=401,json={'refresh_token':before_lock['refresh_token']})
    call('PATCH',f'/admin/users/{mid}/status',admin,json={'trang_thai':'ACTIVE'})
    login('managed_'+suffix,'Closure-test-password')
    call('DELETE',f'/admin/users/{mid}',admin)
    call('GET',f'/admin/users/{mid}',admin,status=404)
    verify('Admin account create/filter/pagination/lock/unlock/delete and authorization')
    hotel=call('POST','/hotels',partner,status=201,json={'ten_khach_san':'Closure '+suffix,'thanh_pho':'Da Nang'})
    hid=hotel['id_khach_san']
    foreign_partner=call('POST','/auth/register',status=201,json={'ten_dang_nhap':'partner_'+suffix,'email':'partner_'+suffix+'@example.com','mat_khau':'Closure-test-password','vai_tro':'PARTNER'})['access_token']
    call('PUT',f'/hotels/{hid}',foreign_partner,status=403,json={'ten_khach_san':'Foreign owner'})
    call('PUT',f'/hotels/{hid}',customer,status=403,json={'ten_khach_san':'Unauthorized'})
    call('PUT',f'/hotels/{hid}',admin,json={'ten_khach_san':'Updated '+suffix})
    assert call('GET','/hotels',params={'keyword':suffix})['total']==1
    images=call('POST',f'/hotels/{hid}/images/',partner,status=201,json=[{'duong_dan_anh':'https://example.com/one.png','la_anh_chinh':True},{'duong_dan_anh':'https://example.com/two.png'}])
    call('PUT',f'/hotels/{hid}/images/{images[1]["id_hinh_anh"]}/primary',partner)
    detail=call('GET',f'/hotels/{hid}')
    assert sum(i['la_anh_chinh'] for i in detail['hinh_anh'])==1
    second_hotel=call('POST','/hotels',partner,status=201,json={'ten_khach_san':'Nested isolation '+suffix})
    call('PUT',f'/hotels/{second_hotel["id_khach_san"]}/images/{images[1]["id_hinh_anh"]}/primary',partner,status=404)
    category=call('POST',f'/hotels/{hid}/amenities/categories',partner,status=201,json={'ten_danh_muc':'Closure amenities'})
    item=call('POST',f'/hotels/{hid}/amenities/categories/{category["id_danh_muc"]}/items',partner,status=201,json={'ten_tien_ich':'WiFi'})
    policy=call('POST',f'/hotels/{hid}/policies/',partner,status=201,json={'loai_chinh_sach':'QUY_DINH_CHUNG','ten':'Closure policy','mo_ta':'Original'})
    call('PUT',f'/hotels/{hid}/policies/{policy["id_quy_tac"]}',partner,json={'mo_ta':'Updated'})
    detail=call('GET',f'/hotels/{hid}')
    assert detail['quy_tac'][0]['mo_ta']=='Updated'
    call('DELETE',f'/hotels/{hid}/images/{images[0]["id_hinh_anh"]}',partner)
    call('DELETE',f'/hotels/{hid}/amenities/items/{item["id_tien_nghi"]}',partner)
    call('DELETE',f'/hotels/{hid}/policies/{policy["id_quy_tac"]}',partner)
    call('PATCH',f'/hotels/{hid}/status',admin,json={'trang_thai':'TAM_DUNG'})
    call('DELETE',f'/hotels/{hid}',admin)
    call('GET',f'/hotels/{hid}',status=404)
    restored=call('POST',f'/hotels/{hid}/restore',admin)
    assert restored['trang_thai']=='TAM_DUNG'
    call('PATCH',f'/hotels/{hid}/status',admin,json={'trang_thai':'HOAT_DONG'})
    verify('Hotel admin/owner CRUD, primary images, amenities, policies, soft delete/restore')
    kind=call('POST',f'/hotels/{hid}/room-types',admin,status=201,json={'ten_loai_phong':'Closure Deluxe','gia_co_ban_mot_dem':200000})
    tid=kind['id_loai_phong']
    call('PUT',f'/room-types/{tid}',admin,json={'mo_ta':'Updated type'})
    rooms=call('POST',f'/room-types/{tid}/rooms/batch',admin,status=201,json={'room_numbers':['C1','C2']})
    call('POST',f'/room-types/{tid}/rooms',admin,status=409,json={'so_phong':'C1'})
    call('DELETE',f'/room-types/{tid}',admin,status=409)
    assert call('GET',f'/hotels/{hid}/rooms',params={'status':'AVAILABLE','page_size':1})['total']==2
    verify('Room type update/delete protection, duplicate constraint and filtered pagination')
    start=(date.today()+timedelta(days=60)).isoformat();end=(date.today()+timedelta(days=62)).isoformat()
    def create_booking(room):return call('POST','/bookings',customer,status=201,json={'id_khach_san':hid,'ngay_nhan_phong':start,'ngay_tra_phong':end,'rooms':[{'id_phong':room['id_phong'],'id_loai_phong':tid,'so_phong':room['so_phong'],'ten_loai_phong':'Closure Deluxe','gia':200000}],'khach_o':{'ho_ten':'Closure Customer','email':'closure@example.com','sdt':'0901112223'}})
    booking=create_booking(rooms[0]);bid=booking['id_dat_phong']
    call('PATCH',f'/bookings/{bid}/confirm',customer,status=403)
    call('PATCH',f'/bookings/{bid}/confirm',partner,status=403)
    call('PATCH',f'/bookings/{bid}/confirm',admin)
    assert call('GET',f'/bookings/{bid}',customer)['trang_thai']=='CONFIRMED'
    call('PATCH',f'/bookings/{bid}/cancel',admin)
    assert call('GET',f'/bookings/{bid}',customer)['trang_thai']=='CANCELLED'
    verify('Existing Dashboard admin confirmation and cancellation persist booking states')
    booking=create_booking(rooms[1]);bid=booking['id_dat_phong']
    payment=call('POST','/payments/create-payment',customer,status=201,json={'id_dat_phong':bid,'ma_booking':booking['ma_booking'],'so_tien':booking['tong_tien'],'phuong_thuc':'VNPAY'})
    txn=payment['ma_giao_dich_gateway']
    call('POST','/payments/simulate-ipn',customer,status=403,json={'ma_giao_dich_gateway':txn,'trang_thai':'SUCCESS'})
    paid=call('POST','/payments/simulate-ipn',admin,json={'ma_giao_dich_gateway':txn,'trang_thai':'SUCCESS'})
    assert paid['trang_thai']=='SUCCESS' and call('GET',f'/bookings/{bid}',customer)['trang_thai']=='CONFIRMED'
    assert call('GET','/payments',admin,params={'keyword':booking['ma_booking']})['total']==1
    verify('Admin payment sandbox action reconciles booking; listing filter and customer rejection')
    notice=call('POST','/notifications/send',admin,status=201,json={'loai_thong_bao':'SYSTEM','kenh_gui':'IN_APP','nguoi_nhan':'closure@example.com','du_lieu':{'message':'<script>bad</script>'}})
    nid=notice['id_thong_bao'];assert '&lt;script&gt;' in notice['noi_dung']['noi_dung_html']
    assert call('PATCH',f'/notifications/{nid}/read',admin)['is_read'] is True
    call('GET',f'/notifications/{nid}',customer,status=404)
    call('DELETE',f'/notifications/{nid}',admin,status=204)
    call('GET',f'/notifications/{nid}',admin,status=404)
    verify('Admin notification create/escaping/read/delete and tenant isolation')
    call('DELETE',f'/rooms/{rooms[0]["id_phong"]}',admin,status=204)
    assert call('GET',f'/rooms/{rooms[0]["id_phong"]}')['trang_thai']=='INACTIVE'
    with connect('room_service') as db:
        assert db.execute('SELECT so_luong_phong FROM loai_phong WHERE id_loai_phong=?',tid).fetchone()[0]==2
    verify('Room removal preserves physical inventory history/counter')
    client.close()

if __name__=='__main__':
    error=None
    try:run()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';print('FAIL: '+error,flush=True)
    (ROOT/'logs/v6-functional-results.json').write_text(json.dumps({'checks':checks,'error':error},indent=2),encoding='utf-8')
    raise SystemExit(1 if error else 0)
