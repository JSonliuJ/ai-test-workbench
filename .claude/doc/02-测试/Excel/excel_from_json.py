#!/usr/bin/env python3
"""excel_from_json.py — 将 excel_data.json 转换为带格式的 Excel 文件"""
import json
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    excel_dir = os.path.join(base_dir, "Excel")
    json_path = os.path.join(excel_dir, "excel_data.json")
    output_path = os.path.join(excel_dir, "HC_API_测试用例.xlsx")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    columns = data["columns"]
    rows = data["rows"]

    wb = Workbook()
    wb.remove(wb.active)

    groups = {}
    for row in rows:
        key = row["接口Key"]
        if key not in groups:
            groups[key] = []
        groups[key].append(row)

    title_font = Font(name="Arial", bold=True, size=14)
    header_font_white = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    cell_font = Font(name="Arial", size=10)
    header_fill = PatternFill("solid", start_color="4472C4")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    wrap_align = Alignment(wrap_text=True, vertical="center", horizontal="left")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    col_widths = [16, 36, 36, 30, 10, 30, 10, 24, 30, 30, 50]

    priority_fills = {
        "High": PatternFill("solid", start_color="FFC7CE"),
        "Medium": PatternFill("solid", start_color="FFEB9C"),
        "Low": PatternFill("solid", start_color="C6EFCE"),
    }

    sheet_idx = 0
    for interface_key, interface_rows in groups.items():
        sheet_idx += 1
        ws = wb.create_sheet(title=interface_key[:31])

        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columns))
        c = ws.cell(row=1, column=1)
        c.value = f"接口 Key: {interface_key}  共 {len(interface_rows)} 条测试用例"
        c.font = title_font
        c.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[1].height = 28

        for ci, col in enumerate(columns, 1):
            cell = ws.cell(row=2, column=ci, value=col)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = thin_border

        for ri, row_data in enumerate(interface_rows, 3):
            for ci in range(1, len(columns) + 1):
                val = row_data.get(columns[ci - 1], "")
                cell = ws.cell(row=ri, column=ci, value=val)
                cell.font = cell_font
                cell.border = thin_border

                if columns[ci - 1] == "优先级":
                    cell.alignment = center_align
                    fill = priority_fills.get(val)
                    if fill:
                        cell.fill = fill
                elif columns[ci - 1] == "用例编号":
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = wrap_align

        from openpyxl.utils import get_column_letter
        for ci in range(1, len(columns) + 1):
            ws.column_dimensions[get_column_letter(ci)].width = col_widths[ci - 1]

    wb.save(output_path)
    print(f"已生成: {output_path}")
    print(f"Sheet 数量: {sheet_idx}, 总用例数: {len(rows)}")


if __name__ == "__main__":
    main()
