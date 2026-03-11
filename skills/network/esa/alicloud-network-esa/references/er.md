# Edge Routine (ER) — 边缘函数参考文档

ESA Edge Routine 是 Serverless 边缘函数服务，代码运行在全球边缘节点。支持完整生命周期管理：创建、提交代码、部署、路由配置、记录管理。

通过 Python SDK 调用 ESA OpenAPI 管理 Edge Routine。

## API 列表

### 函数管理

| API | 描述 | 关键参数 |
|-----|------|----------|
| `CreateRoutine` | 创建边缘函数 | `Name`(必填, 小写字母/数字/连字符, >=2字符), `Description`(可选) |
| `DeleteRoutine` | 删除边缘函数 | `Name`(必填) |
| `GetRoutine` | 获取边缘函数详情，含代码版本列表、关联记录、默认访问域名 | `Name`(必填) |
| `GetRoutineUserInfo` | 获取用户边缘函数总览信息 | 无参数 |
| `ListUserRoutines` | 分页列出账户下所有边缘函数 | `PageNumber`, `PageSize` |

### 代码版本管理

| API | 描述 | 关键参数 |
|-----|------|----------|
| `GetRoutineStagingCodeUploadInfo` | 获取代码上传 OSS 所需的签名信息 | `Name`(必填) |
| `CommitRoutineStagingCode` | 提交暂存代码，生成正式代码版本 | `Name`(必填), `CodeDescription`(可选) |
| `PublishRoutineCodeVersion` | 发布代码版本到 staging/production | `Name`(必填), `Env`(必填, "staging"/"production"), `CodeVersion`(必填) |
| `DeleteRoutineCodeVersion` | 删除代码版本 | `Name`(必填), `CodeVersion`(必填) |
| `CreateRoutineWithAssetsCodeVersion` | 创建带 assets 的代码版本（用于静态文件部署） | `Name`(必填), `CodeDescription`(可选) |
| `GetRoutineCodeVersionInfo` | 获取代码版本状态（init/available/failed） | `Name`(必填), `CodeVersion`(必填) |
| `CreateRoutineCodeDeployment` | 按比例部署代码版本到指定环境（用于 assets 部署） | `Name`(必填), `Env`(必填), `Strategy`(必填), `CodeVersions`(必填, JSON) |
| `ListRoutineCodeVersions` | 分页列出函数的代码版本 | `Name`(必填), `PageNumber`, `PageSize` |
| `GetRoutineCodeVersion` | 查询单个代码版本详情 | `Name`(必填), `CodeVersion`(必填) |

### 路由管理

| API | 描述 | 关键参数 |
|-----|------|----------|
| `CreateRoutineRoute` | 创建路由 | `SiteId`(必填), `Route`(路径,如`test.example.com/*`), `RoutineName`(必填), `RouteName`(必填), `RouteEnable`("on"/"off"), `Bypass`("on"/"off") |
| `UpdateRoutineRoute` | 修改路由配置 | `SiteId`(必填), `ConfigId`(必填), `RouteName`(必填), `RouteEnable`(必填), `Rule`(必填), `RoutineName`(必填), `Bypass`(必填) |
| `DeleteRoutineRoute` | 删除路由 | `SiteId`(必填), `ConfigId`(必填) |
| `GetRoutineRoute` | 获取路由详情 | `SiteId`(必填), `ConfigId`(必填) |
| `ListRoutineRoutes` | 列出函数的所有路由 | `RoutineName`(必填), `RouteName`(可选过滤), `PageNumber`, `PageSize` |
| `ListSiteRoutes` | 列出站点的所有路由 | `SiteId`(必填), `RouteName`(可选过滤), `PageNumber`, `PageSize` |

### 关联记录管理

| API | 描述 | 关键参数 |
|-----|------|----------|
| `CreateRoutineRelatedRecord` | 创建函数关联记录(域名)，触发函数执行 | `Name`(必填), `SiteId`(必填), `RecordName`(必填) |
| `DeleteRoutineRelatedRecord` | 删除关联记录 | `Name`(必填), `SiteId`(必填), `RecordName`(必填), `RecordId`(可选) |
| `ListRoutineRelatedRecords` | 列出函数的所有关联记录 | `Name`(必填), `PageNumber`, `PageSize`, `SearchKeyWord`(可选) |

## 标准工作流

### 创建并部署边缘函数（完整流程）

```
1. CreateRoutine                           → 创建函数
2. GetRoutineStagingCodeUploadInfo          → 获取上传签名
3. 上传代码到 OSS（使用签名信息 POST）       → 代码上传
4. CommitRoutineStagingCode                 → 提交代码版本
5. PublishRoutineCodeVersion(env=staging)   → 部署到测试环境
6. PublishRoutineCodeVersion(env=production)→ 部署到生产环境
7. (可选) CreateRoutineRoute               → 绑定自定义域名路由
8. (可选) CreateRoutineRelatedRecord       → 创建关联记录
9. GetRoutine                              → 获取详情，拿到默认访问 URL
```

### 代码格式要求

Edge Routine 代码必须导出 `fetch` handler：

```javascript
async function handleRequest(request) {
  return new Response("Hello World", {
    headers: { "content-type": "text/html;charset=UTF-8" },
  });
}

export default {
  async fetch(request) {
    return handleRequest(request);
  },
};
```

### 路由模式说明

路由的 `Rule` 字段使用 ESA 规则表达式，例如：
- `(http.host eq "test.example.com" and starts_with(http.request.uri.path, "/"))`

简化路径格式（如 `test.example.com/*`）需转换为规则表达式：
- 域名前 `*` = `ends_with(http.host, ".example.com")`
- 路径尾 `*` = `starts_with(http.request.uri.path, "/")`

## Python SDK 用法

```python
from alibabacloud_esa20240910.client import Client as Esa20240910Client
from alibabacloud_esa20240910 import models as esa_models
from alibabacloud_tea_openapi import models as open_api_models
import requests


def create_client(region_id: str = "cn-hangzhou") -> Esa20240910Client:
    config = open_api_models.Config(
        region_id=region_id,
        endpoint="esa.cn-hangzhou.aliyuncs.com",
    )
    return Esa20240910Client(config)


# 创建边缘函数
def create_routine(name: str, description: str = ""):
    client = create_client()
    request = esa_models.CreateRoutineRequest(name=name, description=description)
    return client.create_routine(request)


# 列出边缘函数
def list_routines():
    client = create_client()
    resp = client.get_routine_user_info()
    return resp.body


# 获取函数详情
def get_routine(name: str):
    client = create_client()
    request = esa_models.GetRoutineRequest(name=name)
    return client.get_routine(request)


# 删除边缘函数
def delete_routine(name: str):
    client = create_client()
    request = esa_models.DeleteRoutineRequest(name=name)
    return client.delete_routine_with_options(request)


# 上传代码并部署（完整流程）
def deploy_code(name: str, code: str, env: str = "production"):
    client = create_client()

    # 1. 获取上传签名
    upload_info = client.get_routine_staging_code_upload_info(
        esa_models.GetRoutineStagingCodeUploadInfoRequest(name=name)
    )
    oss_config = upload_info.body.oss_post_config

    # 2. 上传代码到 OSS
    form_data = {
        "OSSAccessKeyId": oss_config.ossaccess_key_id,
        "Signature": oss_config.signature,
        "callback": oss_config.callback,
        "x:codeDescription": oss_config.x_code_description,
        "policy": oss_config.policy,
        "key": oss_config.key,
    }
    requests.post(oss_config.url, data=form_data, files={"file": code.encode()})

    # 3. 提交代码版本
    commit_resp = client.commit_routine_staging_code(
        esa_models.CommitRoutineStagingCodeRequest(name=name)
    )
    code_version = commit_resp.body.code_version

    # 4. 部署
    client.publish_routine_code_version(
        esa_models.PublishRoutineCodeVersionRequest(
            name=name, env=env, code_version=code_version
        )
    )
    return code_version
```

### 路由管理

```python
# 创建路由
def create_route(site_id: int, routine_name: str, route_name: str, rule: str):
    client = create_client()
    request = esa_models.CreateRoutineRouteRequest(
        site_id=site_id,
        routine_name=routine_name,
        route_name=route_name,
        rule=rule,
        route_enable="on",
        bypass="off",
    )
    return client.create_routine_route(request)


# 列出函数路由
def list_routine_routes(routine_name: str):
    client = create_client()
    request = esa_models.ListRoutineRoutesRequest(routine_name=routine_name)
    return client.list_routine_routes(request)
```

### 关联记录管理

```python
# 创建关联记录
def create_related_record(name: str, site_id: int, record_name: str):
    client = create_client()
    request = esa_models.CreateRoutineRelatedRecordRequest(
        name=name, site_id=site_id, record_name=record_name
    )
    return client.create_routine_related_record(request)
```
