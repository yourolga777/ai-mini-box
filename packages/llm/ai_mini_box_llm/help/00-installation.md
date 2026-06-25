# Установка LLM плагина

## Базовая установка

```bash
pip install ai-mini-box-llm
```

## С локальным провайдером (llama-cpp-python)

```bash
pip install ai-mini-box-llm[local]
```

## С удалённым провайдером (OpenAI API)

```bash
pip install ai-mini-box-llm[remote]
```

## С поддержкой скачивания моделей

```bash
pip install ai-mini-box-llm[download]
```

## Всё сразу

```bash
pip install ai-mini-box-llm[local,remote,download]
```

## Настройка

После установки:

1. Выберите провайдера в `data/llm_config.json`
2. Для локального: скачайте модель `ai-mini-box llm download-model`
3. Для удалённого: укажите `api_key` в конфиге

```json
{
  "provider": "local",
  "model_path": "data/models/Qwen2.5-0.5B-Instruct-Q4.gguf"
}
```
