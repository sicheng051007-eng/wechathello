# 清浙小报 💗

给异地恋人的微信天气与鼓励定时推送。默认尽量在**北京时间每天 08:00 和 18:00**发送一张精简微信卡片；点击卡片可以查看完整天气、气温、活动建议和温柔鼓励。

项目已预置两个地点：

- 女朋友：清华园 · 北京
- 你：浙大紫金港 · 杭州

只配置女朋友的 OpenID，就只给她发送；配置两个人的 OpenID，双方都会收到各自所在地的消息。代码运行在 GitHub Actions，不需要电脑开机，也不需要购买服务器。

## 消息效果

```text
早安，宝贝 ☀️
📅 07月15日 周三｜🌏 清华园 · 北京
☁️ 晴朗 ☀️｜31℃｜雨0%
💡 天气适合出门
💌 愿你今天遇到的题都有思路
来自浙大的牵挂

👉 点击卡片查看完整内容
```

卡片字段会自动缩短，避免安卓微信显示省略号；完整内容由 GitHub Actions 生成手机网页并部署到 GitHub Pages。早晚使用不同的问候、活动建议和鼓励语，文案按日期稳定轮换。

## 为什么这样实现

调研过的早期热门方案（例如 [EverydayWechat](https://github.com/sfyc23/EverydayWechat)）大多依赖 ItChat 和网页版微信；项目说明也明确指出，账号不能登录网页版微信时就无法使用。清浙小报改用微信公众号测试号的模板消息接口，不模拟个人微信登录，适合无人值守运行。

天气来自 [Open-Meteo Forecast API](https://open-meteo.com/en/docs)，个人非商业低频使用无需 API Key。定时任务使用 [GitHub Actions 的时区感知 schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。GitHub 官方提示每小时整点更容易发生排队，因此工作流会在 07:55 和 17:55 提前准备内容，并等到 08:00 和 18:00 再发送；如果首次任务漏触发或发送失败，当小时内还会自动补偿重试。

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
📅 {{date.DATA}}｜🌏 {{location.DATA}}
☁️ {{weather.DATA}}
💡 {{activity.DATA}}
💌 {{encouragement.DATA}}
{{closing.DATA}}

👉 点击卡片查看完整内容
```

保存后记下生成的模板 ID。

### 3. 放到 GitHub

1. 在 GitHub 新建仓库。GitHub 免费账户使用 Pages 时请保持仓库为**公开仓库**。
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

然后打开 `Settings` → `Pages`，在 `Build and deployment` 的 `Source` 中选择 **GitHub Actions**。这是点击卡片查看完整内容所需的一次性设置。

### 4. 第一次手动测试

1. 打开仓库的 `Actions` 页面。
2. 左侧选择“每日微信推送”。
3. 点击 `Run workflow`。
4. `period` 选 `morning`，`dry_run` 保持 `false`，然后运行。
5. 工作流会先部署完整内容页，再发送带链接的精简卡片；全部任务显示绿色后，点击微信卡片即可查看全文。

如果只想先看排版、不实际发送，把 `dry_run` 改成 `true`，消息预览会出现在运行日志里，且不要求配置任何微信 Secret。

如果只想测试完整内容页，把 `deploy_only` 改成 `true`：工作流会部署 GitHub Pages，但不会发送微信。每天的定时任务不受这个手动选项影响。

完成一次手动测试后无需再操作。工作流会按北京时间自动运行：

```yaml
- cron: "55 7 * * *"             # 07:55 准备，等待到 08:00 发送
- cron: "12,27,42,57 8 * * *"    # 早间自动补偿重试
- cron: "55 17 * * *"            # 17:55 准备，等待到 18:00 发送
- cron: "12,27,42,57 18 * * *"   # 晚间自动补偿重试
```

每位收件人、每天、每个时段都有独立的成功标记。首次发送成功后，后续补偿任务会自动跳过该收件人；如果只有一人发送失败，也只会重试失败的人，不会让另一人重复收到消息。GitHub 定时任务仍属于 best effort，因此无法承诺精确到秒，但提前准备可以让正常情况下的发送时间尽量接近整点，多次补偿则显著降低整次漏发的概率。

## 个性化

编辑 [`config/recipients.json`](config/recipients.json) 可以修改：

- `name`：消息里的称呼，例如“小朋友”“宝宝”；
- `location.name`：显示名称；
- `latitude` / `longitude`：天气查询坐标；
- `signoff`：每条消息末尾的专属落款。

`openid_env` 是对应的 GitHub Secret 名称，通常无需修改。没有设置对应 OpenID 的收件人会自动跳过，所以不需要删除第二个人的配置。

鼓励语在 [`love_push/compose.py`](love_push/compose.py) 的 `MORNING_WORDS` 和 `EVENING_WORDS` 中，早晚各准备了 30 条；活动建议在 [`love_push/weather.py`](love_push/weather.py) 中按雨雪、高温、低温、大风、晴天和早晚时段分类。两类文案都会按日期和收件人稳定轮换，同一天重新运行不会反复变化，也可以直接替换为你们之间更有意义的话。项目保留原来的彩色 Emoji；根据安卓实机测试，地点使用兼容性更好的彩色地球 `🌏`，天气标题使用 `☁️`。

## 本地预览与测试（可选）

项目只使用 Python 标准库，没有第三方运行依赖。Python 3.11 以上可执行：

```bash
# 获取两地真实天气并预览，不发送微信
python -m love_push --period morning --dry-run
python -m love_push --period evening --dry-run

# 预览精简卡片（示例地址只用于预览）
python -m love_push --period morning --dry-run --page-base-url https://example.com/

# 运行全部测试
python -m unittest discover -s tests -v
```

本地运行仅用于开发和预览，正式定时推送完全由 GitHub Actions 负责。

## 稳定性与隐私设计

- 天气接口会自动重试；如果当天接口仍不可用，项目会继续发送问候和鼓励，并显示温和的天气降级文案。
- 一个收件人发送失败，不会阻止另一个收件人的消息；任务最后会标红，方便从 Actions 日志排查。
- 定时任务在当小时内自动补偿重试，并按收件人保存成功标记，避免重试导致重复推送。
- 同一地点只请求一次天气，避免不必要的 API 调用。
- 微信 appsecret、OpenID 和模板 ID 不进入仓库、不打印到日志。
- 详情页地址使用不可读的散列路径，页面声明禁止搜索引擎收录，且绝不会写入 OpenID；但免费 GitHub Pages 本质上仍是公开网页，不要在文案中放身份证号、电话等敏感信息。
- 微信消息发送请求不盲目重试，避免服务器已收到消息但响应丢失时造成重复推送。
- 每次推送前会自动运行单元测试，代码异常时停止发送。

## 常见问题

### 微信返回 `40003 invalid openid`

确认该 OpenID 来自**当前这个测试号**，且对方仍关注测试号。复制 Secret 时不要带空格。

### 微信返回 `40037 invalid template_id`

确认 `WECHAT_TEMPLATE_ID` 来自当前测试号，且模板内容中的字段名与本文完全一致。

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
│   ├── details.py           # 生成手机端完整内容页
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
