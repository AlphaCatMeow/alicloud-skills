---
name: alicloud-network-esa
description: Manage Alibaba Cloud ESA — deploy HTML/static sites via Pages, manage Edge Routines (ER) for serverless edge functions, use Edge KV for distributed key-value storage, and handle site management, DNS records, cache rules via OpenAPI/SDK. Use when working with ESA, edge deployment, edge functions, Pages, ER, KV storage, DNS, cache, or site configuration.
---

Category: service

# Edge Security Acceleration (ESA) - Pages, Edge Routine, KV, Site Management & More

Use Alibaba Cloud OpenAPI (RPC) with official Python SDK to manage all ESA capabilities.

Alibaba Cloud ESA provides four core capabilities:
- **Pages** — 部署 HTML 或静态目录到边缘节点（基于 Edge Routine 的快捷部署流程）
- **Edge Routine (ER)** — Serverless 边缘函数全生命周期管理
- **Edge KV** — 分布式边缘键值存储，支持 Namespace/Key/Value 管理
- **Site Management** — 站点管理、DNS 记录、缓存规则、证书等

统一使用 Python SDK 调用 ESA OpenAPI。

## Prerequisites

- Prepare AccessKey (RAM user/role with least privilege).
- Install Python SDK: `pip install alibabacloud_esa20240910 alibabacloud_tea_openapi alibabacloud_credentials`
- ESA OpenAPI is RPC style; prefer SDK or OpenAPI Explorer to avoid manual signing.

## SDK quickstart

```python
from alibabacloud_esa20240910.client import Client as Esa20240910Client
from alibabacloud_esa20240910 import models as esa_models
from alibabacloud_tea_openapi import models as open_api_models


def create_client(region_id: str = "cn-hangzhou") -> Esa20240910Client:
    config = open_api_models.Config(
        region_id=region_id,
        endpoint="esa.cn-hangzhou.aliyuncs.com",
    )
    return Esa20240910Client(config)
```

## Pages — 边缘页面部署

Pages 是基于 Edge Routine 的快捷部署流程，将 HTML 或静态目录部署到边缘。

### 部署 HTML 页面流程

```
CreateRoutine → GetRoutineStagingCodeUploadInfo → 上传代码到OSS
→ CommitRoutineStagingCode → PublishRoutineCodeVersion(staging)
→ PublishRoutineCodeVersion(production) → GetRoutine(获取访问URL)
```

### 部署静态目录流程

```
CreateRoutine → CreateRoutineWithAssetsCodeVersion → 打包zip上传OSS
→ 轮询 GetRoutineCodeVersionInfo(等待available)
→ CreateRoutineCodeDeployment(staging) → CreateRoutineCodeDeployment(production)
→ GetRoutine(获取访问URL)
```

### zip 包结构

zip 包结构取决于 `EDGE_ROUTINE_TYPE`（由 `checkEdgeRoutineType` 根据 entry 文件和 assets 目录是否存在自动判断）：

- **JS_ONLY**: `routine/index.js`（esbuild 打包或 `--no-bundle` 直接读取源文件）
- **ASSETS_ONLY**: `assets/` 下所有静态文件，保持原始目录结构
- **JS_AND_ASSETS**: `routine/index.js` + `assets/` 静态资源（最常见）

`assets/` 路径相对于配置中 `assets.directory`。配置优先级：命令行参数 > `esa.jsonc` / `esa.toml`。

### 关键注意事项

- **函数名规则**: 小写字母/数字/连字符，以小写字母开头，长度 >= 2
- **同名函数**: 若已存在则复用，部署新版本代码
- 默认同时部署到 staging 和 production
- 部署成功后通过 `GetRoutine` 获取 `defaultRelatedRecord` 作为访问域名

详细参考: `references/pages.md`

## Edge Routine (ER) — 边缘函数

通过 Python SDK 管理 Serverless 边缘函数的完整生命周期。

### 核心工作流

```
CreateRoutine → GetRoutineStagingCodeUploadInfo → 上传代码到OSS
→ CommitRoutineStagingCode → PublishRoutineCodeVersion
→ (CreateRoutineRoute) → GetRoutine
```

### API 摘要

- **函数管理**: `CreateRoutine`, `DeleteRoutine`, `GetRoutine`, `GetRoutineUserInfo`, `ListUserRoutines`
- **代码版本**: `GetRoutineStagingCodeUploadInfo`, `CommitRoutineStagingCode`, `PublishRoutineCodeVersion`, `DeleteRoutineCodeVersion`
- **路由**: `CreateRoutineRoute`, `UpdateRoutineRoute`, `DeleteRoutineRoute`, `GetRoutineRoute`, `ListRoutineRoutes`, `ListSiteRoutes`
- **关联记录**: `CreateRoutineRelatedRecord`, `DeleteRoutineRelatedRecord`, `ListRoutineRelatedRecords`

### ER 代码格式

```javascript
export default {
  async fetch(request) {
    return new Response("Hello", {
      headers: { "content-type": "text/html;charset=UTF-8" },
    });
  },
};
```

详细参考: `references/er.md`

## Edge KV — 边缘键值存储

分布式边缘键值存储，可在 Edge Routine 中读写，也可通过 OpenAPI/SDK 管理。

### 核心概念

- **Namespace**: KV 数据的隔离容器，Key 最大 512 字符，Value 最大 2MB（高容量 25MB）
- 支持 TTL 过期：`Expiration`（Unix 时间戳）或 `ExpirationTtl`（秒）

### API 摘要

- **Namespace**: `CreateKvNamespace`, `DeleteKvNamespace`, `GetKvNamespace`, `GetKvAccount`, `DescribeKvAccountStatus`
- **单键操作**: `PutKv`, `GetKv`, `GetKvDetail`, `DeleteKv`, `PutKvWithHighCapacity`
- **批量操作**: `BatchPutKv`, `BatchDeleteKv`, `BatchPutKvWithHighCapacity`, `BatchDeleteKvWithHighCapacity`, `ListKvs`

### 快速使用

```python
client = create_client()

# 创建 namespace
client.create_kv_namespace(esa_models.CreateKvNamespaceRequest(namespace="my-ns"))

# 写入
client.put_kv(esa_models.PutKvRequest(namespace="my-ns", key="k1", value="v1"))

# 读取
resp = client.get_kv(esa_models.GetKvRequest(namespace="my-ns", key="k1"))
```

详细参考: `references/kv.md`

## Site Management — 站点管理

使用 Python SDK 管理 ESA 站点、DNS 记录、缓存规则等。

### API behavior notes

- Most list APIs support pagination via `PageNumber` + `PageSize`.
- `ListSites` returns sites across all regions; no need to iterate regions.
- Newly created sites start as `pending`; complete access verification via `VerifySite` to activate.
- Deleting a site removes all associated configuration.
- `UpdateSiteAccessType` can switch between CNAME and NS, but switching to CNAME may fail if incompatible DNS records exist.
- DNS record APIs (`CreateRecord`, `ListRecords`, etc.) work for both NS and CNAME connected sites. **CNAME sites** are limited to `CNAME` and `A/AAAA` types only, and records cannot disable acceleration (proxy must stay enabled).
- DNS record `Type` parameter must be exact: use `A/AAAA` (not `A`), `CNAME`, `MX`, `TXT`, `NS`, `SRV`, `CAA`.
- `CreateCacheRule` supports two config types: `global` (site-wide default) and `rule` (conditional rule with match expression).

### Workflow

1) Confirm target site ID, access type (CNAME/NS), and desired action.
2) Find API group and exact operation name in `references/api_overview.md`.
3) Call API with Python SDK (preferred) or OpenAPI Explorer.
4) Verify results with describe/list APIs.
5) If you need repeatable inventory or summaries, use `scripts/` and write outputs under `output/alicloud-network-esa/`.

### SDK priority

1) Python SDK (preferred)
2) OpenAPI Explorer
3) Other SDKs (only if Python is not feasible)

### Python SDK scripts (recommended for inventory)

- List all ESA sites: `scripts/list_sites.py`
- Summarize sites by plan: `scripts/summary_sites_by_plan.py`
- Check site status: `scripts/check_site_status.py`
- List DNS records for a site: `scripts/list_dns_records.py`

## Common operation mapping

### Site Management

- Create site: `CreateSite`
- List sites: `ListSites` (supports `SiteName`, `Status`, `AccessType`, `Coverage` filters)
- Get site details: `GetSite`
- Delete site: `DeleteSite`
- Check site name availability: `CheckSiteName`
- Verify site ownership: `VerifySite`
- Update access type: `UpdateSiteAccessType`
- Update coverage: `UpdateSiteCoverage`
- Get current nameservers: `GetSiteCurrentNS`
- Update custom nameservers: `UpdateSiteVanityNS`
- Pause/resume site: `UpdateSitePause`, `GetSitePause`
- Site exclusivity: `UpdateSiteNameExclusive`, `GetSiteNameExclusive`
- Version management: `ActivateVersionManagement`, `DeactivateVersionManagement`

### Site Configuration

- IPv6: `GetIPv6`, `UpdateIPv6`

### DNS Records

NS access: full record type support. CNAME access: only `CNAME` and `A/AAAA`, proxy must stay enabled.

- Create record: `CreateRecord`
- List records: `ListRecords` (supports `Type`, `RecordName`, `Proxied` filters)
- Get record: `GetRecord`
- Update record: `UpdateRecord`
- Delete record: `DeleteRecord`
- Batch create: `BatchCreateRecords`
- Export records: `ExportRecords`

### Cache Rules

- Create cache rule: `CreateCacheRule`
- List cache rules: `ListCacheRules`
- Get cache rule: `GetCacheRule`
- Update cache rule: `UpdateCacheRule`
- Delete cache rule: `DeleteCacheRule`

**Cache rule expression notes (important):**
- `CreateCacheRule` parameters are **flat**, not a nested JSON `Rule` object.
- The `Rule` parameter is a match condition expression string. See **Rule Expression Syntax** section below.
- Quick reminders: `ends_with()`/`starts_with()` must use function-call style; `matches` (regex) requires standard plan or above.
- Set edge cache TTL with `--EdgeCacheMode override_origin --EdgeCacheTtl <seconds>`.

## Rule Expression Syntax

ESA uses a unified rule engine expression syntax across multiple features (cache rules, WAF custom rules, rate limiting, URL rewrite, header modification, etc.).

### When to use

Use this syntax for the `Rule` parameter in any ESA API that accepts a match condition expression:
- `CreateCacheRule` / `UpdateCacheRule` - Cache rules
- `CreateWafRule` / `UpdateWafRule` - WAF custom rules
- `CreateRatePlanRule` - Rate limiting rules
- `CreateRewriteUrlRule` / `UpdateRewriteUrlRule` - URL rewrite rules
- Origin rules, redirect rules, header modification rules, etc.

### Expression format

```
(condition)
(condition1 and condition2)
(condition1) or (condition2)
```

Max nesting depth: **2 levels**.

### Operator syntax - two styles

**Infix style** (operator between field and value):
```
(field eq "value")
(field ne "value")
(field contains "value")
(field in {"value1" "value2"})
(field matches "regex")
```

**Function style** (operator wraps field):
```
(starts_with(field, "value"))
(ends_with(field, "value"))
(exists(field))
(len(field) gt 100)
(lower(field) eq "value")
```

### Common patterns

```bash
# Match file extension
--Rule '(http.request.uri.path.extension eq "html")'

# Match multiple extensions
--Rule '(http.request.uri.path.extension in {"js" "css" "png" "jpg"})'

# Match URL prefix
--Rule '(starts_with(http.request.uri, "/api/"))'

# Match URL suffix
--Rule '(ends_with(http.request.uri, ".html"))'

# Match URL containing substring (value MUST start with /)
--Rule '(http.request.uri contains "/test")'

# Match specific host
--Rule '(http.host eq "www.example.com")'

# Combined conditions
--Rule '(http.request.uri contains "/test" and ip.geoip.country eq "CN")'

# Match by country
--Rule '(ip.geoip.country eq "CN")'

# Exclude path
--Rule '(not starts_with(http.request.uri, "/admin/"))'

# Negating set membership
--Rule '(not http.host in {"a.com" "b.com"})'
```

### Key gotchas

1. `ends_with` and `starts_with` must use **function-call syntax**, NOT infix.
2. `matches` (regex) requires **standard plan or above**; basic plan returns `RuleRegexQuotaCheckFailed`.
3. `contains` with URI must include path separator: `"/test"` is correct; `"test"` alone causes `CompileRuleError`.
4. List values in `in` operator are **space-separated** inside braces: `{"a.com" "b.com"}`.
5. Outer parentheses are **optional** for single conditions.
6. Use `ne` for "not equal", **never** use `not...eq`.
7. Use `not...in` for negating set membership (not before field), not `not in`.

### Plan limitations

| Plan | eq/ne/in/starts_with/ends_with | contains | matches (regex) |
|------|-------------------------------|----------|----------------|
| Basic | Supported | Supported | Not supported |
| Standard | Supported | Supported | Supported |
| Enterprise | Supported | Supported | Supported |

## AccessKey priority (must follow, align with README)

1) Environment variables: `ALICLOUD_ACCESS_KEY_ID` / `ALICLOUD_ACCESS_KEY_SECRET` / `ALICLOUD_REGION_ID`
Region policy: `ALICLOUD_REGION_ID` is an optional default. If unset, decide the most reasonable region for the task; if unclear, ask the user.
2) Shared config file: `~/.alibabacloud/credentials` (region still from env)

### Auth setup (README-aligned)

Environment variables:

```bash
export ALICLOUD_ACCESS_KEY_ID="your-ak"
export ALICLOUD_ACCESS_KEY_SECRET="your-sk"
export ALICLOUD_REGION_ID="cn-hangzhou"
```

Also supported by the Alibaba Cloud SDKs:

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-ak"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-sk"
```

Shared config file:

`~/.alibabacloud/credentials`

```ini
[default]
type = access_key
access_key_id = your-ak
access_key_secret = your-sk
```

## API discovery

- Product code: `ESA`
- Default API version: `2024-09-10`
- Metadata endpoint: `https://api.aliyun.com/meta/v1/products/ESA/versions/2024-09-10/api-docs.json`
- Use OpenAPI metadata endpoints to list APIs and get schemas (see references).

## Output policy

If you need to save responses or generated artifacts, write them under:
`output/alicloud-network-esa/`

## References

### Pages, ER & KV
- **Pages 部署参考**: `references/pages.md`
- **Edge Routine 参考**: `references/er.md`
- **Edge KV 存储参考**: `references/kv.md`

### Site Management
- API overview: `references/api_overview.md`
- Endpoints: `references/endpoints.md`
- Sites: `references/sites.md`
- DNS records: `references/dns-records.md`
- Cache: `references/cache.md`
- Sources: `references/sources.md`
- **Rule expression - generation guide**: `references/rule-generation-guide.md`
- **Rule expression - match fields**: `references/rule-match-fields.md`
- **Rule expression - operators**: `references/rule-operators.md`
- **Rule expression - examples**: `references/rule-examples.md`
