# roy-ai-editor

Roy 的 local-first AI 剪輯師。第一個 workflow 是把 YouTube Live 自動整理成可審核、可發布的多語卡拉 OK 歌曲影片。

目前狀態：V0 scaffold。先建立可重播的 CLI、專案資料模型與測試，再遷移 HACHI Birthday LIVE 2025 原型。

## Quick start

```bash
uv sync
uv run roy-editor --help
uv run pytest
```

## Product direction

- [North Star](NORTH_STAR.md)
- [Open-source landscape](docs/research/open-source-landscape.md)

大型影片、音訊、快取與渲染結果不進 Git，預設存放於 D 槽 workspace。
