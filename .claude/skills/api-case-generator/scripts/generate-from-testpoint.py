#!/usr/bin/env python3
"""从接口测试点文档生成测试用例（MD + Excel）"""
import os, re, json, sys, uuid, pathlib


def parse_testpoint_file(filepath):
    """解析接口测试点文档，提取接口信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    info = {}

    # 接口名称（从标题行提取）
    m = re.match(r'^# (.+)', content, re.M)
    if m:
        raw_name = m.group(1).strip()
        # 去掉末尾的下划线和英文后缀，得到中文功能名
        name_part = re.sub(r'_\w+\s*$', '', raw_name).strip()
        info['name'] = name_part
        info['full_name'] = raw_name

    # 请求方法
    m = re.search(r'### 请求方法\s*\n\s*(GET|POST|PUT|DELETE|PATCH)', content, re.I)
    info['method'] = m.group(1).upper() if m else 'GET'

    # 请求路径
    m = re.search(r'### 请求路径\s*\n\s*(\S+)', content)
    info['path'] = m.group(1) if m else '/'

    # URL参数
    url_params = []
    params_section = re.search(r'## 二、URL参数\s*\n(.*?)(?=## \u4e09|$)', content, re.S)
    if params_section:
        param_rows = re.findall(r'\|\s*(\w+)\s*\|\s*[^|]*\|\s*([^|]*)\s*\|', params_section.group(1))
        for pname, pdesc in param_rows:
            if pname == '参数名':
                continue
            # 检查是否真的无参数（空白行或"无"）
            if pname.strip() == '' or pname.strip() == '无':
                break
            url_params.append({
                'name': pname,
                'value': pdesc.split('：')[0].split(':')[0] if pdesc else '待补充',
                'description': pdesc.strip(),
                'required': '是'
            })
    info['url_params'] = url_params

    # 请求头参数
    headers = {}
    header_section = re.search(r'## 三、请求头参数\s*\n(.*?)(?=## 四|$)', content, re.S)
    if header_section:
        hrows = re.findall(r'\|\s*(\w+)\s*\|\s*[^|]*\|\s*([^|]*)\s*\|', header_section.group(1))
        for hname, hval in hrows:
            if hname in ('字段名',):
                continue
            headers[hname] = {'value': hval.strip(), 'desc': hval.strip()}
    info['headers'] = headers

    # 请求体格式
    body_type = 'JSON' if info['method'] in ('POST', 'PUT', 'PATCH') else '无'
    body_section = re.search(r'### 4\.1 请求体格式\s*\n(.*?)(?=### 4\.2|$)', content, re.S)
    if body_section:
        bm = re.search(r'\|\s*类型\s*\|\s*([^|]+)\s*\|', body_section.group(1))
        if bm:
            body_type = bm.group(1).strip()
    info['body_type'] = body_type

    # 请求体参数
    body_params = []
    if body_type != '无':
        bp_section = re.search(r'### 4\.2 参数定义\s*\n(.*?)(?=### 4\.3|$)', content, re.S)
        if bp_section:
            browss = re.findall(r'\|\s*(\w+)\s*\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*([^|]*)\s*\|', bp_section.group(1))
            for bname, bgenerator in browss:
                if bname in ('参数名',):
                    continue
                if bname.strip() == '' or bname.strip() == '无':
                    break
                body_params.append({
                    'name': bname,
                    'required': '是',
                    'type': 'string',
                    'generator': bgenerator.strip()
                })
    info['body_params'] = body_params

    # 构建URL（含query string）
    path = info['path']
    if url_params:
        qp = [f"{p['name']}={{{{ {p['name']} }}}}" for p in url_params if p.get('name')]
        if qp:
            path = f"{path}?{'&'.join(qp)}"
    info['url_with_query'] = path

    return info


def gen_login_testcases(name, method, path, url_params, body_params, body_type):
    """生成登录接口的测试用例数据"""
    has_body = body_type != 'no_body' and body_type != '无'
    is_safe = 'safe' in name.lower() or '加密' in name

    tcases = []
    cid = lambda: uuid.uuid4().hex

    # 功能测试 - 正确登录
    tcases.append({
        'key': name,
        'case_id': cid(),
        'module': '功能测试',
        'title': f'{name}-正确账号密码登录',
        'priority': 'High',
        'precondition': '系统已注册用户，用户状态正常',
        'steps': '1. 进入登录页面\n2. 输入正确的用户名和密码\n3. 点击登录按钮',
        'input_data': json.dumps({'username': '{{ 正确用户名 }}', 'password': '{{ 正确密码 }}'}, ensure_ascii=False),
        'expected': '响应状态码：200\ncode = 0\ndata.token 存在且非空\n跳转至首页'
    })

    # 功能测试 - token在URL中传递的接口
    if url_params and any(p['name'] in ('token', 'sign', 'time') for p in url_params):
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '功能测试',
            'title': f'{name}-携带有效token查询成功',
            'priority': 'High',
            'precondition': '已成功登录，获取到有效token',
            'steps': '1. 构造带token的请求URL\n2. 发起GET请求',
            'input_data': f'{path}?token={{{{ 有效token }}}}&time={{{{ 当前时间 }}}}',
            'expected': '响应状态码：200\ncode = 0\ndata 包含完整的用户余额/个人信息数据'
        })

    # 参数校验 - 必填缺失
    if body_params:
        for bp in body_params:
            tcases.append({
                'key': name,
                'case_id': cid(),
                'module': '参数校验',
                'title': f'{name}-{bp["name"]}参数缺失',
                'priority': 'Medium',
                'precondition': '无',
                'steps': f'1. 不填写{bp["name"]}字段\n2. 提交请求',
                'input_data': json.dumps({bp['name']: '' if not is_safe else None}, ensure_ascii=False),
                'expected': f'响应状态码：400 或\ncode != 0\nmsg 包含"{bp["name"]}"或"必填"或"不能为空"'
            })

    # 参数校验 - 空值
    if body_params:
        for bp in body_params:
            tcases.append({
                'key': name,
                'case_id': cid(),
                'module': '参数校验',
                'title': f'{name}-{bp["name"]}空字符串',
                'priority': 'Medium',
                'precondition': '无',
                'steps': f'1. 将{bp["name"]}设置为空字符串\n2. 提交请求',
                'input_data': json.dumps({bp['name']: ''}, ensure_ascii=False),
                'expected': f'响应状态码：400 或\ncode != 0\nmsg 包含{bp["name"]}相关的错误提示'
            })

    # 参数校验 - 错误凭证
    if body_params:
        username_bp = next((p for p in body_params if p['name'] == 'username'), None)
        password_bp = next((p for p in body_params if p['name'] == 'password'), None)
        if username_bp and password_bp:
            tcases.append({
                'key': name,
                'case_id': cid(),
                'module': '参数校验',
                'title': f'{name}-用户名或密码错误',
                'priority': 'Medium',
                'precondition': '系统中存在合法用户',
                'steps': '1. 输入错误的用户名或密码\n2. 点击登录按钮',
                'input_data': json.dumps({'username': '{{ 错误用户名 }}', 'password': '{{ 错误密码 }}'}, ensure_ascii=False),
                'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"账号或密码错误"'
            })

    # 业务逻辑 - 未登录访问需要认证的接口
    if url_params and any(p['name'] == 'token' for p in url_params):
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '业务逻辑',
            'title': f'{name}-无token访问',
            'priority': 'High',
            'precondition': '用户未登录，无token',
            'steps': '1. 不带token参数发起请求',
            'input_data': path,
            'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"未授权"或"Token"或"登录"'
        })

    # 业务逻辑 - 无效token
    if url_params and any(p['name'] == 'token' for p in url_params):
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '业务逻辑',
            'title': f'{name}-无效token访问',
            'priority': 'High',
            'precondition': '无',
            'steps': '1. 使用无效的token参数发起请求',
            'input_data': f'{path}?token={{{{ 无效token }}}}',
            'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"未授权"或"Token"或"登录"'
        })

    # 边界测试 - token过期
    if url_params and any(p['name'] == 'token' for p in url_params):
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '边界测试',
            'title': f'{name}-token过期访问',
            'priority': 'Medium',
            'precondition': '已过期token',
            'steps': '1. 使用过期的token参数发起请求',
            'input_data': f'{path}?token={{{{ 过期token }}}}',
            'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"token过期"或"请重新登录"'
        })

    # 异常场景 - 非法签名（balance接口）
    sign_p = next((p for p in url_params if p['name'] == 'sign'), None)
    if sign_p and 'balance' in name.lower():
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '参数校验',
            'title': f'{name}-非法签名字符串',
            'priority': 'Medium',
            'precondition': '无',
            'steps': '1. 构造非法签名的URL请求',
            'input_data': f'{path}?token={{{{ 有效token }}}}&time={{{{ 当前时间 }}}}&sign={{{{ 非法签名 }}}}',
            'expected': '响应状态码：403 或\ncode != 0\nmsg 包含"签名验证失败"'
        })

    # 异常场景 - time超时（balance接口）
    time_p = next((p for p in url_params if p['name'] == 'time'), None)
    if time_p and 'balance' in name.lower():
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '边界测试',
            'title': f'{name}-请求时间戳超时',
            'priority': 'Medium',
            'precondition': '无',
            'steps': '1. 使用超过10秒前的时间戳发起请求',
            'input_data': f'{path}?token={{{{ 有效token }}}}&time={{{{ 10秒前时间 }}}}&sign={{{{ 对应签名 }}}}',
            'expected': '响应状态码：400 或\ncode != 0\nmsg 包含"请求超时"或"时间无效"'
        })

    # 加密接口特有测试
    if is_safe:
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '参数校验',
            'title': f'{name}-未加密明文传输',
            'priority': 'Medium',
            'precondition': '无',
            'steps': '1. 直接传输未进行AES+Base64加密的用户名和密码\n2. 提交请求',
            'input_data': json.dumps({'username': 'tony', 'password': '123456'}, ensure_ascii=False),
            'expected': '响应状态码：400 或\ncode != 0\nmsg 包含"参数格式错误"或"解密失败"'
        })
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '边界测试',
            'title': f'{name}-特殊字符加密传输',
            'priority': 'Low',
            'precondition': '用户名或密码包含特殊字符（如@#$%&等）',
            'steps': '1. 输入含特殊字符的用户名和密码\n2. 进行加密处理\n3. 提交请求',
            'input_data': json.dumps({'username': '{{ 含特殊字符用户名(加密后) }}', 'password': '{{ 含特殊字符密码(加密后) }}'}, ensure_ascii=False),
            'expected': '响应状态码：200 或400\ncode = 0 表示加密传输成功；code != 0 表示服务器拒绝非标准密文'
        })

    # 通用异常场景
    tcases.append({
        'key': name,
        'case_id': cid(),
        'module': '异常场景',
        'title': f'{name}-HTTP请求异常',
        'priority': 'Low',
        'precondition': '无',
        'steps': '1. 关闭网络连接或配置不可达的域名\n2. 发起请求',
        'input_data': 'N/A',
        'expected': '连接超时或网络异常\n返回HTTP连接错误'
    })

    return tcases


def gen_default_testcases(name, method, path, url_params, body_params, body_type):
    """生成默认接口的测试用例（GET接口为主）"""
    tcases = []
    cid = lambda: uuid.uuid4().hex

    has_token = any(p['name'] == 'token' for p in url_params)

    # 功能测试 - 正常查询
    tcases.append({
        'key': name,
        'case_id': cid(),
        'module': '功能测试',
        'title': f'{name}-正常查询',
        'priority': 'High',
        'precondition': '已登录并获取有效token' if has_token else '无',
        'steps': f'1. 构造请求URL：{path}\n2. 携带必要参数发起{method}请求',
        'input_data': f'{path}' + (f'?token={{{{ 有效token }}}}' if has_token else ''),
        'expected': '响应状态码：200\ncode = 0\ndata 包含预期的业务数据'
    })

    # 参数校验 - token缺失
    if has_token:
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '参数校验',
            'title': f'{name}-token参数缺失',
            'priority': 'High',
            'precondition': '无',
            'steps': f'1. 不带token参数发起请求：{path}\n2. 提交请求',
            'input_data': path,
            'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"未授权"或"Token"'
        })

    # 业务逻辑 - 无效token
    if has_token:
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '业务逻辑',
            'title': f'{name}-无效token',
            'priority': 'High',
            'precondition': '无',
            'steps': f'1. 携带无效token参数发起请求\n2. 提交请求',
            'input_data': f'{path}?token={{{{ 无效token }}}}',
            'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"未授权"或"Token"'
        })

    # 边界测试 - token过期
    if has_token:
        tcases.append({
            'key': name,
            'case_id': cid(),
            'module': '边界测试',
            'title': f'{name}-token过期',
            'priority': 'Medium',
            'precondition': '已过期token',
            'steps': f'1. 携带过期token参数发起请求\n2. 提交请求',
            'input_data': f'{path}?token={{{{ 过期token }}}}',
            'expected': '响应状态码：401 或\ncode != 0\nmsg 包含"token过期"或"请重新登录"'
        })

    # 异常场景
    tcases.append({
        'key': name,
        'case_id': cid(),
        'module': '异常场景',
        'title': f'{name}-网络异常',
        'priority': 'Low',
        'precondition': '无',
        'steps': '1. 断开网络连接\n2. 发起请求',
        'input_data': 'N/A',
        'expected': '连接超时或网络异常'
    })

    return tcases


def generate_md(info, tcases, output_dir):
    """生成Markdown测试用例文件"""
    name = info['name'].replace('|', '').strip()
    # 清理文件名中的特殊字符
    safe_name = name
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '(', ')']:
        safe_name = safe_name.replace(ch, '')
    filename = f"{safe_name}_测试用例.md"
    filepath = os.path.join(output_dir, filename)

    # 构建接口参数列表（去重）
    seen = set()
    param_str = ''
    if info.get('url_params'):
        for p in info['url_params']:
            pname = p.get('name', '')
            if pname and pname not in seen:
                seen.add(pname)
                param_str += f"{pname}(必填,string), "
    if info.get('body_params'):
        for p in info['body_params']:
            pname = p.get('name', '')
            if pname and pname not in seen:
                seen.add(pname)
                param_str += f"{pname}(必填,string), "
    if not param_str:
        param_str = "无"
    param_str = param_str.rstrip(', ')

    lines = []
    lines.append(f"# {info['name']}测试用例")
    lines.append("")
    lines.append("## 接口信息")
    lines.append(f"- 接口路径：{info['path']}")
    lines.append(f"- 请求方法：{info['method']}")
    lines.append(f"- 请求参数：{param_str}")
    lines.append("")
    lines.append("## 测试用例")
    lines.append("")
    lines.append("| 用例编号 | 测试模块 | 测试点 | 优先级 | 前置条件 | 测试步骤 | 输入数据 | 预期结果 |")
    lines.append("|----------|----------|--------|--------|----------|----------|----------|----------|")

    for tc in tcases:
        steps_clean = tc['steps'].replace('\n', '→').replace('\r', '')
        input_clean = tc['input_data'].replace('\n', ' ').replace('\r', '').replace('|', '｜')
        expected_clean = tc['expected'].replace('\n', '<br>').replace('\r', '').replace('|', '｜')

        priority_map = {'High': 'P0', 'Medium': 'P1', 'Low': 'P2'}
        prio = priority_map.get(tc['priority'], 'P2')

        lines.append(f"| {tc['case_id']} | {tc['module']} | {tc['title']} | {prio} | {tc['precondition']} | {steps_clean} | {input_clean} | {expected_clean} |")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return filename


def generate_excel_data(all_interfaces_tcases, output_dir):
    """生成Excel用的中间JSON数据"""
    excel_json_path = os.path.join(output_dir, 'excel_data.json')
    with open(excel_json_path, 'w', encoding='utf-8') as f:
        json.dump(list(all_interfaces_tcases.values()), f, ensure_ascii=False, indent=2)
    return excel_json_path


def main():
    input_dir = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\jieliu666\python3_code\sublime_text03\05project\HCsource\.claude\doc\01-需求\接口文档'
    output_base = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\jieliu666\python3_code\sublime_text03\05project\HCsource\.claude\doc\02-测试'

    md_dir = os.path.join(output_base, 'MD')
    excel_dir = os.path.join(output_base, 'Excel')
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(excel_dir, exist_ok=True)

    # 收集所有接口的测试用例（用于Excel）
    all_interfaces_tcases = {}

    # 遍历输入目录中的所有测试点文件
    files = sorted([f for f in os.listdir(input_dir) if f.endswith('_测试点.md')])

    for fname in files:
        fpath = os.path.join(input_dir, fname)
        print(f"[INFO] 正在处理: {fname}")

        # 解析测试点文档
        info = parse_testpoint_file(fpath)
        name = info['name']
        method = info['method']
        path = info['path']
        url_params = info.get('url_params', [])
        body_params = info.get('body_params', [])
        body_type = info.get('body_type', 'JSON')

        # 判断是否为登录类接口（POST且有username/password）
        is_login = 'login' in name.lower() or '登录' in name

        # 生成测试用例
        if is_login or body_params:
            tcases = gen_login_testcases(name, method, path, url_params, body_params, body_type)
        else:
            tcases = gen_default_testcases(name, method, path, url_params, body_params, body_type)

        # 生成MD文件
        md_file = generate_md(info, tcases, md_dir)
        print(f"  → 已生成MD文件: {md_file} ({len(tcases)}条用例)")

        # 保存Excel数据
        all_interfaces_tcases[name] = tcases

    # 生成Excel中间JSON
    excel_json_path = generate_excel_data(all_interfaces_tcases, excel_dir)
    print(f"\n[INFO] 共处理 {len(files)} 个接口，生成 {sum(len(v) for v in all_interfaces_tcases.values())} 条测试用例")
    print(f"[INFO] MD文件已保存到: {md_dir}")
    print(f"[INFO] Excel数据已保存至: {excel_json_path}")
    print("[INFO] 下一步：运行 excel_from_json.py 生成Excel文件")


if __name__ == '__main__':
    main()
