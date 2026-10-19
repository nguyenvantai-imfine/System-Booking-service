"""init_and_upgrade_models

Revision ID: 1adff95a44fc
Revises: 
Create Date: 2026-10-20 02:58:02.939115

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1adff95a44fc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Bảng khách sạn
    op.create_table(
        'khach_san',
        sa.Column('id_khach_san', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_tai_khoan', sa.Integer(), nullable=False),
        sa.Column('ten_khach_san', sa.String(length=255), nullable=False),
        sa.Column('email_khach_san', sa.String(length=100), nullable=True),
        sa.Column('sdt_khach_san', sa.String(length=20), nullable=True),
        sa.Column('trang_thai', sa.Enum('HOAT_DONG', 'TAM_DUNG', 'CHO_DUYET', 'DA_XOA', name='trang_thai_khach_san_enum', native_enum=False), nullable=False, server_default='HOAT_DONG'),
        sa.Column('dia_chi', sa.String(length=255), nullable=True),
        sa.Column('phuong_xa', sa.String(length=100), nullable=True),
        sa.Column('quan_huyen', sa.String(length=100), nullable=True),
        sa.Column('thanh_pho', sa.String(length=100), nullable=True),
        sa.Column('tinh', sa.String(length=100), nullable=True),
        sa.Column('quoc_gia', sa.String(length=100), nullable=True, server_default='Việt Nam'),
        sa.Column('kinh_do', sa.Float(), nullable=True),
        sa.Column('vi_do', sa.Float(), nullable=True),
        sa.Column('ma_buu_chinh', sa.String(length=20), nullable=True),
        sa.Column('ten_nguoi_lien_he', sa.String(length=100), nullable=True),
        sa.Column('sdt_nguoi_lien_he', sa.String(length=20), nullable=True),
        sa.Column('ngay_tao', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ngay_cap_nhat', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id_khach_san')
    )
    op.create_index('ix_khach_san_id_khach_san', 'khach_san', ['id_khach_san'], unique=False)
    op.create_index('ix_khach_san_id_tai_khoan', 'khach_san', ['id_tai_khoan'], unique=False)
    op.create_index('ix_khach_san_ten_khach_san', 'khach_san', ['ten_khach_san'], unique=False)
    op.create_index('ix_khach_san_thanh_pho', 'khach_san', ['thanh_pho'], unique=False)
    op.create_index('ix_khach_san_tinh', 'khach_san', ['tinh'], unique=False)
    op.create_index('ix_khach_san_quan_huyen', 'khach_san', ['quan_huyen'], unique=False)
    op.create_index('ix_khach_san_trang_thai', 'khach_san', ['trang_thai'], unique=False)
    op.create_index('ix_khach_san_is_deleted', 'khach_san', ['is_deleted'], unique=False)

    # 2. Bảng hình ảnh khách sạn
    op.create_table(
        'hinh_anh_khach_san',
        sa.Column('id_hinh_anh', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_khach_san', sa.Integer(), nullable=False),
        sa.Column('duong_dan_anh', sa.String(length=500), nullable=False),
        sa.Column('loai_anh', sa.String(length=50), nullable=True, server_default='chung'),
        sa.Column('la_anh_chinh', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('thu_tu', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('ngay_tao', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['id_khach_san'], ['khach_san.id_khach_san'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_hinh_anh')
    )
    op.create_index('ix_hinh_anh_khach_san_id_hinh_anh', 'hinh_anh_khach_san', ['id_hinh_anh'], unique=False)

    # 3. Bảng thông tin khách sạn
    op.create_table(
        'thong_tin_khach_san',
        sa.Column('id_thong_tin', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_khach_san', sa.Integer(), nullable=False),
        sa.Column('loai_thong_tin', sa.String(length=255), nullable=False),
        sa.Column('noi_dung', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['id_khach_san'], ['khach_san.id_khach_san'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_thong_tin')
    )
    op.create_index('ix_thong_tin_khach_san_id_thong_tin', 'thong_tin_khach_san', ['id_thong_tin'], unique=False)

    # 4. Bảng quy tắc & chính sách khách sạn
    op.create_table(
        'quy_tac_khach_san',
        sa.Column('id_quy_tac', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_khach_san', sa.Integer(), nullable=False),
        sa.Column('loai_chinh_sach', sa.Enum('CHECK_IN_OUT', 'HUY_PHONG', 'TRE_EM', 'DAT_COC', 'QUY_DINH_CHUNG', name='loai_chinh_sach_enum', native_enum=False), nullable=False, server_default='QUY_DINH_CHUNG'),
        sa.Column('ten', sa.String(length=255), nullable=False),
        sa.Column('gia_tri_chon', sa.String(length=255), nullable=True),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['id_khach_san'], ['khach_san.id_khach_san'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_quy_tac')
    )
    op.create_index('ix_quy_tac_khach_san_id_quy_tac', 'quy_tac_khach_san', ['id_quy_tac'], unique=False)
    op.create_index('ix_quy_tac_khach_san_loai_chinh_sach', 'quy_tac_khach_san', ['loai_chinh_sach'], unique=False)

    # 5. Bảng danh mục tiện ích
    op.create_table(
        'danh_muc_tien_ich',
        sa.Column('id_danh_muc', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_khach_san', sa.Integer(), nullable=False),
        sa.Column('ten_danh_muc', sa.String(length=255), nullable=False),
        sa.Column('icon_danh_muc', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['id_khach_san'], ['khach_san.id_khach_san'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_danh_muc')
    )
    op.create_index('ix_danh_muc_tien_ich_id_danh_muc', 'danh_muc_tien_ich', ['id_danh_muc'], unique=False)

    # 6. Bảng chi tiết tiện nghi
    op.create_table(
        'chi_tiet_tien_nghi',
        sa.Column('id_tien_nghi', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_danh_muc', sa.Integer(), nullable=False),
        sa.Column('ten_tien_ich', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['id_danh_muc'], ['danh_muc_tien_ich.id_danh_muc'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_tien_nghi')
    )
    op.create_index('ix_chi_tiet_tien_nghi_id_tien_nghi', 'chi_tiet_tien_nghi', ['id_tien_nghi'], unique=False)


def downgrade() -> None:
    op.drop_table('chi_tiet_tien_nghi')
    op.drop_table('danh_muc_tien_ich')
    op.drop_table('quy_tac_khach_san')
    op.drop_table('thong_tin_khach_san')
    op.drop_table('hinh_anh_khach_san')
    op.drop_table('khach_san')
