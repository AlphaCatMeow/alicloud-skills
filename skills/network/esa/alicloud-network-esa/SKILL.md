---
name: alicloud-network-esa
description: Manage Alibaba Cloud Edge Security Acceleration (ESA) via OpenAPI/SDK. Use for site lifecycle management, DNS/record operations, origin and cache rules, WAF/security policy management, and diagnostics/troubleshooting for ESA resources.
---

Category: service

# Edge Security Acceleration (ESA)

## Validation

```bash
mkdir -p output/alicloud-network-esa
python -m py_compile skills/network/esa/alicloud-network-esa/scripts/list_openapi_meta_apis.py
echo "py_compile_ok" > output/alicloud-network-esa/validate.txt
```

Pass criteria: command exits 0 and `output/alicloud-network-esa/validate.txt` is generated.

## Output And Evidence

- Save API inventory and operation evidence under `output/alicloud-network-esa/`.
- Keep command parameters and region scope in evidence files.

Use Alibaba Cloud OpenAPI (RPC) with official SDKs or OpenAPI Explorer to manage ESA resources.
Prefer metadata-first API discovery before executing mutate operations.

## Prerequisites

- Prepare least-privilege RAM AccessKey/STS credentials.
- Confirm target region and site scope before change operations.
- Use read-only `List*` / `Describe*` APIs first, then execute create/update/delete APIs.

## Workflow

1) Confirm target site/domain/resource identifiers and desired operation.
2) Discover API names and required parameters via metadata and API Explorer.
3) Execute read-only validation (`Describe*` / `List*`).
4) Execute mutate operations (`Create*` / `Update*` / `Delete*`) with rollback plan.
5) Save outputs and request context under `output/alicloud-network-esa/`.

## AccessKey Priority

1) Environment variables: `ALICLOUD_ACCESS_KEY_ID` / `ALICLOUD_ACCESS_KEY_SECRET` / `ALICLOUD_REGION_ID`.
2) Shared config file: `~/.alibabacloud/credentials`.

If region is ambiguous, ask user before executing write operations.

## API Discovery

- Product code: `ESA`
- Default API version: `2024-09-10`
- Metadata source: `https://api.aliyun.com/meta/v1/products/ESA/versions/2024-09-10/api-docs.json`

## Minimal Executable Quickstart

```bash
python skills/network/esa/alicloud-network-esa/scripts/list_openapi_meta_apis.py
```

Optional overrides:

```bash
python skills/network/esa/alicloud-network-esa/scripts/list_openapi_meta_apis.py \
  --product-code ESA \
  --version 2024-09-10 \
  --output-dir output/alicloud-network-esa
```

## Common Operation Mapping

- Site lifecycle: `CreateSite`, `DeleteSite`, `DescribeSites`, `GetSite`
- DNS/record: `CreateRecord`, `UpdateRecord`, `DeleteRecord`, `DescribeRecords`
- Origin and routing: `CreateOriginPool`, `CreateOriginRule`, `CreateRedirectRule`, `CreateRewriteUrlRule`
- Cache/compression: `CreateCacheRule`, `CreateCompressionRule`
- Security: `CreateWafRule`, `CreateWafRuleset`, `BatchCreateWafRules`
- Delivery/logging: `CreateSiteDeliveryTask`, `DescribeSiteDeliveryTasks`

## Output Policy

Write all generated files and execution evidence under:
`output/alicloud-network-esa/`

## References

- Source list: `references/sources.md`
- API quick map: `references/api_quick_map.md`
