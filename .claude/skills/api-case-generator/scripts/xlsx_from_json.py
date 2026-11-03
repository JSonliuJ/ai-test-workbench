#!/usr/bin/env python3
"""从 excel_data.json 生成格式化的 Excel 文件"""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def main():
    input_json = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\jieliu666\python3_code\sublime_text03\05project\HCsource\.claude\doc\02-测试\Excel\excel_data.json'
    output_xlsx = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\jieliu666\python3_code\sublime_text03\05project\HCsource\.claude\doc\02-测试\Excel\HC_API_测试用例.xlsx'

    with open(input_json, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    # Group test cases by interface key
    by_interface = {}
    for item in raw:
        if isinstance(item, dict):
            key = item.get('key', '未知接口')
        elif isinstance(item, list):
            # Flatten nested lists
            for sub in item:
                if isinstance(sub, dict):
                    key = sub.get('key', '未知接口')
                    clean = ''.join(c for c in key if c not in '/\\:*?"<>|()')
                    by_interface.setdefault(clean, []).append(sub)
            continue
        else:
            continue

        clean = ''.join(c for c in key if c not in '/\\:*?"<>|()')
        by_interface.setdefault(clean, []).append(item)

    wb = Workbook()

    # 定义样式
    header_font = Font(name='Arial', bold=True, color='FFFFFF', size=10)
    header_fill = PatternFill('solid', start_color='4472C4')
    body_font = Font(name='Arial', size=10)

    priority_fills = {
        'High': PatternFill('solid', start_color='FFC7CE'),
        'Medium': PatternFill('solid', start_color='FFEB9C'),
        'Low': PatternFill('solid', start_color='C6EFCE'),
    }

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )

    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_align = Alignment(horizontal='left', vertical='top', wrap_text=True)

    col_widths = [32, 12, 32, 16, 24, 40, 10, 24, 24, 24, 48]
    columns = ['接口Key', '用例编号', '测试标题', '前置条件', '优先级',
               '请求URL', '请求方法', '请求头', 'URL参数', '请求体参数', '预期结果']

    for iface_name, tcases in by_interface.items():
        ws = wb.create_sheet(title=iface_name[:31])

        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

        # Header row
        for ci, col_name in enumerate(columns, 1):
            cell = ws.cell(row=1, column=ci, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = thin_border

        # Data rows
        for ri, tc in enumerate(tcases, 2):
            url_params_str = '无'
            body_params_str = ''

            if tc.get('input_data'):
                try:
                    inp = json.loads(tc['input_data'])
                    if isinstance(inp, dict):
                        body_params_str = '\n'.join(f"{k}: {v}" for k, v in inp.items())
                except (json.JSONDecodeError, TypeError):
                    pass

            req_url = tc.get('input_data', '')
            if '?' in req_url:
                parts = req_url.split('?', 1)
                req_url = parts[0]
                if parts[1]:
                    url_params_str = parts[1].replace('&', '\n').replace('=', ': ')

            prio_fill = priority_fills.get(tc.get('priority', ''), None)

            values = [
                tc.get('key', ''),
                tc.get('case_id', ''),
                tc.get('title', ''),
                tc.get('precondition', ''),
                tc.get('priority', ''),
                req_url, '', '',
                url_params_str, body_params_str,
                tc.get('expected', ''),
            ]

            for ci, val in enumerate(values, 1):
                cell = ws.cell(row=ri, column=ci, value=val if val != '' else '无')
                cell.font = body_font
                cell.border = thin_border

                if ci == 1:
                    cell.alignment = Alignment(horizontal='center', vertical='top', wrap_text=True)
                elif ci == 5 and prio_fill:
                    cell.fill = prio_fill
                    cell.alignment = center_align
                elif ci == 7:
                    cell.alignment = center_align
                else:
                    cell.alignment = left_align

        ws.freeze_panes = 'A2'

    if 'Sheet' in wb.sheetnames:
        del wb['Sheet']

    wb.save(output_xlsx)
    total_cases = sum(len(v) for v in by_interface.values())
    print(f"[INFO] Excel 文件已生成: {output_xlsx}")
    print(f"[INFO] 共 {len(by_interface)} 个 Sheet，{total_cases} 条测试用例")


if __name__ == '__main__':
    main()
