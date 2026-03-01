---
name: weather
description: "Get weather information for any location using wttr.in service"
homepage: https://github.com/chubin/wttr.in
metadata: {"chaobot":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# Weather Skill

Get current weather and forecasts for any location using the free wttr.in service.

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

### Tips

- URL-encode spaces: `wttr.in/New+York`
- Airport codes: `wttr.in/JFK`
- Units: add `?m` for metric (default), `?u` for US units
- Current only: `wttr.in/Hangzhou?0`
- Today only: `wttr.in/Hangzhou?1`

## Examples

**Simple query:**
```bash
curl -s "wttr.in/Beijing?format=3"
# Output: Beijing: ⛅️ +15°C
```

**Detailed query:**
```bash
curl -s "wttr.in/Shanghai?format=%l:+%c+%t+湿度%h+风速%w"
# Output: Shanghai: 🌧️ +18°C 湿度85% 风速↙15km/h
```

## Alternative: Open-Meteo API

For JSON response (programmatic use):
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=30.27&longitude=120.15&current_weather=true"
```

Find coordinates at https://open-meteo.com/en/docs
