---
name: alicloud-network-esa-test
description: Minimal smoke test for Alibaba Cloud ESA skill. Validate OpenAPI metadata discovery and API inventory generation for product ESA.
---

Category: test

# ESA 最小可用测试

## 前置条件

- 已具备网络访问能力。
- 目标技能：`skills/network/esa/alicloud-network-esa/`。

## 测试步骤

1) 执行：

```bash
python skills/network/esa/alicloud-network-esa/scripts/list_openapi_meta_apis.py \
  --product-code ESA \
  --version 2024-09-10 \
  --output-dir output/alicloud-network-esa-test
```

2) 检查输出文件是否存在：
- `output/alicloud-network-esa-test/ESA_2024-09-10_api_docs.json`
- `output/alicloud-network-esa-test/ESA_2024-09-10_api_list.md`

## 期望结果

- 命令执行成功。
- API 列表文件包含多条 API 名称（非空）。
