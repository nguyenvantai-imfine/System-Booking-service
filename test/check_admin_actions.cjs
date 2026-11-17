// Existing dashboard mutations, against newly created isolated fixtures only.
const {chromium,request}=require('../logs/v4-browser/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const api=await request.newContext({baseURL:'http://127.0.0.1:18080/api/v1/'});
 const results=[];const suffix=Date.now();
 const call=async(path,method='get',data,token)=>{const r=await api[method](path,{data,headers:token?{Authorization:`Bearer ${token}`}:{}});if(!r.ok())throw Error(`${method} ${path} ${r.status()}`);return r.status()===204?null:r.json();};
 const admin=(await call('auth/login','post',{ten_dang_nhap_hoac_email:'admin',mat_khau:'123456'})).access_token;
 const customer=(await call('auth/login','post',{ten_dang_nhap_hoac_email:'customer1',mat_khau:'123456'})).access_token;
 const account=await call('admin/users','post',{ten_dang_nhap:'ui_'+suffix,email:`ui_${suffix}@example.com`,mat_khau:'Ui-test-password',vai_tro:'CUSTOMER'},admin);
 const hotel=await call('hotels','post',{ten_khach_san:'Admin UI '+suffix},admin);
 const kind=await call(`hotels/${hotel.id_khach_san}/room-types`,'post',{ten_loai_phong:'UI Deluxe',gia_co_ban_mot_dem:1000000},admin);
 const rooms=await call(`room-types/${kind.id_loai_phong}/rooms/batch`,'post',{room_numbers:['U1-'+suffix,'U2-'+suffix,'U3-'+suffix]},admin);
 const start=new Date(Date.now()+70*86400000).toISOString().slice(0,10),end=new Date(Date.now()+72*86400000).toISOString().slice(0,10);
 const book=async room=>call('bookings','post',{id_khach_san:hotel.id_khach_san,ngay_nhan_phong:start,ngay_tra_phong:end,rooms:[{id_phong:room.id_phong,id_loai_phong:kind.id_loai_phong,so_phong:room.so_phong,ten_loai_phong:'UI Deluxe',gia:1000000}],khach_o:{ho_ten:'Admin UI Guest',email:'ui@example.com',sdt:'0901112223'}},customer);
 const booking=await book(rooms[0]),payBooking=await book(rooms[1]);
 const payment=await call('payments/create-payment','post',{id_dat_phong:payBooking.id_dat_phong,ma_booking:payBooking.ma_booking,so_tien:payBooking.tong_tien,phuong_thuc:'VNPAY'},customer);
 const notice=await call('notifications/send','post',{loai_thong_bao:'SYSTEM',kenh_gui:'IN_APP',nguoi_nhan:`ui_${suffix}@example.com`,du_lieu:{message:'UI acceptance '+suffix}},admin);
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const page=await browser.newPage();page.on('dialog',dialog=>dialog.accept());
  await page.route('**/*',route=>['image','font','media'].includes(route.request().resourceType())?route.abort():route.continue());
  await page.goto('http://localhost:13000/login');await page.getByPlaceholder('admin@hotel.com').fill('admin');await page.locator('input[type=password]').fill('123456');await page.getByRole('button',{name:'Đăng Nhập',exact:true}).click();await page.waitForURL(url=>url.pathname==='/');
  async function action(path,placeholder,keyword,title,method,endpoint){
   console.log('Checking UI action: '+path+' / '+title);
   await page.goto('http://localhost:13000/'+path);
   if(placeholder)await page.getByPlaceholder(placeholder).fill(keyword);
   const row=page.getByRole('row').filter({hasText:keyword});await row.waitFor();
   const response=page.waitForResponse(r=>r.url().includes(endpoint)&&r.request().method()===method);
   await row.getByTitle(title,{exact:true}).click();
   if(path==='Users')await page.getByRole('button',{name:'Xác nhận',exact:true}).click();
   const r=await response;if(!r.ok())throw Error(`${title}: ${r.status()}`);
   console.log('PASS UI response: '+title);
  }
  await action('Users','Tìm theo ID, tên đăng nhập, email, số điện thoại...',account.ten_dang_nhap,'Khóa tài khoản','PATCH',`/admin/users/${account.id_tai_khoan}/status`);
  if((await call('admin/users/'+account.id_tai_khoan,'get',undefined,admin)).trang_thai!=='LOCKED')throw Error('Account not locked');results.push('User search and lock persisted');
  await action('Users','Tìm theo ID, tên đăng nhập, email, số điện thoại...',account.ten_dang_nhap,'Mở khóa tài khoản','PATCH',`/admin/users/${account.id_tai_khoan}/status`);
  if((await call('admin/users/'+account.id_tai_khoan,'get',undefined,admin)).trang_thai!=='ACTIVE')throw Error('Account not unlocked');results.push('Dashboard account unlock persisted');
  await action('Hotels','Tìm theo tên khách sạn, địa chỉ, người liên hệ...',hotel.ten_khach_san,'Tạm dừng / Ẩn khách sạn','PATCH',`/hotels/${hotel.id_khach_san}/status`);
  if((await call('hotels/'+hotel.id_khach_san)).trang_thai!=='TAM_DUNG')throw Error('Hotel not paused');results.push('Hotel search and pause persisted');
  await call(`hotels/${hotel.id_khach_san}/status`,'patch',{trang_thai:'HOAT_DONG'},admin);
  await action('Bookings','Tìm theo mã booking, tên khách, email, SĐT...',booking.ma_booking,'Xác nhận thanh toán','PATCH',`/bookings/${booking.id_dat_phong}/confirm`);
  if((await call('bookings/'+booking.id_dat_phong,'get',undefined,customer)).trang_thai!=='CONFIRMED')throw Error('Booking not confirmed');results.push('Dashboard manual booking confirmation persisted');
  await action('Bookings','Tìm theo mã booking, tên khách, email, SĐT...',booking.ma_booking,'Hủy đơn & nhả phòng','PATCH',`/bookings/${booking.id_dat_phong}/cancel`);
  if((await call('bookings/'+booking.id_dat_phong,'get',undefined,customer)).trang_thai!=='CANCELLED')throw Error('Booking not cancelled');results.push('Dashboard booking cancellation persisted');
  await action('Payments','Tìm theo mã booking, mã giao dịch gateway...',payment.ma_giao_dich_gateway,'Mô phỏng Thanh toán Thành Công (SUCCESS)','POST','/payments/simulate-ipn');
  if((await call('bookings/'+payBooking.id_dat_phong,'get',undefined,customer)).trang_thai!=='CONFIRMED')throw Error('IPN did not confirm booking');results.push('Dashboard payment IPN confirmed booking');
  await action('Notifications',null,new RegExp(`#${notice.id_thong_bao}(?!\\d)`),'Đánh dấu đã đọc','PATCH',`/notifications/${notice.id_thong_bao}/read`);
  if(!(await call('notifications/'+notice.id_thong_bao,'get',undefined,admin)).is_read)throw Error('Notice not read');results.push('Dashboard notification mark-read persisted');
  await action('Notifications',null,new RegExp(`#${notice.id_thong_bao}(?!\\d)`),'Xóa thông báo','DELETE',`/notifications/${notice.id_thong_bao}`);results.push('Dashboard notification delete');
  await page.goto('http://localhost:13000/Rooms');await page.getByPlaceholder('Tìm theo số phòng, hạng phòng, ghi chú...').fill(rooms[2].so_phong);
  const row=page.getByRole('row').filter({hasText:rooms[2].so_phong});await row.waitFor();
  const changed=page.waitForResponse(r=>r.url().includes(`/rooms/${rooms[2].id_phong}/status`)&&r.request().method()==='PATCH');await row.locator('select').selectOption('MAINTENANCE');if(!(await changed).ok())throw Error('Room status request failed');
  if((await call('rooms/'+rooms[2].id_phong)).trang_thai!=='MAINTENANCE')throw Error('Room not maintained');results.push('Dashboard room status persisted');
  console.log('PASS: '+results.join('; '));fs.writeFileSync('logs/v6-admin-browser-results.json',JSON.stringify({status:'PASS',checks:results},null,2));
 }finally{await browser.close();await api.dispose();}
})().catch(error=>{fs.writeFileSync('logs/v6-admin-browser-results.json',JSON.stringify({status:'FAIL',error:error.message},null,2));console.error(error.message);process.exitCode=1;});
