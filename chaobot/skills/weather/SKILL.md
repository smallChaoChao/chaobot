---
name: weather
description: "Get weather information for any location using wttr.in service. IMPORTANT: wttr.in only accepts English/pinyin city names, NOT Chinese characters. Always convert Chinese city names to pinyin before querying."
homepage: https://github.com/chubin/wttr.in
metadata: {"chaobot":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# Weather Skill

Get current weather and forecasts for any location using the free wttr.in service.

## ⚠️ IMPORTANT: City Name Format

**wttr.in ONLY accepts English or pinyin city names. Chinese characters will FAIL.**

When user asks for Chinese cities, you MUST convert to pinyin:
- 北京 → Beijing
- 上海 → Shanghai
- 杭州 → Hangzhou
- 深圳 → Shenzhen
- 广州 → Guangzhou
- 成都 → Chengdu
- 西安 → Xian
- 南京 → Nanjing
- 武汉 → Wuhan
- 重庆 → Chongqing

For cities with multiple characters, concatenate pinyin without spaces:
- 哈尔滨 → Harbin
- 乌鲁木齐 → Urumqi
- 呼和浩特 → Hohhot
- 齐齐哈尔 → Qiqihar

## Usage

### Current Weather

Get current weather for a city:
```bash
curl -s "wttr.in/Hangzhou?format=3"
```

### Detailed Information

Get detailed weather with temperature, humidity, wind:
```bash
curl -s "wttr.in/Hangzhou?format=%l:+%c+%t+%h+%w"
```

Format codes:
- `%l` - location
- `%c` - condition (emoji)
- `%t` - temperature
- `%h` - humidity
- `%w` - wind
- `%m` - moon phase

### Full Forecast

Get 3-day forecast:
```bash
curl -s "wttr.in/Hangzhou?T"
```

## Examples

**Chinese city (convert to pinyin first):**
```bash
# User asks: "北京天气如何"
# You should query: Beijing
curl -s "wttr.in/Beijing?format=3"
# Output: Beijing: ⛅️ +15°C
```

**Detailed query:**
```bash
curl -s "wttr.in/Shanghai?format=%l:+%c+%t+湿度%h+风速%w"
# Output: Shanghai: 🌧️ +18°C 湿度85% 风速↙15km/h
```

**International cities:**
```bash
curl -s "wttr.in/London?format=3"
curl -s "wttr.in/New+York?format=3"
curl -s "wttr.in/Tokyo?format=3"
```

## Common Chinese Cities Reference

| Chinese | Pinyin | Command Example |
|---------|--------|-----------------|
| 北京 | Beijing | `wttr.in/Beijing` |
| 上海 | Shanghai | `wttr.in/Shanghai` |
| 广州 | Guangzhou | `wttr.in/Guangzhou` |
| 深圳 | Shenzhen | `wttr.in/Shenzhen` |
| 杭州 | Hangzhou | `wttr.in/Hangzhou` |
| 南京 | Nanjing | `wttr.in/Nanjing` |
| 成都 | Chengdu | `wttr.in/Chengdu` |
| 武汉 | Wuhan | `wttr.in/Wuhan` |
| 西安 | Xian | `wttr.in/Xian` |
| 重庆 | Chongqing | `wttr.in/Chongqing` |
| 苏州 | Suzhou | `wttr.in/Suzhou` |
| 天津 | Tianjin | `wttr.in/Tianjin` |
| 青岛 | Qingdao | `wttr.in/Qingdao` |
| 厦门 | Xiamen | `wttr.in/Xiamen` |
| 大连 | Dalian | `wttr.in/Dalian` |

## Tips

- URL-encode spaces: `wttr.in/New+York`
- Airport codes: `wttr.in/JFK`
- Units: add `?m` for metric (default), `?u` for US units
- Current only: `wttr.in/Beijing?0`
- Today only: `wttr.in/Beijing?1`

## Alternative: Open-Meteo API

For JSON response (programmatic use):
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=30.27&longitude=120.15&current_weather=true"
```

Find coordinates at https://open-meteo.com/en/docs
