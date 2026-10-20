#!/bin/bash
set -e

# Chạy script khởi tạo CSDL dưới chế độ background
/bin/bash /usr/config/init-db.sh &

# Chạy tiến trình chính SQL Server
exec /opt/mssql/bin/sqlservr
