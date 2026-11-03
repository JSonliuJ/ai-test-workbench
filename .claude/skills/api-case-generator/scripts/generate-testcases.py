#!/usr/bin/env python3
"""generate-testcases.py — 根据接口文档生成测试用例 Markdown 文件和 Excel 文件"""
import uuid
import json
import os
import sys


# ==================== 接口数据定义（从接口文档提取） ====================
INTERFACES = [
    {
        "name": "账户余额",
        "key": "balance",
        "method": "GET",
        "path": "/balance",
        "params": [
            {"name": "sign", "required": "必填", "type": "string", "desc": "签名字段: base64(md5(token+time))"},
            {"name": "time", "required": "必填", "type": "integer", "desc": "请求时间:10秒内请求有效"},
            {"name": "token", "required": "必填", "type": "string", "desc": "登录后的令牌"},
        ],
        "has_body": False,
    },
    {
        "name": "登录接口",
        "key": "login",
        "method": "POST",
        "path": "/login",
        "params": [
            {"name": "username", "required": "必填", "type": "string", "desc": "用户名", "example": "admin"},
            {"name": "password", "required": "必填", "type": "string", "desc": "密码", "example": "123456"},
        ],
        "has_body": True,
        "body_type": "JSON",
    },
    {
        "name": "获取个人信息接口",
        "key": "info",
        "method": "GET",
        "path": "/info",
        "params": [
            {"name": "token", "required": "必填", "type": "string", "desc": "登录后的令牌"},
        ],
        "has_body": False,
    },
    {
        "name": "获取积分信息接口",
        "key": "integral",
        "method": "GET",
        "path": "/integral",
        "params": [
            {"name": "token", "required": "必填", "type": "string", "desc": "登录后的令牌"},
        ],
        "has_body": False,
    },
    {
        "name": "获取订单汇总信息接口",
        "key": "orderSummary",
        "method": "GET",
        "path": "/orderSummary",
        "params": [
            {"name": "token", "required": "必填", "type": "string", "desc": "登录后的令牌"},
        ],
        "has_body": False,
    },
    {
        "name": "登录接口 (加密 aes->base64)",
        "key": "login_safe",
        "method": "POST",
        "path": "/login_safe",
        "params": [
            {"name": "username", "required": "必填", "type": "string", "desc": "用户名 (加密后)", "example": "tony"},
            {"name": "password", "required": "必填", "type": "string", "desc": "密码 (加密后)", "example": "123456"},
        ],
        "has_body": True,
        "body_type": "JSON",
    },
]


def gen_id():
    """生成 32 位无横杠 UUID"""
    return uuid.uuid4().hex


def param_to_str(params):
    """将参数列表转为接口信息字符串"""
    parts = []
    for p in params:
        parts.append(f"{p['name']}({p['required']},{p['type']})")
    return ", ".join(parts)


def generate_testcases(interface):
    """为单个接口生成测试用例列表"""
    name = interface["name"]
    key = interface["key"]
    method = interface["method"]
    path = interface["path"]
    params = interface["params"]

    cases = []

    # ====== 功能测试 ======
    if method == "POST":
        # POST 接口的正常调用
        body_lines = []
        for p in params:
            example_val = p.get("example", "{{" + p["name"] + "}}")
            body_lines.append(f'  "{p["name"]}": "{example_val}"')
        body_example = "{\n" + ",\n".join(body_lines) + "\n}"
        cases.append({
            "module": "功能测试",
            "testpoint": f"{name} - 正确参数调用",
            "priority": "P0",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}",
            "input": body_example,
            "expected": "响应状态码：200\n响应 code 等于 0\nmsg 包含\"成功\"或空\n响应 data 非空",
        })
    else:
        # GET 接口的正常调用
        query_parts = []
        for p in params:
            placeholder = "{{" + p["name"] + "}}"
            query_parts.append(f'{p["name"]}={placeholder}')
        query_url = f"{path}?{'&'.join(query_parts)}" if query_parts else path
        cases.append({
            "module": "功能测试",
            "testpoint": f"{name} - 携带有效 token 调用",
            "priority": "P0",
            "prereq": "用户已登录，持有有效 token",
            "steps": f"发送{method}请求到{path}，传递有效的 token 参数",
            "input": query_url,
            "expected": "响应状态码：200\n响应 code 等于 0\n响应 data 包含业务数据",
        })

    # ====== 参数校验 ======
    for p in params:
        pname = p["name"]
        # 缺失参数
        cases.append({
            "module": "参数校验",
            "testpoint": f"{name} - 缺失{pname}参数",
            "priority": "P1",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，不传{pname}参数",
            "input": build_input(method, path, params, exclude=pname),
            "expected": "响应 code 不等于 0\nmsg 包含\"必填\"或\"参数\"或\"不能为空\"",
        })
        # 空值
        cases.append({
            "module": "参数校验",
            "testpoint": f"{name} - {pname}参数为空",
            "priority": "P1",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，传递空的{pname}参数",
            "input": build_input_empty(method, path, params, target=pname),
            "expected": "响应 code 不等于 0\nmsg 包含\"参数\"或\"不能为空\"或\"非法\"",
        })

    # ====== 异常场景 ======
    # Token 无效 / 错误凭证
    is_post = interface["method"] == "POST"
    has_token_param = any(p["name"] == "token" for p in params)
    if has_token_param:
        cases.append({
            "module": "异常场景",
            "testpoint": f"{name} - 无效 token",
            "priority": "P1",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，传递无效/伪造的 token",
            "input": build_input_with_fake(method, path, params),
            "expected": "响应状态码 401\n或响应 msg 包含\"未授权\"、\"Token\"、\"登录\"",
        })
    elif is_post:
        # 登录接口不需要 token，但需要正确的账号密码
        cases.append({
            "module": "异常场景",
            "testpoint": f"{name} - 错误账号密码",
            "priority": "P1",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，传递错误的账号和密码",
            "input": '{\n  "username": "{{错误账号}}",\n  "password": "{{错误密码}}"\n}',
            "expected": "响应 code 不等于 0\nmsg 包含\"账号\"或\"密码\"或\"错误\"或\"不存在\"",
        })

    # 未认证（不带任何凭证）
    if method == "POST":
        cases.append({
            "module": "异常场景",
            "testpoint": f"{name} - 空请求体",
            "priority": "P2",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，传递空请求体",
            "input": "{}",
            "expected": "响应 code 不等于 0\nmsg 包含\"必填\"或\"参数\"或\"不能为空\"",
        })
    else:
        cases.append({
            "module": "异常场景",
            "testpoint": f"{name} - 无 token 调用",
            "priority": "P1",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，不传递 token 参数",
            "input": path,
            "expected": "响应状态码 401\n或响应 code 不等于 0\nmsg 包含\"未授权\"或\"登录\"",
        })

    # ====== 边界测试 ======
    for p in params:
        pname = p["name"]
        if p["type"] == "integer":
            # 数值边界
            cases.append({
                "module": "边界测试",
                "testpoint": f"{name} - {pname}为负数",
                "priority": "P2",
                "prereq": "无",
                "steps": f"发送{method}请求到{path}，传递负数的{pname}",
                "input": build_input_with_value(method, path, params, pname, "-1"),
                "expected": "响应 code 不等于 0\n或响应 code 等于 0（取决于后端实现）",
            })
            cases.append({
                "module": "边界测试",
                "testpoint": f"{name} - {pname}超大数值",
                "priority": "P2",
                "prereq": "无",
                "steps": f"发送{method}请求到{path}，传递超大的{pname}",
                "input": build_input_with_value(method, path, params, pname, "999999999999"),
                "expected": "响应 code 不等于 0\n或响应 code 等于 0（取决于后端实现）",
            })
        elif p["type"] == "string":
            # 字符串超长
            cases.append({
                "module": "边界测试",
                "testpoint": f"{name} - {pname}超长字符串",
                "priority": "P2",
                "prereq": "无",
                "steps": f"发送{method}请求到{path}，传递超长的{pname}",
                "input": build_input_with_value(method, path, params, pname, "A" * 10000),
                "expected": "响应 code 不等于 0\nmsg 包含\"长度\"或\"超出\"或\"非法\"",
            })
            # SQL 注入尝试
            sql_injection = "'' OR ''1''=''1'; DROP TABLE;--"
            cases.append({
                "module": "边界测试",
                "testpoint": f"{name} - {pname}含特殊字符",
                "priority": "P2",
                "prereq": "无",
                "steps": f"发送{method}请求到{path}，传递含SQL注入字符的{pname}",
                "input": build_input_with_value(method, path, params, pname, sql_injection),
                "expected": "响应 code 不等于 0\nmsg 包含\"非法\"或\"格式\"或\"参数\"",
            })

    # ====== 业务逻辑 ======
    if method == "GET" and any(p["name"] == "token" for p in params):
        cases.append({
            "module": "业务逻辑",
            "testpoint": f"{name} - token 过期",
            "priority": "P1",
            "prereq": "无",
            "steps": f"发送{method}请求到{path}，传递已过期的 token",
            "input": build_input_with_fake(method, path, params),
            "expected": "响应状态码 401\n或响应 msg 包含\"过期\"或\"失效\"或\"登录\"",
        })

    return cases


def build_input(method, path, params, exclude=None):
    """构建输入数据"""
    if method == "POST":
        pairs = []
        for p in params:
            if p["name"] != exclude:
                pairs.append(f'  "{p["name"]}": "{{{{{p["name"]}}}}}"')
        if not pairs:
            return "{}"
        return "{\n" + ",\n".join(pairs) + "\n}"
    else:
        filtered = [p for p in params if p["name"] != exclude]
        if not filtered:
            return path
        return path + "?" + "&".join(f'{p["name"]}={{{{{p["name"]}}}}}' for p in filtered)


def build_input_empty(method, path, params, target=None):
    """构建空值输入"""
    if method == "POST":
        return "{\n" + ",\n".join(
            f'  "{p["name"]}": ""' if p["name"] == target else f'  "{p["name"]}": "{{{{{p["name"]}}}}}"'
            for p in params
        ) + "\n}"
    else:
        return path + "?" + "&".join(
            f'{p["name"]}=' if p["name"] == target else f'{p["name"]}={{{{{p["name"]}}}}}'
            for p in params
        )


def build_input_with_value(method, path, params, pname, value):
    """构建带特定值的输入"""
    if method == "POST":
        return "{\n" + ",\n".join(
            f'  "{p["name"]}": "{value}"' if p["name"] == pname else f'  "{p["name"]}": "{{{{{p["name"]}}}}}"'
            for p in params
        ) + "\n}"
    else:
        return path + "?" + "&".join(
            f'{p["name"]}={value}' if p["name"] == pname else f'{p["name"]}={{{{{p["name"]}}}}}'
            for p in params
        )


def build_input_with_fake(method, path, params):
    """构建使用伪造 token 的输入"""
    if method == "POST":
        return "{\n" + ",\n".join(
            f'  "{p["name"]}": "{{{{无效{p["name"]}}}}}"' for p in params
        ) + "\n}"
    else:
        return path + "?" + "&".join(
            f'{p["name"]}={{{{无效{p["name"]}}}}}' for p in params
        )


def generate_md(interface, cases):
    """生成 Markdown 内容"""
    name = interface["name"]
    md_lines = []
    md_lines.append(f"# {name}测试用例")
    md_lines.append("")
    md_lines.append("## 接口信息")
    md_lines.append(f"- 接口路径：{interface['path']}")
    md_lines.append(f"- 请求方法：{interface['method']}")
    md_lines.append(f"- 请求参数：{param_to_str(interface['params'])}")
    md_lines.append("")
    md_lines.append("## 测试用例")
    md_lines.append("")
    md_lines.append("| 用例编号 | 测试模块 | 测试点 | 优先级 | 前置条件 | 测试步骤 | 输入数据 | 预期结果 |")
    md_lines.append("|----------|----------|--------|--------|----------|----------|----------|----------|")

    for c in cases:
        cid = gen_id()
        input_data = c["input"].replace("\n", "\\n").strip()
        expected = c["expected"].replace("\n", "<br>")
        md_lines.append(
            f"| {cid} | {c['module']} | {c['testpoint']} | {c['priority']} "
            f"| {c['prereq']} | {c['steps']} | {input_data} | {expected} |"
        )

    md_lines.append("")
    return "\n".join(md_lines)


def generate_excel_rows(interfaces):
    """生成所有接口的 Excel 行数据"""
    all_rows = []
    for interface in interfaces:
        cases = generate_testcases(interface)
        for c in cases:
            cid = gen_id()
            row = {
                "接口Key": interface["key"],
                "用例编号": cid,
                "测试标题": f"{interface['name']} - {c['testpoint'].split(' - ', 1)[-1] if ' - ' in c['testpoint'] else c['testpoint']}",
                "前置条件": c["prereq"],
                "优先级": "High" if c["priority"] == "P0" else "Medium" if c["priority"] == "P1" else "Low",
                "请求URL": "{{base_url}}" + interface["path"],
                "请求方法": interface["method"],
                "请求头": "Content-Type: application/json" if interface["has_body"] else "无",
                "URL参数": build_excel_params(interface),
                "请求体参数": build_excel_body(interface),
                "预期结果": c["expected"].replace("\n", ""),
            }
            all_rows.append(row)
    return all_rows


def build_excel_params(interface):
    """构建 Excel 中的 URL 参数列"""
    if interface["has_body"]:
        return "无"
    return "; ".join(f'{p["name"]}: {{{{{p["name"]}}}}}' for p in interface["params"])


def build_excel_body(interface):
    """构建 Excel 中的请求体参数列"""
    if interface["has_body"]:
        return json.dumps(
            {p["name"]: f"{{{{{p['name']}}}}}" for p in interface["params"]},
            ensure_ascii=False,
        )
    return "无"


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-testcases.py <output_dir>")
        sys.exit(1)

    base_dir = sys.argv[1]
    md_dir = os.path.join(base_dir, "MD")
    excel_dir = os.path.join(base_dir, "Excel")
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(excel_dir, exist_ok=True)

    all_excel_rows = []

    for interface in INTERFACES:
        print(f"正在处理: {interface['name']} ({interface['method']} {interface['path']})")
        cases = generate_testcases(interface)

        # 生成 MD 文件
        md_content = generate_md(interface, cases)
        # 安全文件名：去除括号等特殊字符
        safe_name = interface["name"]
        for ch in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "(", ")"]:
            safe_name = safe_name.replace(ch, "")
        safe_name = safe_name.strip()
        filename = f"{safe_name}_测试用例.md"
        filepath = os.path.join(md_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"  -> 已生成: {filename} ({len(cases)} 条用例)")

        # 收集 Excel 数据
        rows = generate_excel_rows([interface])
        all_excel_rows.extend(rows)

    print(f"\n共生成 {len(INTERFACES)} 个接口的测试用例")
    print(f"Excel 数据: {len(all_excel_rows)} 行")

    # 保存 Excel 中间数据为 JSON（后续可用 xlsx 技能转换）
    meta = {
        "columns": ["接口Key", "用例编号", "测试标题", "前置条件", "优先级", "请求URL",
                     "请求方法", "请求头", "URL参数", "请求体参数", "预期结果"],
        "rows": all_excel_rows,
    }
    meta_path = os.path.join(excel_dir, "excel_data.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Excel 中间数据: {meta_path}")


if __name__ == "__main__":
    main()
