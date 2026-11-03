#!/usr/bin/env python3
"""generate-api-testpoint.py — 从 Swagger JSON 生成接口测试点文档"""
import json
import uuid
import sys
import os

def generate_id():
    return uuid.uuid4().hex

def get_summary_path(path_name):
    """生成中文_英文格式的接口名称"""
    clean_path = path_name.strip('/').replace('/', '_')
    return f"{clean_path}_{clean_path}"

def extract_parameters(params, definitions=None):
    """提取参数列表"""
    param_list = []
    if not params:
        return param_list
    for p in params:
        param_info = {
            'name': p.get('name', ''),
            'required': '是' if p.get('required', False) else '否',
            'type': p.get('schema', {}).get('type', p.get('type', 'string')),
            'description': p.get('description', '待补充'),
            'example': p.get('x-example', p.get('example', '待补充'))
        }
        param_list.append(param_info)
    return param_list

def extract_request_body(params, consumes):
    """提取请求体参数（仅 POST/PUT/PATCH）"""
    # 从 parameters 中提取可能的 body 参数
    body_params = []
    for p in params or []:
        if p.get('in') == 'body':
            # 解析 $ref
            ref = p.get('schema', {}).get('$ref', '')
            if ref:
                schema_name = ref.split('/')[-1]
                if definitions and schema_name in definitions:
                    schema = definitions[schema_name]
                    body_params = extract_schema_properties(schema, definitions)
        elif p.get('in') in ['query', 'formData']:
            body_params.append({
                'name': p.get('name', ''),
                'required': '是' if p.get('required', False) else '否',
                'type': p.get('schema', {}).get('type', p.get('type', 'string')),
                'description': p.get('description', '待补充'),
                'example': p.get('x-example', p.get('example', '待补充'))
            })
    return body_params

def extract_schema_properties(schema, definitions, prefix=''):
    """递归提取 schema 属性"""
    props = []
    properties = schema.get('properties', {})
    required_list = schema.get('required', [])

    for name, prop in properties.items():
        full_name = f"{prefix}{name}" if not prefix else f"{prefix}.{name}"
        prop_info = {
            'name': full_name,
            'required': '是' if name in required_list else '否',
            'type': prop.get('type', 'string'),
            'description': prop.get('description', '待补充'),
            'example': prop.get('example', prop.get('x-example', '待补充'))
        }
        props.append(prop_info)

        # 递归处理嵌套对象
        if prop.get('type') == 'object' and prop.get('properties'):
            nested_ref = prop.get('properties')
            nested_schema = {'properties': nested_ref, 'required': []}
            nested_props = extract_schema_properties(nested_schema, definitions, full_name)
            props.extend(nested_props)

    return props

def main():
    if len(sys.argv) < 3:
        print("用法: python generate-api-testpoint.py <swagger.json> <output_dir>")
        sys.exit(1)

    swagger_file = sys.argv[1]
    output_dir = sys.argv[2]

    with open(swagger_file, 'r', encoding='utf-8') as f:
        swagger_data = json.load(f)

    paths = swagger_data.get('paths', {})
    definitions = swagger_data.get('definitions', {})
    host = swagger_data.get('host', '127.0.0.1:8080')
    base_path = swagger_data.get('basePath', '/')

    for path_name, path_item in paths.items():
        for method, operation in path_item.items():
            method_upper = method.upper()

            # 生成文件名（使用安全的文件名格式）
            summary = operation.get('summary', path_name)
            # 只使用中文和路径名，去除特殊字符
            safe_summary = summary.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 去掉括号中的内容（如加密说明）
            import re
            safe_summary = re.sub(r'\(.*?\)', '', safe_summary)
            filename = f"{safe_summary}_{path_name.replace('/', '_').strip('_')}_测试点.md"
            filepath = os.path.join(output_dir, filename)
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # 提取参数
            params = operation.get('parameters', [])
            consumes = operation.get('consumes', [])
            produces = operation.get('produces', [])

            # URL 参数
            url_params = [p for p in params if p.get('in') == 'query']

            # 请求体参数（仅 POST/PUT/PATCH）
            body_params = []
            if method_upper in ['POST', 'PUT', 'PATCH']:
                body_params = extract_request_body(params, consumes)

            # 响应信息
            responses = operation.get('responses', {})
            response_200 = responses.get('200', {})
            response_schema = response_200.get('schema', {})
            response_ref = response_schema.get('$ref', '')

            # 生成文档内容
            content = generate_doc(summary, path_name, method_upper, params,
                                  body_params, url_params, consumes, produces, response_ref, definitions)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"已生成: {filename}")

    print(f"\n共生成 {len(paths)} 个接口测试点文档")

def generate_doc(summary, path_name, method_upper, params, body_params, url_params, consumes,
                 produces, response_ref, definitions):
    """生成单个接口的 Markdown 文档"""
    doc_id = generate_id()
    name_en = path_name.strip('/').replace('/', '_')
    interface_name = f"{summary}_{name_en}"

    # 请求体类型
    if method_upper == 'GET':
        body_type = '无'
        body_desc = 'GET 请求，无请求体'
    elif 'application/json' in consumes:
        body_type = 'JSON'
        body_desc = '接口请求数据为 JSON 格式'
    else:
        body_type = '待补充'
        body_desc = '待补充'

    # Content-Type
    if method_upper == 'GET':
        content_type = '待补充'
    else:
        content_type = 'application/json'

    # 响应 Content-Type
    response_content_type = 'application/json'
    if produces:
        for prod in produces:
            if 'json' in prod:
                response_content_type = prod
                break

    # 构建文档
    lines = []
    lines.append(f"# {interface_name}\n")
    lines.append("## 一、基本信息\n")
    lines.append(f"### 接口ID\n{doc_id}\n")
    lines.append(f"### 接口名称\n{interface_name}\n")
    lines.append(f"### 请求方法\n{method_upper}\n")
    lines.append(f"### 请求路径\n{path_name}\n")
    lines.append(f"### 完整URL示例\n待补充\n")
    lines.append(f"### 描述\n{summary}\n")

    # URL 参数
    lines.append("## 二、URL参数\n")
    lines.append("| 参数名 | 值 | 说明 |")
    lines.append("| ------ | -- | ---- |")
    for p in url_params:
        example = p.get('x-example', p.get('example', '待补充'))
        desc = p.get('description', '待补充')
        lines.append(f"| {p.get('name', '')} | {example} | {desc} |")
    if not url_params:
        lines.append("|  |  |  |")
    lines.append("")

    # 请求头参数
    lines.append("## 三、请求头参数\n")
    lines.append("| 字段名 | 值 | 说明 |")
    lines.append("| ------ | -- | ---- |")
    lines.append(f"| Content-Type | {content_type} | 请求体格式 |")
    lines.append("| Authorization | 待补充 | 授权 Token（如 raw 中存在） |")
    lines.append("")

    # 请求体参数
    lines.append("## 四、请求体参数\n")
    lines.append("### 4.1 请求体格式\n")
    lines.append("| 类型 | 说明 |")
    lines.append("| ---- | ---- |")
    lines.append(f"| {body_type} | {body_desc} |")
    lines.append("")

    lines.append("### 4.2 参数定义\n")
    lines.append("| 参数名 | 必填 | 类型 | 说明 | 生成规则 |")
    lines.append("| ------ | ---- | ---- | ---- | -------- |")
    if body_params:
        for bp in body_params:
            lines.append(f"| {bp['name']} | {bp['required']} | {bp['type']} | {bp['description']} | {bp['example'] if bp['example'] != '待补充' else '待补充'} |")
    else:
        lines.append("| 无 |  |  |  |  |")
    lines.append("")

    lines.append("### 4.3 请求示例\n")
    lines.append("```json")
    if body_params:
        # 生成示例 JSON
        example_json = generate_example_json(body_params)
        lines.append(example_json)
    else:
        lines.append("// 待补充：请提供真实数据")
    lines.append("```\n")

    # 响应
    lines.append("## 五、响应\n")
    lines.append("### 5.1 正常响应\n")

    lines.append("#### 5.1.1 正常响应头\n")
    lines.append("| 字段名 | 值 | 说明 |")
    lines.append("| ------ | -- | ---- |")
    lines.append(f"| Content-Type | {response_content_type} | 响应体格式 |")
    lines.append("")

    lines.append("#### 5.1.2 正常响应体格式\n")
    lines.append("| 类型 | 说明 |")
    lines.append("| ---- | ---- |")
    lines.append("| JSON | 接口返回标准 JSON 格式数据 |")
    lines.append("")

    lines.append("#### 5.1.3 正常响应体参数\n")
    lines.append("| 字段路径 | 类型 | 说明 |")
    lines.append("| -------- | ---- | ---- |")

    # 解析响应结构
    if response_ref and definitions:
        schema_name = response_ref.split('/')[-1]
        if schema_name in definitions:
            resp_schema = definitions[schema_name]
            resp_props = resp_schema.get('properties', {})

            # 添加标准字段
            lines.append("| code | integer | 业务状态码，0 表示成功 |")
            lines.append("| msg | string | 业务提示信息 |")

            if 'body' in resp_props:
                body_schema = resp_props['body']
                if body_schema.get('type') == 'object' and body_schema.get('properties'):
                    body_name = body_schema.get('title', 'data')
                    lines.append(f"| data ({body_name}) | object | 业务响应数据主体 |")
                    # 递归展开 body 属性
                    for bname, bprop in body_schema.get('properties', {}).items():
                        lines.append(f"| data.{bname} | {bprop.get('type', 'string')} | {bprop.get('description', '待补充')} |")
    else:
        lines.append("| code | integer | 业务状态码 |")
        lines.append("| msg | string | 业务提示信息 |")
        lines.append("| data | object | 业务响应数据主体 |")
    lines.append("")

    lines.append("#### 5.1.4 正常响应示例\n")
    lines.append("```json")
    lines.append("// 待补充：录制批次中未捕获到正常响应体")
    lines.append("```\n")

    # 异常响应
    lines.append("### 5.2 异常响应\n")

    lines.append("#### 5.2.1 异常响应体格式\n")
    lines.append("| 类型 | 说明 |")
    lines.append("| ---- | ---- |")
    lines.append("| 待补充 | 待补充 |")
    lines.append("")

    lines.append("#### 5.2.2 异常响应体参数\n")
    lines.append("| 字段路径 | 类型 | 说明 |")
    lines.append("| -------- | ---- | ---- |")
    lines.append("| 待补充 | 待补充 | 待补充 |")
    lines.append("")

    lines.append("#### 5.2.3 异常响应示例\n")
    lines.append("```json")
    lines.append("// 待补充：录制批次中未捕获到异常响应")
    lines.append("```\n")

    lines.append("#### 5.2.4 异常响应状态码\n")
    lines.append("| 场景 | HTTP状态码 | code | msg |")
    lines.append("| ---- | ---------- | ---- | --- |")
    lines.append("| 身份未认证 | 401 | 待补充 | 待补充 |")
    lines.append("| 权限不足 | 403 | 待补充 | 待补充 |")
    lines.append("| 接口不存在 | 404 | 待补充 | 待补充 |")
    lines.append("")

    return '\n'.join(lines)

def generate_example_json(params):
    """根据参数生成示例 JSON"""
    example = {}
    for p in params:
        name = p['name']
        if p['example'] != '待补充':
            example[name] = p['example']
        else:
            example[name] = f"{{{{{name}}}}}"
    return json.dumps(example, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
