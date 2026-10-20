#!/bin/bash
set -e

echo "=========================================================="
echo ">>> [SQL Server Init] Khởi tạo CSDL Microservices..."
echo "=========================================================="

SA_PWD="${SA_PASSWORD:-Password123!}"
HOTEL_SQL_FILE="/usr/config/database_update.sql"
USER_SQL_FILE="/usr/config/user_database_init.sql"
ROOM_SQL_FILE="/usr/config/room_database_init.sql"
BOOKING_SQL_FILE="/usr/config/booking_database_init.sql"
PAYMENT_SQL_FILE="/usr/config/payment_database_init.sql"
NOTIFICATION_SQL_FILE="/usr/config/notification_database_init.sql"

# Vòng lặp chờ SQL Server sẵn sàng tiếp nhận kết nối (tối đa 90 giây)
echo ">>> [SQL Server Init] Đang chờ SQL Server sẵn sàng..."
for i in {1..45}; do
    if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -Q "SELECT 1" > /dev/null 2>&1; then
        echo ">>> [SQL Server Init] SQL Server đã sẵn sàng kết nối!"
        break
    fi
    echo ">>> [SQL Server Init] Đang chờ kết nối ($i/45)..."
    sleep 2
done

# Kiểm tra lại một lần nữa
if ! /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -Q "SELECT 1" > /dev/null 2>&1; then
    echo ">>> [SQL Server Init] LỖI: Hết thời gian chờ SQL Server!"
    exit 1
fi

# Chạy script khởi tạo CSDL Hotel Service
if [ -f "$HOTEL_SQL_FILE" ]; then
    echo ">>> [SQL Server Init] Đang thực thi script Hotel Service: $HOTEL_SQL_FILE..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -i "$HOTEL_SQL_FILE"
    echo ">>> [SQL Server Init] Khởi tạo CSDL Hotel Service hoàn tất!"
fi

# Chạy script khởi tạo CSDL User Service
if [ -f "$USER_SQL_FILE" ]; then
    echo ">>> [SQL Server Init] Đang thực thi script User Service: $USER_SQL_FILE..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -i "$USER_SQL_FILE"
    echo ">>> [SQL Server Init] Khởi tạo CSDL User Service hoàn tất!"
fi

# Chạy script khởi tạo CSDL Room Service
if [ -f "$ROOM_SQL_FILE" ]; then
    echo ">>> [SQL Server Init] Đang thực thi script Room Service: $ROOM_SQL_FILE..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -i "$ROOM_SQL_FILE"
    echo ">>> [SQL Server Init] Khởi tạo CSDL Room Service hoàn tất!"
fi

# Chạy script khởi tạo CSDL Booking Service
if [ -f "$BOOKING_SQL_FILE" ]; then
    echo ">>> [SQL Server Init] Đang thực thi script Booking Service: $BOOKING_SQL_FILE..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -i "$BOOKING_SQL_FILE"
    echo ">>> [SQL Server Init] Khởi tạo CSDL Booking Service hoàn tất!"
fi

# Chạy script khởi tạo CSDL Payment Service
if [ -f "$PAYMENT_SQL_FILE" ]; then
    echo ">>> [SQL Server Init] Đang thực thi script Payment Service: $PAYMENT_SQL_FILE..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -i "$PAYMENT_SQL_FILE"
    echo ">>> [SQL Server Init] Khởi tạo CSDL Payment Service hoàn tất!"
fi

# Chạy script khởi tạo CSDL Notification Service
if [ -f "$NOTIFICATION_SQL_FILE" ]; then
    echo ">>> [SQL Server Init] Đang thực thi script Notification Service: $NOTIFICATION_SQL_FILE..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PWD" -C -i "$NOTIFICATION_SQL_FILE"
    echo ">>> [SQL Server Init] Khởi tạo CSDL Notification Service hoàn tất!"
fi

echo "=========================================================="
echo ">>> [SQL Server Init] Hoàn tất quá trình khởi tạo CSDL!"
echo "=========================================================="
