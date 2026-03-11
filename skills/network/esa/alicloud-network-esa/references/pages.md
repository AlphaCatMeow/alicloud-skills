# ESA Pages — 边缘页面部署参考文档

ESA Pages 提供快速将 HTML 页面或静态文件目录部署到边缘节点的能力。底层基于 Edge Routine，通过 Python SDK 调用 ESA OpenAPI 完成部署。

## 部署 HTML 页面

### 流程

```
1. CreateRoutine(name)                     → 创建函数（已存在则跳过）
2. GetRoutineStagingCodeUploadInfo(name)   → 获取 OSS 上传签名
3. POST 代码到 OSS                          → 上传代码文件
4. CommitRoutineStagingCode(name)          → 提交代码版本
5. PublishRoutineCodeVersion(staging)       → 部署到测试环境
6. PublishRoutineCodeVersion(production)    → 部署到生产环境
7. GetRoutine(name)                        → 获取 defaultRelatedRecord 作为访问 URL
```

### 代码模板

HTML 内容需包装为 Edge Routine 代码：

```javascript
const html = `<html><body>Hello World</body></html>`;

async function handleRequest(request) {
  return new Response(html, {
    headers: { "content-type": "text/html;charset=UTF-8" },
  });
}

export default {
  async fetch(request) {
    return handleRequest(request);
  },
};
```

### Python SDK 示例

```python
from alibabacloud_esa20240910.client import Client as Esa20240910Client
from alibabacloud_esa20240910 import models as esa_models
from alibabacloud_tea_openapi import models as open_api_models
import requests


def create_client() -> Esa20240910Client:
    config = open_api_models.Config(
        region_id="cn-hangzhou",
        endpoint="esa.cn-hangzhou.aliyuncs.com",
    )
    return Esa20240910Client(config)


def deploy_html(name: str, html: str):
    """部署 HTML 页面到 ESA Pages"""
    client = create_client()

    # 转义模板字符串中的特殊字符
    escaped_html = html.replace("`", "\\`").replace("$", "\\$")
    code = f'''const html = `{escaped_html}`;

async function handleRequest(request) {{
  return new Response(html, {{
    headers: {{ "content-type": "text/html;charset=UTF-8" }},
  }});
}}

export default {{
  async fetch(request) {{
    return handleRequest(request);
  }},
}};'''

    # 1. 创建函数（已存在则跳过）
    try:
        client.create_routine(esa_models.CreateRoutineRequest(name=name))
    except Exception as e:
        if "RoutineNameAlreadyExist" not in str(e):
            raise

    # 2. 获取上传签名
    upload_info = client.get_routine_staging_code_upload_info(
        esa_models.GetRoutineStagingCodeUploadInfoRequest(name=name)
    )
    oss = upload_info.body.oss_post_config

    # 3. 上传代码到 OSS
    form_data = {
        "OSSAccessKeyId": oss.ossaccess_key_id,
        "Signature": oss.signature,
        "callback": oss.callback,
        "x:codeDescription": oss.x_code_description,
        "policy": oss.policy,
        "key": oss.key,
    }
    requests.post(oss.url, data=form_data, files={"file": code.encode()})

    # 4. 提交代码版本
    commit = client.commit_routine_staging_code(
        esa_models.CommitRoutineStagingCodeRequest(name=name)
    )
    version = commit.body.code_version

    # 5-6. 部署到 staging 和 production
    for env in ["staging", "production"]:
        client.publish_routine_code_version(
            esa_models.PublishRoutineCodeVersionRequest(
                name=name, env=env, code_version=version
            )
        )

    # 7. 获取访问 URL
    routine = client.get_routine(esa_models.GetRoutineRequest(name=name))
    domain = routine.body.default_related_record
    return f"https://{domain}" if domain else None
```

## 部署静态文件目录

### 流程

```
1. CreateRoutine(name)                            → 创建函数（已存在则跳过）
2. CreateRoutineWithAssetsCodeVersion(name)        → 创建 assets 代码版本，获取 OSS 签名
3. 打包目录为 zip → POST zip 到 OSS                → 上传 assets
4. 轮询 GetRoutineCodeVersionInfo(name, version)   → 等待状态变为 available
5. CreateRoutineCodeDeployment(staging, 100%)       → 部署到测试环境
6. CreateRoutineCodeDeployment(production, 100%)    → 部署到生产环境
7. GetRoutine(name)                                → 获取访问 URL
```

### zip 包结构

部署时创建的 zip 包结构取决于项目的 `EDGE_ROUTINE_TYPE`，共三种情况：

#### 1. JS_ONLY（只有入口文件）

```
your-project.zip
└── routine/
    └── index.js        ← 经 esbuild 打包（或 --no-bundle 时直接读取源文件）后的代码
```

#### 2. ASSETS_ONLY（只有静态资源）

```
your-project.zip
└── assets/
    ├── image.png
    ├── style.css
    └── subdir/
        └── data.json   ← assets 目录下的所有文件，保持原始目录结构
```

#### 3. JS_AND_ASSETS（入口文件 + 静态资源，最常见）

```
your-project.zip
├── routine/
│   └── index.js        ← 动态代码（打包后的 JS）
└── assets/
    ├── image.png
    └── ...             ← 静态资源，保持原始目录结构
```

#### 关键细节

- `index.js` 的内容来源：默认通过 prodBuild（esbuild）对入口文件打包产出；如果传了 `--no-bundle`，则直接读取源文件原文
- `assets/` 下的路径是相对于配置中 `assets.directory` 的相对路径，递归遍历所有子目录和文件
- zip 包最终通过 `zip.toBuffer()` 转成 Buffer，上传到 OSS（先调 API 拿 OSS 临时凭证，再 POST 上传），最多重试 3 次
- 项目类型的判断逻辑在 `checkEdgeRoutineType` 里，根据 entry 文件和 assets 目录是否实际存在来决定
- 配置来源优先级：命令行参数 > `esa.jsonc` / `esa.toml` 配置文件

### Python SDK 示例

```python
import os
import zipfile
import io
import time
import json
import requests


def deploy_folder(name: str, folder_path: str, description: str = ""):
    """部署静态目录到 ESA Pages"""
    client = create_client()

    # 1. 创建函数
    try:
        client.create_routine(
            esa_models.CreateRoutineRequest(name=name, description=description)
        )
    except Exception as e:
        if "RoutineNameAlreadyExist" not in str(e):
            raise

    # 2. 创建 assets 代码版本
    # 注意：此 API 需通过 callApi 方式调用
    from alibabacloud_tea_openapi import models as api_models
    params = api_models.Params(
        action="CreateRoutineWithAssetsCodeVersion",
        version="2024-09-10", protocol="https", method="POST",
        auth_type="AK", body_type="json", req_body_type="json",
        style="RPC", pathname="/",
    )
    body = {"Name": name, "CodeDescription": description}
    request = api_models.OpenApiRequest(body=body)
    runtime = {}
    result = client._client.call_api(params, request, runtime)
    oss_config = result.get("body", {}).get("OssPostConfig", {})
    code_version = result.get("body", {}).get("CodeVersion")

    # 3. 打包并上传 zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, folder_path).replace(os.sep, "/")
                zf.write(full, f"assets/{rel}")
    buf.seek(0)

    form_data = {
        "OSSAccessKeyId": oss_config["OSSAccessKeyId"],
        "Signature": oss_config["Signature"],
        "policy": oss_config["Policy"],
        "key": oss_config["Key"],
    }
    if oss_config.get("XOssSecurityToken"):
        form_data["x-oss-security-token"] = oss_config["XOssSecurityToken"]
    requests.post(oss_config["Url"], data=form_data, files={"file": buf.getvalue()})

    # 4. 等待版本就绪
    for _ in range(300):
        info = client._client.call_api(
            api_models.Params(
                action="GetRoutineCodeVersionInfo", version="2024-09-10",
                protocol="https", method="GET", auth_type="AK",
                body_type="json", req_body_type="json", style="RPC", pathname="/",
            ),
            api_models.OpenApiRequest(query={"Name": name, "CodeVersion": code_version}),
            {},
        )
        status = info.get("body", {}).get("Status", "").lower()
        if status == "available":
            break
        if status not in ("", "init"):
            raise RuntimeError(f"Build failed: {status}")
        time.sleep(1)

    # 5-6. 部署
    for env in ["staging", "production"]:
        client._client.call_api(
            api_models.Params(
                action="CreateRoutineCodeDeployment", version="2024-09-10",
                protocol="https", method="POST", auth_type="AK",
                body_type="json", req_body_type="json", style="RPC", pathname="/",
            ),
            api_models.OpenApiRequest(query={
                "Name": name, "Env": env, "Strategy": "percentage",
                "CodeVersions": json.dumps([{"Percentage": 100, "CodeVersion": code_version}]),
            }),
            {},
        )

    # 7. 获取访问 URL
    routine = client.get_routine(esa_models.GetRoutineRequest(name=name))
    domain = routine.body.default_related_record
    return f"https://{domain}" if domain else None
```

## 常见使用场景

### 1. 部署单个 HTML 页面

适合快速原型、游戏、演示页面：

```python
url = deploy_html("game-2048", "<html><body>...</body></html>")
print(f"访问地址: {url}")
```

### 2. 部署前端构建产物

适合 React/Vue/Angular 等前端项目的 dist/build 目录：

```python
url = deploy_folder("my-app", "/path/to/dist")
print(f"访问地址: {url}")
```

## 注意事项

1. **函数名称规则**: 只能用小写字母、数字、连字符，必须以小写字母开头，长度 >= 2
2. **同名函数**: 如果函数已存在，会复用已有函数并部署新版本代码
3. **部署环境**: 默认同时部署到 staging 和 production
4. **访问 URL**: 部署成功后通过 `GetRoutine` 的 `defaultRelatedRecord` 获取默认访问域名
5. **静态目录部署**: 目录不能为空；zip 内文件统一放在 `assets/` 前缀下
6. **HTML 转义**: 包装为 ER 代码时需转义反引号和 `$` 符号
7. **assets 部署**: `CreateRoutineWithAssetsCodeVersion` 和 `CreateRoutineCodeDeployment` 需通过 `callApi` 方式调用（SDK 未直接封装）