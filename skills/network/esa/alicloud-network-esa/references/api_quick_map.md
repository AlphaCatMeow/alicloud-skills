# ESA API Quick Map (2024-09-10)

Use metadata inventory first:

```bash
python skills/network/esa/alicloud-network-esa/scripts/list_openapi_meta_apis.py
```

Common API families:

- Site management: `CreateSite`, `DeleteSite`, `DescribeSites`, `GetSite`
- DNS/Record: `CreateRecord`, `UpdateRecord`, `DeleteRecord`, `DescribeRecords`
- Origin/routing: `CreateOriginPool`, `CreateOriginRule`, `CreateRedirectRule`, `CreateRewriteUrlRule`
- Cache/performance: `CreateCacheRule`, `CreateCompressionRule`, `CreateNetworkOptimization`
- Security: `CreateWafRule`, `CreateWafRuleset`, `BatchCreateWafRules`
- Delivery/log: `CreateSiteDeliveryTask`, `DescribeSiteDeliveryTasks`

For authoritative parameter schemas, use the API Explorer links and metadata JSON.
