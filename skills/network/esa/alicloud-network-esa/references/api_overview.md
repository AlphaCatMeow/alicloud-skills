# ESA OpenAPI overview (2024-09-10) - Pages, ER, KV, Site Management, DNS & Cache

API index for Pages deployment, Edge Routine, Edge KV, site management, configuration, DNS records, and cache rules.
All APIs via Python SDK (`alibabacloud_esa20240910`).

## Pages (基于 Edge Routine)

底层调用 ER API 实现，完整流程见 `references/pages.md`。

### HTML 部署核心 API
- CreateRoutine - 创建边缘函数
- GetRoutineStagingCodeUploadInfo - 获取代码上传 OSS 签名
- CommitRoutineStagingCode - 提交代码版本
- PublishRoutineCodeVersion - 发布到 staging/production
- GetRoutine - 获取访问 URL

### 静态目录部署核心 API
- CreateRoutine - 创建边缘函数
- CreateRoutineWithAssetsCodeVersion - 创建带 assets 的代码版本
- GetRoutineCodeVersionInfo - 查询版本构建状态
- CreateRoutineCodeDeployment - 按比例部署到指定环境
- GetRoutine - 获取访问 URL

## Edge Routine (ER)

### 函数管理
- CreateRoutine - 创建边缘函数
- DeleteRoutine - 删除边缘函数
- GetRoutine - 获取边缘函数详情
- GetRoutineUserInfo - 获取用户边缘函数信息
- ListUserRoutines - 分页列出所有边缘函数

### 代码版本
- GetRoutineStagingCodeUploadInfo - 获取代码上传信息
- CommitRoutineStagingCode - 提交暂存代码版本
- PublishRoutineCodeVersion - 发布代码版本到 staging/production
- DeleteRoutineCodeVersion - 删除代码版本
- CreateRoutineWithAssetsCodeVersion - 创建带 assets 的代码版本 (静态目录部署使用)
- GetRoutineCodeVersionInfo - 获取代码版本状态
- CreateRoutineCodeDeployment - 创建代码部署 (assets 部署使用)
- ListRoutineCodeVersions - 分页列出代码版本
- GetRoutineCodeVersion - 查询单个代码版本详情
- UpdateRoutineConfigDescription - 修改函数描述

### 路由管理
- CreateRoutineRoute - 创建函数路由
- DeleteRoutineRoute - 删除函数路由
- GetRoutineRoute - 获取路由详情
- UpdateRoutineRoute - 修改函数路由
- ListRoutineRoutes - 列出函数路由
- ListSiteRoutes - 列出站点路由

### 关联记录管理
- CreateRoutineRelatedRecord - 创建函数关联记录 (域名)
- DeleteRoutineRelatedRecord - 删除函数关联记录
- ListRoutineRelatedRecords - 列出函数关联记录

## Edge KV

边缘键值存储，支持 Namespace 和 Key-Value 管理。

### Namespace 管理
- CreateKvNamespace - 创建 KV 存储空间
- DeleteKvNamespace - 删除 KV 存储空间
- GetKvNamespace - 查询单个 namespace 信息
- GetKvAccount - 查询账户 KV 使用信息及所有 namespace
- DescribeKvAccountStatus - 查询 Edge KV 是否已开通

### 单键操作
- PutKv - 写入键值对 (≤2MB)
- PutKvWithHighCapacity - 写入大容量键值对 (≤25MB)
- GetKv - 读取键的值
- GetKvDetail - 读取键值及 TTL 信息
- DeleteKv - 删除键值对

### 批量操作
- BatchPutKv - 批量写入键值对 (≤2MB)
- BatchPutKvWithHighCapacity - 批量写入大容量 (≤100MB)
- BatchDeleteKv - 批量删除键值对 (≤10000个)
- BatchDeleteKvWithHighCapacity - 批量删除大容量 (≤100MB)
- ListKvs - 列出 namespace 下所有键 (支持前缀过滤和分页)

## Site Management

- CreateSite - 添加站点
- ListSites - 列出站点 (支持分页和过滤)
- GetSite - 获取站点详情
- DeleteSite - 删除站点
- CheckSiteName - 检查站点名称可用性
- VerifySite - 验证站点所有权
- UpdateSiteAccessType - 更新接入方式 (CNAME/NS)
- UpdateSiteCoverage - 更新覆盖区域
- GetSiteCurrentNS - 获取当前NS服务器
- UpdateSiteVanityNS - 更新自定义NS
- UpdateSitePause - 暂停/恢复站点代理
- GetSitePause - 获取站点代理状态
- UpdateSiteNameExclusive - 设置站点独占
- GetSiteNameExclusive - 获取站点独占状态
- ActivateVersionManagement - 启用版本管理
- DeactivateVersionManagement - 禁用版本管理

## Site Configuration

- GetIPv6 - 获取IPv6配置
- UpdateIPv6 - 更新IPv6配置

## DNS Records

NS access: supports all record types. CNAME access: only `CNAME` and `A/AAAA`, and proxy (acceleration) cannot be disabled.

- CreateRecord - 创建DNS记录
- ListRecords - 列出DNS记录 (支持Type, RecordName, Proxied过滤)
- GetRecord - 获取DNS记录详情
- UpdateRecord - 更新DNS记录
- DeleteRecord - 删除DNS记录
- BatchCreateRecords - 批量创建DNS记录
- ExportRecords - 导出DNS记录

## Cache Rules

- CreateCacheRule - 创建缓存规则
- ListCacheRules - 列出缓存规则
- GetCacheRule - 获取缓存规则详情
- UpdateCacheRule - 更新缓存规则
- DeleteCacheRule - 删除缓存规则

## References

- Official API list: https://next.api.aliyun.com/document/ESA/2024-09-10/overview
- API metadata: https://api.aliyun.com/meta/v1/products/ESA/versions/2024-09-10/api-docs.json
