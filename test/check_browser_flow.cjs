// Uses only isolated acceptance endpoints; test email inbox remains in memory.
const { chromium, request } = require('../logs/v4-browser/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const api=await request.newContext({baseURL:'http://127.0.0.1:18080/api/v1/'});
 const checked=[];
 const json=async(path,method='get',data,token)=>{
  const r=await api[method](path,{data,headers:token?{Authorization:`Bearer ${token}`}:{}});
  if(!r.ok())throw new Error(`${method} ${path}: ${r.status()}`);return r.json();
 };
 const partner=(await json('auth/login','post',{ten_dang_nhap_hoac_email:'partner1',mat_khau:'123456'})).access_token;
 const suffix=Date.now();
 const hotel=await json('hotels','post',{ten_khach_san:`Browser ${suffix}`},partner);
 const kind=await json(`hotels/${hotel.id_khach_san}/room-types`,'post',{ten_loai_phong:'Browser Deluxe',gia_co_ban_mot_dem:1000000},partner);
 const room=await json(`room-types/${kind.id_loai_phong}/rooms`,'post',{so_phong:`UI-${suffix}`},partner);
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-background-networking','--renderer-process-limit=2']});
 try {
  let page=await browser.newPage();
  await page.route('**/*',route=>['image','font','media'].includes(route.request().resourceType()) ? route.abort() : route.continue());
  await page.goto('http://localhost:13000/login');
  await page.getByPlaceholder('admin@hotel.com').fill('admin');
  await page.locator('input[type=password]').fill('123456');
  await page.getByRole('button',{name:'Đăng Nhập',exact:true}).click();
  await page.waitForURL(url=>!url.pathname.includes('login'));
  for(const path of ['/Hotels','/Rooms','/Bookings','/Payments','/Users','/Notifications']){
   const response=await page.goto('http://localhost:13000'+path);
   if(!response.ok())throw new Error('Admin page '+path);checked.push('Admin '+path);
  }
  await page.context().close();
  page=await browser.newPage();
  await page.route('**/*',route=>['image','font','media'].includes(route.request().resourceType()) ? route.abort() : route.continue());
  await page.goto('http://localhost:13001');
  await page.getByRole('button',{name:/Đăng nhập/i}).first().click();
  await page.getByPlaceholder('customer@hotel.com hoặc customer').fill('customer1');
  await page.locator('input[type=password]').fill('123456');
  await page.getByRole('button',{name:'Đăng nhập ngay',exact:true}).click();
  await page.waitForFunction(()=>!!localStorage.getItem('customer_token'));
  const start=new Date(Date.now()+15*86400000).toISOString().slice(0,10),end=new Date(Date.now()+17*86400000).toISOString().slice(0,10);
  const search=new URLSearchParams({keyword:hotel.ten_khach_san,check_in:start,check_out:end});
  await page.goto('http://localhost:13001/search?'+search);
  const availability=page.waitForResponse(r=>r.url().includes('/rooms/available')&&r.request().method()==='GET');
  await page.getByRole('link',{name:hotel.ten_khach_san,exact:true}).click();
  if(!(await availability).ok())throw new Error('Room availability failed');
  await page.getByRole('button',{name:'Chọn phòng & Đặt ngay',exact:true}).click();
  await page.waitForURL('**/booking/checkout?**');
  if(new URL(page.url()).searchParams.get('room_id')!==String(room.id_phong))throw new Error('Wrong selected room');
  checked.push('Browser hotel search -> real room availability -> selected room');
  await page.getByPlaceholder('Ví dụ: NGUYEN VAN A (như trên CCCD)').fill('Browser Customer');
  await page.getByPlaceholder('nguyenvana@gmail.com').fill('browser@example.com');
  await page.getByPlaceholder('0901234567').fill('0901234567');
  const otpResponse=page.waitForResponse(r=>r.url().includes('/generate-otp')&&r.request().method()==='POST');
  await page.getByRole('button',{name:/Xác nhận và Thanh toán/}).click();
  const generated=await otpResponse; if(!generated.ok())throw new Error('Generate OTP HTTP '+generated.status());
  const txn=(await generated.json()).ma_giao_dich_gateway;
  let code;
  for(let i=0;i<50&&!code;i++){
   const response=await fetch(process.env.MOCK_INBOX_URL+'/?txn='+encodeURIComponent(txn),{headers:{'X-Test-Inbox-Key':process.env.MOCK_INBOX_KEY}});
   if(response.ok)code=(await response.json()).code;else await new Promise(r=>setTimeout(r,200));
  }
  if(!code)throw new Error('Mock inbox timeout');
  const inputs=page.locator('input[maxlength="1"]');
  const verifyResponse=page.waitForResponse(r=>r.url().includes('/verify-otp')&&r.request().method()==='POST');
  for(let i=0;i<6;i++)await inputs.nth(i).fill(code[i]);
  const verified=await verifyResponse;
  if(!verified.ok())throw new Error('OTP verification HTTP '+verified.status());
  const payment=await verified.json();
  if(payment.trang_thai!=='SUCCESS')throw new Error('Payment not successful');
  await page.waitForURL('**/booking/success/**');
  await page.getByText('Đặt phòng thành công & Đã xác nhận',{exact:true}).waitFor();
  checked.push('Browser checkout -> real OTP -> confirmed E-ticket');
  const token=await page.evaluate(()=>localStorage.getItem('customer_token'));
  const booking=await json('bookings/'+payment.id_dat_phong,'get',undefined,token);
  if(booking.trang_thai!=='CONFIRMED')throw new Error('Booking was not confirmed');
  await page.goto('http://localhost:13001/my-bookings');
  await page.getByText(payment.ma_booking,{exact:false}).first().waitFor();
  checked.push('Browser booking history contains the confirmed booking');
  fs.writeFileSync('logs/v4-browser-results.json',JSON.stringify({status:'PASS',checks:checked},null,2));
  console.log('PASS: Browser login, admin pages, checkout, OTP, E-ticket and history');
 } finally {await browser.close();await api.dispose();}
})().catch(error=>{
 fs.writeFileSync('logs/v4-browser-results.json',JSON.stringify({status:error.message.includes('ERR_INSUFFICIENT_RESOURCES')?'BLOCKED':'FAIL',error:error.message},null,2));
 console.error(error.message);process.exitCode=1;
});
