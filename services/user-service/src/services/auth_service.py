from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from src.models import TaiKhoanModel, NguoiDungModel, VaiTroEnum, TrangThaiTaiKhoanEnum
from src.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserBrief
from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

class AuthService:

    @staticmethod
    def register(db: Session, req: RegisterRequest) -> TokenResponse:
        # Kiểm tra trùng tên đăng nhập hoặc email
        existing = db.query(TaiKhoanModel).filter(
            or_(
                TaiKhoanModel.ten_dang_nhap == req.ten_dang_nhap,
                TaiKhoanModel.email == req.email,
            )
        ).first()

        if existing:
            if existing.ten_dang_nhap == req.ten_dang_nhap:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tên đăng nhập đã tồn tại trong hệ thống.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã được đăng ký cho tài khoản khác.",
            )

        # Không cho phép tự đăng ký quyền ADMIN trực tiếp qua public API
        role = req.vai_tro
        if role == VaiTroEnum.ADMIN:
            role = VaiTroEnum.CUSTOMER

        # Tạo tài khoản
        tai_khoan = TaiKhoanModel(
            ten_dang_nhap=req.ten_dang_nhap,
            email=req.email,
            sdt=req.sdt,
            mat_khau_hash=hash_password(req.mat_khau),
            vai_tro=role,
            trang_thai=TrangThaiTaiKhoanEnum.ACTIVE,
        )
        db.add(tai_khoan)
        db.flush()

        # Tạo hồ sơ người dùng tương ứng (1:1)
        profile = NguoiDungModel(
            id_tai_khoan=tai_khoan.id_tai_khoan,
            ho=req.ho,
            ten=req.ten,
        )
        db.add(profile)
        db.commit()
        db.refresh(tai_khoan)

        # Cấp token
        access_token = create_access_token({
            "sub": str(tai_khoan.id_tai_khoan),
            "role": str(tai_khoan.vai_tro.value),
            "email": tai_khoan.email,
        })
        refresh_token = create_refresh_token({
            "sub": str(tai_khoan.id_tai_khoan),
        })

        user_brief = UserBrief(
            id_tai_khoan=tai_khoan.id_tai_khoan,
            ten_dang_nhap=tai_khoan.ten_dang_nhap,
            email=tai_khoan.email,
            vai_tro=tai_khoan.vai_tro,
            trang_thai=tai_khoan.trang_thai,
            ho_va_ten=profile.ho_va_ten,
            avatar=profile.avatar,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_brief,
        )

    @staticmethod
    def login(db: Session, req: LoginRequest) -> TokenResponse:
        # Tìm theo username hoặc email
        tai_khoan = db.query(TaiKhoanModel).filter(
            or_(
                TaiKhoanModel.ten_dang_nhap == req.ten_dang_nhap_hoac_email,
                TaiKhoanModel.email == req.ten_dang_nhap_hoac_email,
            )
        ).first()

        if not tai_khoan or not verify_password(req.mat_khau, tai_khoan.mat_khau_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản hoặc mật khẩu không chính xác.",
            )

        if tai_khoan.trang_thai == TrangThaiTaiKhoanEnum.LOCKED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Quản trị viên.",
            )

        if tai_khoan.trang_thai == TrangThaiTaiKhoanEnum.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản chưa được kích hoạt hoặc đã ngừng hoạt động.",
            )

        # Tự động nâng cấp hash: Khi người dùng đăng nhập thành công bằng mật khẩu plaintext cũ,
        # tự động băm lại mật khẩu và cập nhật mat_khau_hash vào CSDL.
        if tai_khoan.mat_khau_hash and not tai_khoan.mat_khau_hash.startswith("$2"):
            tai_khoan.mat_khau_hash = hash_password(req.mat_khau)
            db.commit()
            db.refresh(tai_khoan)

        profile = tai_khoan.nguoi_dung
        ho_va_ten = profile.ho_va_ten if profile else "Chưa đặt tên"
        avatar = profile.avatar if profile else None

        access_token = create_access_token({
            "sub": str(tai_khoan.id_tai_khoan),
            "role": str(tai_khoan.vai_tro.value),
            "email": tai_khoan.email,
        })
        refresh_token = create_refresh_token({
            "sub": str(tai_khoan.id_tai_khoan),
        })

        user_brief = UserBrief(
            id_tai_khoan=tai_khoan.id_tai_khoan,
            ten_dang_nhap=tai_khoan.ten_dang_nhap,
            email=tai_khoan.email,
            vai_tro=tai_khoan.vai_tro,
            trang_thai=tai_khoan.trang_thai,
            ho_va_ten=ho_va_ten,
            avatar=avatar,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_brief,
        )

    @staticmethod
    def refresh(db: Session, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token không phải là refresh token hợp lệ.",
                )
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token không hợp lệ hoặc đã hết hạn.",
            )

        tai_khoan = db.query(TaiKhoanModel).filter(TaiKhoanModel.id_tai_khoan == user_id).first()
        if not tai_khoan or tai_khoan.trang_thai in [TrangThaiTaiKhoanEnum.LOCKED, TrangThaiTaiKhoanEnum.INACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản không tồn tại, đã bị khóa hoặc chưa được kích hoạt.",
            )

        profile = tai_khoan.nguoi_dung
        ho_va_ten = profile.ho_va_ten if profile else "Chưa đặt tên"
        avatar = profile.avatar if profile else None

        new_access_token = create_access_token({
            "sub": str(tai_khoan.id_tai_khoan),
            "role": str(tai_khoan.vai_tro.value),
            "email": tai_khoan.email,
        })
        new_refresh_token = create_refresh_token({
            "sub": str(tai_khoan.id_tai_khoan),
        })

        user_brief = UserBrief(
            id_tai_khoan=tai_khoan.id_tai_khoan,
            ten_dang_nhap=tai_khoan.ten_dang_nhap,
            email=tai_khoan.email,
            vai_tro=tai_khoan.vai_tro,
            trang_thai=tai_khoan.trang_thai,
            ho_va_ten=ho_va_ten,
            avatar=avatar,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=user_brief,
        )
