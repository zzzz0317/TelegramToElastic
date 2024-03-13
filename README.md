# TelegramToElastic

将 Telegram 的信息采集到 Elasticsearch 中

## 使用方法

```shell
# 安装依赖
pip install -r requirements.txt

# 修改配置文件
cp config.py.example config.py
nano config.py

# 启动
python main.py
```

## 配置文件

### 一定要改的地方
* TELEGRAM_API_ID
* TELEGRAM_API_HASH
* TELEGRAM_PROXY
* TELEGRAM_CHAT_LIST
* ELASTICSEARCH_CLIENT
* ELASTICSEARCH_INDEX

我猜你都看得懂hhhhh

### 不要改的地方
* 文件头部的 import
* TELEGRAM_CHAT_LATEST_MSG_ID

## Docker

使用 `docker` 文件夹内的文件辅助您将此应用 Docker 化。

不要忘记修改几个脚本内的 `/srv/pods/telegram-to-elastic` 为您的文件存放目录。
