# 清浙小报

给异地恋人的微信天气与鼓励定时推送。默认在**北京时间每天 08:05 和 18:05**，分别把收件人所在校园的天气、气温、活动建议和一句温柔鼓励发送到微信。

项目已预置两个地点：

- 女朋友：清华园 · 北京
- 你：浙大紫金港 · 杭州

只配置女朋友的 OpenID，就只给她发送；配置两个人的 OpenID，双方都会收到各自所在地的消息。代码运行在 GitHub Actions，不需要电脑开机，也不需要购买服务器。

## 消息效果

```text
早安呀，宝贝！今天也一起加油 (^_^)

【日期】2026年07月15日 · 星期三
【地点】清华园 · 北京
【天气】晴朗｜降雨 0%｜湿度 52%
【气温】现在 31.5℃（体感 36.9℃）｜今日 23～34℃
【建议】天气适合出门，午间紫外线偏强，记得防晒补水

【给你】愿你今天遇到的题都有思路，走过的路都有好风景。
来自浙大的牵挂，隔着山海也一直想你 <3
天气数据：Open-Meteo
```

早晚使用不同的问候、活动建议和鼓励语。文案从项目内置的精选句子中按日期稳定轮换，不依赖质量不稳定的“情话接口”。

## 为什么这样实现

调研过的早期热门方案（例如 [EverydayWechat](https://github.com/sfyc23/EverydayWechat)）大多依赖 ItChat 和网页版微信；项目说明也明确指出，账号不能登录网页版微信时就无法使用。清浙小报改用微信公众号测试号的模板消息接口，不模拟个人微信登录，适合无人值守运行。

天气来自 [Open-Meteo Forecast API](https://open-meteo.com/en/docs)，个人非商业低频使用无需 API Key。定时任务使用 [GitHub Actions 的时区感知 schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。GitHub 官方提示每小时整点更容易发生排队，因此默认放在 08:05 和 18:05。

## 部署：约 10 分钟

### 1. 建立微信测试号

1. 打开[微信公众平台接口测试帐号](https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login)，用微信扫码登录。
2. 记下页面顶部的 `appID` 和 `appsecret`。
3. 在“测试号二维码”区域，让女朋友扫码关注；如果你也想收到消息，你也扫码关注。
4. 关注后，页面的“用户列表”会显示每个人的微信号/OpenID，分别记下来。

> 收件人必须先关注这个测试号。收到的是公众号测试号模板通知，不是伪装成你本人发出的私聊消息；这是个人开发者目前更稳定、也更合规的微信推送方式。

### 2. 新建消息模板

在测试号页面找到“模板消息接口”，点击“新增测试模板”：

- 模板标题：`清浙小报`
- 模板内容：完整复制下面内容，字段名不要改

```text
{{greeting.DATA}}

【日期】{{date.DATA}}
【地点】{{location.DATA}}
【天气】{{weather.DATA}}
【气温】{{temperature.DATA}}
【建议】{{activity.DATA}}

【给你】{{encouragement.DATA}}
{{closing.DATA}}
{{source.DATA}}
```

保存后记下生成的模板 ID。

### 3. 放到 GitHub

1. 在 GitHub 新建一个**私有仓库**。
2. 把本项目的全部文件上传并提交到默认分支（通常是 `main`）。
3. 打开仓库的 `Settings` → `Secrets and variables` → `Actions`。
4. 逐个新建以下 Repository secrets：

| Secret 名称 | 填写内容 | 必需 |
| --- | --- | --- |
| `WECHAT_APP_ID` | 测试号的 appID | 是 |
| `WECHAT_APP_SECRET` | 测试号的 appsecret | 是 |
| `WECHAT_TEMPLATE_ID` | 刚创建的模板 ID | 是 |
| `WECHAT_OPENID_GIRLFRIEND` | 女朋友关注测试号后显示的 OpenID | 是 |
| `WECHAT_OPENID_BOYFRIEND` | 你关注测试号后显示的 OpenID | 否 |

所有凭据都只放在 GitHub Secrets 中，不要把它们写进代码或截图发给别人。

### 4. 第一次手动测试

1. 打开仓库的 `Actions` 页面。
2. 左侧选择“每日微信推送”。
3. 点击 `Run workflow`。
4. `period` 选 `morning`，`dry_run` 保持 `false`，然后运行。
5. 任务显示绿色成功，微信通常会很快收到一条模板消息。

如果只想先看排版、不实际发送，把 `dry_run` 改成 `true`，消息预览会出现在运行日志里，且不要求配置任何微信 Secret。

完成一次手动测试后无需再操作。工作流会按北京时间自动运行：

```yaml
- cron: "5 8 * * *"    # 08:05
  timezone: "Asia/Shanghai"
- cron: "5 18 * * *"   # 18:05
  timezone: "Asia/Shanghai"
```

如一定要整点发送，可把 [`daily-push.yml`](.github/workflows/daily-push.yml) 中的两个 `5` 改为 `0`，同时更新工作流“判断早晚时段”步骤里的匹配文本。GitHub 定时任务是 best effort，平台繁忙时可能有几分钟延迟；默认避开整点可降低延迟或任务被丢弃的概率。

## 个性化

编辑 [`config/recipients.json`](config/recipients.json) 可以修改：

- `name`：消息里的称呼，例如“小朋友”“宝宝”；
- `location.name`：显示名称；
- `latitude` / `longitude`：天气查询坐标；
- `signoff`：每条消息末尾的专属落款。

`openid_env` 是对应的 GitHub Secret 名称，通常无需修改。没有设置对应 OpenID 的收件人会自动跳过，所以不需要删除第二个人的配置。

鼓励语在 [`love_push/compose.py`](love_push/compose.py) 的 `MORNING_WORDS` 和 `EVENING_WORDS` 中，可以直接替换为你们之间更有意义的话。模板消息不支持 Emoji；为兼容安卓，请使用 `(^_^)`、`<3` 等纯文本表情。

## 本地预览与测试（可选）

项目只使用 Python 标准库，没有第三方运行依赖。Python 3.11 以上可执行：

```bash
# 获取两地真实天气并预览，不发送微信
python -m love_push --period morning --dry-run
python -m love_push --period evening --dry-run

# 运行全部测试
python -m unittest discover -s tests -v
```

本地运行仅用于开发和预览，正式定时推送完全由 GitHub Actions 负责。

## 稳定性与隐私设计

- 天气接口会自动重试；如果当天接口仍不可用，项目会继续发送问候和鼓励，并显示温和的天气降级文案。
- 一个收件人发送失败，不会阻止另一个收件人的消息；任务最后会标红，方便从 Actions 日志排查。
- 同一地点只请求一次天气，避免不必要的 API 调用。
- 微信 appsecret、OpenID 和模板 ID 不进入仓库、不打印到日志。
- 微信消息发送请求不盲目重试，避免服务器已收到消息但响应丢失时造成重复推送。
- 每次推送前会自动运行单元测试，代码异常时停止发送。

## 常见问题

### 微信返回 `40003 invalid openid`

确认该 OpenID 来自**当前这个测试号**，且对方仍关注测试号。复制 Secret 时不要带空格。

### 微信返回 `40037 invalid template_id`

确认 `WECHAT_TEMPLATE_ID` 来自当前测试号，且模板内容中的 9 个字段名与本文完全一致。

### 微信返回 `40125 invalid appsecret`

重新复制测试号页面的 appsecret，检查 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 是否来自同一个测试号。

### Actions 没有定时运行

确认工作流文件已经在默认分支，仓库的 Actions 功能已启用。GitHub 说明：公共仓库连续 60 天无活动会自动停用 scheduled workflow；使用私有仓库也更适合保护你们的称呼、位置等隐私信息。

### 天气地点想改成玉泉、西溪或之江校区

只需在 `config/recipients.json` 修改显示名称与经纬度。天气逻辑无需改动。

## 项目结构

```text
.
├── .github/workflows/
│   ├── daily-push.yml       # 每日定时与手动推送
│   └── ci.yml               # 提交时运行测试
├── config/recipients.json   # 称呼、校园坐标、落款
├── love_push/
│   ├── cli.py               # 命令行入口
│   ├── compose.py           # 排版与鼓励语
│   ├── config.py            # 安全读取收件人配置
│   ├── http.py              # 带超时的 JSON 请求
│   ├── service.py           # 推送编排与故障降级
│   ├── weather.py           # 天气解析与活动建议
│   └── wechat.py            # 微信官方模板消息接口
└── tests/                   # 单元测试
```

## 参考与许可

- [微信公众平台接口测试帐号](https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login)
- [Open-Meteo Weather Forecast API](https://open-meteo.com/en/docs)
- [GitHub Actions scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [EverydayWechat](https://github.com/sfyc23/EverydayWechat)（同类项目调研）

本项目采用 [MIT License](LICENSE)。
