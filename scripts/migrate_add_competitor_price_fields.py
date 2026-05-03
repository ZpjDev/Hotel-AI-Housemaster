"""
数据库迁移脚本：为 competitor_prices 表新增真实 OTA API 字段

用法：
    python scripts/migrate_add_competitor_price_fields.py

功能：
    1. 检查 competitor_prices 表是否存在
    2. 如果字段已存在，跳过不添加
    3. 如果字段不存在，使用 ALTER TABLE 添加
    4. 不删除旧数据
    5. 打印迁移结果
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
import sqlalchemy


NEW_COLUMNS = [
    {"name": "platform", "type": "VARCHAR", "nullable": True},
    {"name": "room_type", "type": "VARCHAR", "nullable": True},
    {"name": "remaining_rooms", "type": "INTEGER", "nullable": True},
    {"name": "availability_status", "type": "VARCHAR", "nullable": True},
    {"name": "cancellable", "type": "BOOLEAN", "nullable": True},
    {"name": "promotion_text", "type": "VARCHAR", "nullable": True},
    {"name": "source_type", "type": "VARCHAR", "nullable": True},
    {"name": "captured_at", "type": "DATETIME", "nullable": True},
]

TABLE_NAME = "competitor_prices"


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    """检查表中是否已存在某列"""
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def migrate():
    print(f"开始迁移 {TABLE_NAME} 表...")
    print(f"数据库: {engine.url}")

    inspector = sqlalchemy.inspect(engine)

    # 检查表是否存在
    if not inspector.has_table(TABLE_NAME):
        print(f"错误：表 {TABLE_NAME} 不存在，请先运行 seed_demo_data.py 初始化数据库。")
        return

    added = 0
    skipped = 0
    errors = 0

    for col_def in NEW_COLUMNS:
        col_name = col_def["name"]
        col_type = col_def["type"]
        nullable = col_def["nullable"]

        if column_exists(inspector, TABLE_NAME, col_name):
            print(f"  ✓ 字段 {col_name} 已存在，跳过")
            skipped += 1
            continue

        try:
            # 构建 ALTER TABLE 语句
            nullable_str = "NULL" if nullable else "NOT NULL"
            sql = f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col_name} {col_type} {nullable_str}"
            with engine.begin() as conn:
                conn.execute(sqlalchemy.text(sql))
            print(f"  ✓ 字段 {col_name} 添加成功 ({col_type} {nullable_str})")
            added += 1
        except Exception as e:
            print(f"  ✗ 字段 {col_name} 添加失败: {e}")
            errors += 1

    # 打印迁移结果
    print("\n" + "=" * 50)
    print(f"迁移完成：")
    print(f"  新增字段: {added}")
    print(f"  已存在跳过: {skipped}")
    print(f"  失败: {errors}")
    print(f"  总计: {len(NEW_COLUMNS)}")

    if errors == 0:
        print("✓ 所有字段迁移成功，旧数据未受影响。")
    else:
        print(f"⚠ 有 {errors} 个字段迁移失败，请检查日志。")

    # 验证最终表结构
    print("\n当前表结构:")
    inspector = sqlalchemy.inspect(engine)
    columns = inspector.get_columns(TABLE_NAME)
    for col in columns:
        print(f"  {col['name']:30s} {str(col['type']):15s} nullable={col.get('nullable', True)}")


if __name__ == "__main__":
    migrate()
