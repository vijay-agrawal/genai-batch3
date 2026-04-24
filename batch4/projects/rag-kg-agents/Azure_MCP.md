# MCP (Model Context Protocol) Support in Azure AI Foundry

> **What is MCP?**
> Model Context Protocol (MCP) is an open standard that lets AI models communicate with external tool servers in a uniform, vendor-neutral way. Think of it as "USB-C for AI tools" — a single plug that works regardless of the model or platform. Any MCP-compatible client (including Azure AI Foundry agents) can connect to any MCP server and use its tools.

---

## Table of Contents

1. [MCP in Azure AI Foundry — Overview](#1-mcp-in-azure-ai-foundry--overview)
2. [How MCP Works with Foundry Agents](#2-how-mcp-works-with-foundry-agents)
3. [MCP Support in the Azure AI Projects SDK](#3-mcp-support-in-the-azure-ai-projects-sdk)
4. [Build a Weather Tool (Python function)](#4-build-a-weather-tool-python-function)
5. [Build a Weather MCP Server](#5-build-a-weather-mcp-server)
6. [Host the MCP Server on Azure Functions (required for Foundry)](#6-host-the-mcp-server-on-azure-functions-required-for-foundry)
7. [Connect the MCP Server to an Azure AI Foundry Agent](#7-connect-the-mcp-server-to-an-azure-ai-foundry-agent)
8. [Test and Verify in the Foundry Playground](#8-test-and-verify-in-the-foundry-playground)
9. [Architecture Diagram](#9-architecture-diagram)
10. [Cost Breakdown](#10-cost-breakdown)
11. [Security Considerations](#11-security-considerations)
12. [Quick Reference](#12-quick-reference)

---

## 1. MCP in Azure AI Foundry — Overview

Azure AI Foundry supports MCP on **both sides** of the protocol:

| Role | Description |
|---|---|
| **MCP Client** | Foundry agents can connect to external MCP servers and use their tools |
| **MCP Server** | Azure Functions and Azure Container Apps can host your custom MCP servers |

### Key Benefits

- **Reuse**: Write a tool once as an MCP server — any agent (Foundry, Claude, Cursor, VS Code Copilot) can use it without modification.
- **Security**: Foundry agents authenticate to MCP servers using their **Entra Managed Identity** — no hard-coded secrets.
- **Discovery**: MCP servers advertise their tool list at runtime via the `tools/list` endpoint — no manual schema registration needed.
- **Composability**: Stack multiple MCP servers on a single agent — search, weather, CRM, calendar — each as a separate server.

---

## 2. How MCP Works with Foundry Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                   AZURE AI FOUNDRY AGENT                        │
│                                                                 │
│  ┌──────────────────────┐                                       │
│  │  LLM (gpt-4o-mini)  │                                        │
│  │  decides to call a  │                                        │
│  │  weather tool       │                                        │
│  └──────────┬───────────┘                                       │
│             │  tool call request                                │
│             ▼                                                   │
│  ┌──────────────────────┐         JSON-RPC 2.0 over HTTP(S)     │
│  │  MCP Client (built   │ ──────────────────────────────────►   │
│  │  into Foundry Agent  │                                       │
│  │  Service)            │ ◄──────────────────────────────────   │
│  └──────────────────────┘         tool result (JSON)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                         │
                              ┌──────────▼────────────┐
                              │   MCP SERVER          │
                              │                       │
                              │                       │
                              │  Tools exposed:       │
                              │  • get_current_weather│
                              │  • get_forecast       │
                              │  • get_alerts         │
                              └───────────────────────┘
```

### Communication flow (per tool call)

1. Agent receives user message: *"What is the weather in Mumbai right now?"*
2. LLM decides it needs the `get_current_weather` tool
3. Foundry Agent Service sends a `tools/call` JSON-RPC request to the MCP server URL
4. MCP server calls the real weather API and returns the result as JSON
5. LLM receives the result and composes a natural-language answer for the user

---

## 3. MCP Support in the Azure AI Projects SDK

Azure AI Foundry supports MCP servers via the `ToolSet` abstraction in the `azure-ai-projects` SDK (version ≥ 1.0.0b11).

### Install the SDK

```bash
pip install azure-ai-projects azure-identity mcp
```

### Register an MCP server as a tool provider

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import McpTool

client = AIProjectClient(
    endpoint="https://<your-project>.services.ai.azure.com/api/projects/<project-id>",
    credential=DefaultAzureCredential(),
)

# Define the MCP server connection
weather_mcp = McpTool(
    server_label="weather",                         # logical name used in the agent
    server_url="https://<your-mcp-server>/mcp",    # your MCP server endpoint
    allowed_tools=["get_current_weather", "get_forecast", "get_alerts"],  # optional allow-list
)

# Create an agent that uses the MCP tool
agent = client.agents.create_agent(
    model="gpt-4o-mini",
    name="weather-assistant",
    instructions=(
        "You are a helpful weather assistant. "
        "Use the weather tools to answer questions about current conditions and forecasts."
    ),
    tools=weather_mcp.definitions,
)
```

---

## 4. Build a Weather Tool (Python function)

Before building the MCP server, implement the core weather logic as a plain Python function. This keeps the business logic separate and testable.

### Prerequisites

```bash
pip install httpx python-dotenv
```

Get a free API key from [Open-Meteo](https://open-meteo.com/) (no key required) or [OpenWeatherMap](https://openweathermap.org/api).

### weather_service.py

```python
import httpx
from dataclasses import dataclass
from typing import Optional

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL   = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

@dataclass
class Coordinates:
    lat: float
    lon: float
    name: str
    country: str

def geocode(city: str) -> Optional[Coordinates]:
    """Convert a city name to latitude/longitude."""
    resp = httpx.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en"})
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    r = results[0]
    return Coordinates(lat=r["latitude"], lon=r["longitude"],
                       name=r["name"], country=r.get("country", ""))

def get_current_weather(city: str) -> dict:
    """
    Return current weather conditions for a city.

    Args:
        city: Name of the city (e.g. 'Mumbai', 'London', 'New York')

    Returns:
        dict with keys: city, country, temperature_c, feels_like_c,
                        humidity_pct, wind_speed_kmh, condition, condition_code
    """
    coords = geocode(city)
    if not coords:
        return {"error": f"City '{city}' not found"}

    resp = httpx.get(WEATHER_URL, params={
        "latitude": coords.lat,
        "longitude": coords.lon,
        "current": [
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "wind_speed_10m", "weathercode",
        ],
        "wind_speed_unit": "kmh",
    })
    resp.raise_for_status()
    current = resp.json()["current"]

    return {
        "city": coords.name,
        "country": coords.country,
        "temperature_c": current["temperature_2m"],
        "feels_like_c": current["apparent_temperature"],
        "humidity_pct": current["relative_humidity_2m"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "condition": WMO_CODES.get(current["weathercode"], "Unknown"),
        "condition_code": current["weathercode"],
    }

def get_forecast(city: str, days: int = 5) -> dict:
    """
    Return a multi-day weather forecast for a city.

    Args:
        city: Name of the city
        days: Number of forecast days (1–16, default 5)

    Returns:
        dict with keys: city, country, forecast (list of daily records)
    """
    days = max(1, min(days, 16))
    coords = geocode(city)
    if not coords:
        return {"error": f"City '{city}' not found"}

    resp = httpx.get(WEATHER_URL, params={
        "latitude": coords.lat,
        "longitude": coords.lon,
        "daily": [
            "weathercode", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "wind_speed_10m_max",
        ],
        "forecast_days": days,
        "wind_speed_unit": "kmh",
    })
    resp.raise_for_status()
    daily = resp.json()["daily"]

    forecast = []
    for i in range(len(daily["time"])):
        forecast.append({
            "date": daily["time"][i],
            "condition": WMO_CODES.get(daily["weathercode"][i], "Unknown"),
            "max_temp_c": daily["temperature_2m_max"][i],
            "min_temp_c": daily["temperature_2m_min"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "max_wind_kmh": daily["wind_speed_10m_max"][i],
        })

    return {"city": coords.name, "country": coords.country, "forecast": forecast}

def get_alerts(city: str) -> dict:
    """
    Return any active severe weather conditions for a city.

    Args:
        city: Name of the city

    Returns:
        dict with keys: city, has_alerts, alerts (list of alert descriptions)
    """
    weather = get_current_weather(city)
    if "error" in weather:
        return weather

    alerts = []
    code = weather.get("condition_code", 0)
    wind = weather.get("wind_speed_kmh", 0)

    if code in (95, 96, 99):
        alerts.append("THUNDERSTORM WARNING: Active thunderstorm in the area.")
    if code in (71, 73, 75):
        alerts.append("SNOW ADVISORY: Snowfall in progress.")
    if code in (65, 82):
        alerts.append("HEAVY RAIN WARNING: Heavy rain in progress.")
    if wind > 60:
        alerts.append(f"HIGH WIND ADVISORY: Wind speeds of {wind} km/h recorded.")

    return {
        "city": weather["city"],
        "has_alerts": len(alerts) > 0,
        "alerts": alerts if alerts else ["No active weather alerts."],
    }
```

---

## 5. Build a Weather MCP Server

Now wrap the weather functions above in an MCP server using [FastMCP](https://github.com/jlowin/fastmcp) — the fastest way to build MCP servers in Python.

### Install FastMCP

```bash
pip install fastmcp
```

### weather_mcp_server.py

```python
from fastmcp import FastMCP
from weather_service import get_current_weather, get_forecast, get_alerts

# Create the MCP server
mcp = FastMCP(
    name="weather-server",
    description="Provides real-time weather data and forecasts for any city worldwide.",
)

# ── Tool 1: Current weather ──────────────────────────────────────────────────

@mcp.tool()
def current_weather(city: str) -> dict:
    """
    Get the current weather conditions for a city.

    Use this tool when the user asks about the current or present weather,
    temperature, humidity, or wind for a specific location.

    Args:
        city: The name of the city (e.g. 'Mumbai', 'London', 'New York')
    """
    return get_current_weather(city)

# ── Tool 2: Forecast ─────────────────────────────────────────────────────────

@mcp.tool()
def weather_forecast(city: str, days: int = 5) -> dict:
    """
    Get a multi-day weather forecast for a city.

    Use this tool when the user asks about the upcoming weather, future
    temperature, or planning questions like 'will it rain this week?'.

    Args:
        city: The name of the city
        days: Number of days to forecast (1 to 16, default 5)
    """
    return get_forecast(city, days)

# ── Tool 3: Weather alerts ────────────────────────────────────────────────────

@mcp.tool()
def weather_alerts(city: str) -> dict:
    """
    Check for active severe weather alerts in a city.

    Use this tool when the user asks about safety conditions, storms,
    weather warnings, or whether it is dangerous to travel.

    Args:
        city: The name of the city to check for weather alerts
    """
    return get_alerts(city)

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # stdio transport — for local testing with MCP Inspector or Claude Desktop
    mcp.run()
```

### Run the server locally (stdio mode — for testing)

```bash
python weather_mcp_server.py
```

### Run the server as an HTTP endpoint (for Foundry agents)

```bash
# FastMCP supports streamable-HTTP (SSE) out of the box
fastmcp run weather_mcp_server.py --transport streamable-http --port 8000
```

The server is now available at `http://localhost:8000/mcp`.

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python weather_mcp_server.py
```

Open `http://localhost:5173` in your browser to call tools interactively and inspect responses.

---

## 6. Host the MCP Server on Azure Functions (required for Foundry)

> **Why a public endpoint is required**
>
> The Foundry Agent Service runs inside Microsoft's cloud infrastructure. When an agent calls an MCP tool, Foundry makes an outbound HTTPS request **from Azure** to your MCP server. This means your server must be reachable at a **public HTTPS URL** — `localhost:8000` only works for testing tools like MCP Inspector or Claude Desktop that run on your own machine.
>
> The recommended hosting option is **Azure Functions** on the Consumption Plan, which gives you:
> - A public `https://<name>.azurewebsites.net` endpoint automatically
> - Pay-per-execution pricing (very cheap for low-volume use)
> - No server management

### Prerequisites

```bash
# Install Azure CLI and Azure Functions Core Tools
# Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
# Functions Core Tools v4:
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Log in
az login
```

### Step 1 — Create Azure resources

```bash
# Set variables
RG="rg-weather-mcp"
LOCATION="eastus"
STORAGE="stweathermcp$RANDOM"   # must be globally unique, 3-24 lowercase alphanumeric
FUNC_APP="weather-mcp-fn-$RANDOM"

# Create resource group
az group create --name $RG --location $LOCATION

# Create storage account (required by Azure Functions)
az storage account create \
  --name $STORAGE \
  --location $LOCATION \
  --resource-group $RG \
  --sku Standard_LRS

# Create the Function App (Consumption plan = pay-per-use)
az functionapp create \
  --resource-group $RG \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNC_APP \
  --storage-account $STORAGE \
  --os-type Linux

echo "Function App URL: https://$FUNC_APP.azurewebsites.net"
```

### Step 2 — Create the project files

```
weather_mcp_azure/
├── function_app.py        ← Azure Functions entry point (new file)
├── weather_service.py     ← copy from §4
├── weather_mcp_server.py  ← copy from §5
├── requirements.txt
└── host.json
```

**requirements.txt**

```
azure-functions
fastmcp
httpx
```

**host.json**

```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

**function_app.py**

```python
import azure.functions as func
from fastmcp.server.http import create_sse_app
from weather_mcp_server import mcp  # import the FastMCP instance

# FastMCP → ASGI app → Azure Functions ASGI adapter
asgi_app = create_sse_app(mcp)

app = func.AsgiFunctionApp(
    app=asgi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS,  # use FUNCTION for key-based auth
)
```

> **Auth level**: `ANONYMOUS` lets Foundry call the endpoint without a key — simplest to start with. Switch to `FUNCTION` and pass the key in `McpTool` headers once everything works, or use Entra EasyAuth (see §11).

### Step 3 — Deploy

```bash
cd weather_mcp_azure

func azure functionapp publish $FUNC_APP --python
```

Expected output at the end:

```
Functions in weather-mcp-fn-XXXXX:
    weather_mcp - [httpTrigger]
        Invoke url: https://weather-mcp-fn-XXXXX.azurewebsites.net/api/mcp
```

### Step 4 — Verify the endpoint is live

```bash
# Should return the MCP server's tool list as JSON
curl https://weather-mcp-fn-XXXXX.azurewebsites.net/api/mcp
```

A successful response returns an SSE stream beginning with:
```
event: endpoint
data: /api/mcp?sessionId=...
```

Your public MCP server URL is now:
```
https://weather-mcp-fn-XXXXX.azurewebsites.net/api/mcp
```

### Step 5 — Enable Entra authentication (recommended for production)

```bash
# Give the Function App a Managed Identity
az functionapp identity assign --name $FUNC_APP --resource-group $RG

# Enable Entra EasyAuth — only callers with a valid Entra token can reach the function
az functionapp auth update \
  --name $FUNC_APP \
  --resource-group $RG \
  --enabled true \
  --action LoginWithAzureActiveDirectory \
  --aad-client-id <your-app-registration-client-id>
```

---

### Alternative: Deploy via Azure Portal UI (no CLI required)

> **What the portal can and cannot do**
>
> | Task | Via Portal? |
> |---|---|
> | Create resource group, storage account, Function App | Yes — full wizard UI |
> | Write Python code | No — write the files locally as normal |
> | Deploy code to Azure | Yes — ZIP upload via Deployment Center |
> | Set environment variables | Yes — Application Settings UI |
> | View logs and test the endpoint | Yes — Log Stream and Function Monitor |
>
> In short: you still write the same 5 files locally (Step 2 above), but you replace Steps 1, 3, and 4 with portal clicks.

#### Portal Step 1 — Create a Function App

1. Go to [portal.azure.com](https://portal.azure.com) and sign in.
2. Click **Create a resource** → search for **Function App** → click **Create**.
3. Fill in the **Basics** tab:

   | Field | Value |
   |---|---|
   | Subscription | Your subscription |
   | Resource Group | Create new → `rg-weather-mcp` |
   | Function App name | `weather-mcp-fn-<your-initials>` (must be globally unique) |
   | Runtime stack | **Python** |
   | Version | **3.11** |
   | Region | East US (or nearest to you) |
   | Operating System | **Linux** |
   | Hosting plan | **Consumption (Serverless)** |

4. Click **Next: Storage** → let Azure create a new storage account automatically.
5. Click **Review + create** → **Create**.
6. Wait ~1 minute. When deployment finishes, click **Go to resource**.
7. Note the **URL** shown on the overview page — it will be `https://weather-mcp-fn-<your-initials>.azurewebsites.net`. Your MCP endpoint will be at `/api/mcp`.

#### Portal Step 2 — Write code locally and zip the files

Write the same 5 files described in Step 2 of the CLI approach above, then zip them:

```bash
# Windows (PowerShell)
Compress-Archive -Path weather_mcp_azure\* -DestinationPath weather_mcp.zip

# macOS / Linux
cd weather_mcp_azure && zip -r ../weather_mcp.zip .
```

The zip must contain the files at the **root** (not inside a subfolder):

```
weather_mcp.zip
├── function_app.py
├── weather_service.py
├── weather_mcp_server.py
├── requirements.txt
└── host.json
```

#### Portal Step 3 — Upload the ZIP via Deployment Center

1. In your Function App, go to **Deployment** → **Deployment Center** in the left menu.
2. Under **Settings**, set **Source** to **External Git** or scroll down and look for the **Manual deploy** option.

   > The easiest path is the **Kudu ZIP deploy** endpoint, which the portal exposes via **Advanced Tools**:
   >
   > 1. Go to **Development Tools** → **Advanced Tools** → click **Go** (opens Kudu in a new tab).
   > 2. In Kudu, click **Tools** → **Zip Push Deploy** in the top menu.
   > 3. Drag and drop `weather_mcp.zip` onto the page.
   > 4. Kudu unzips the files, installs `requirements.txt`, and restarts the app automatically.

3. Back in the portal, go to **Functions** in the left menu — you should see **weather_mcp** listed as an HTTP trigger function.

#### Portal Step 4 — Verify in the portal

1. Click the function name (**weather_mcp**) → click **Get Function Url** → copy the URL.
2. Paste it in your browser or use the **Test/Run** tab in the portal to send a GET request.
3. A successful response returns an SSE stream starting with `event: endpoint`.

Your public MCP URL:
```
https://weather-mcp-fn-<your-initials>.azurewebsites.net/api/mcp
```

#### Portal Step 5 — Set environment variables (if needed)

If your weather service uses an API key or any environment variable:

1. Go to **Settings** → **Environment variables** in the left menu.
2. Click **+ Add** for each variable (e.g., `OPENWEATHER_API_KEY`).
3. Click **Apply** → **Confirm** to restart the app.

#### Portal Step 6 — Enable authentication (optional)

1. Go to **Settings** → **Authentication** in the left menu.
2. Click **Add identity provider** → choose **Microsoft**.
3. Follow the wizard — Azure creates an App Registration automatically and locks down the endpoint to Entra-authenticated callers only.

---

## 7. Connect the MCP Server to an Azure AI Foundry Agent

> **Prerequisite**: Your MCP server must be deployed and reachable at a public HTTPS URL (e.g., from §6 above). The Foundry Agent Service cannot reach `localhost`.

### Full working example

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import McpTool, ToolSet

# ── 1. Connect to your Foundry project ──────────────────────────────────────

client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_FOUNDRY_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# ── 2. Declare the MCP server ────────────────────────────────────────────────

weather_mcp = McpTool(
    server_label="weather",
    server_url=os.environ["WEATHER_MCP_SERVER_URL"],   # e.g. https://weather-mcp-fn-XXXXX.azurewebsites.net/api/mcp
    # Optional: restrict which tools this agent can use from the server
    allowed_tools=["current_weather", "weather_forecast", "weather_alerts"],
)

# ── 3. Create the agent ───────────────────────────────────────────────────────

agent = client.agents.create_agent(
    model="gpt-4o-mini",
    name="weather-assistant",
    instructions=(
        "You are a friendly weather assistant. "
        "Always state the city and country when reporting weather. "
        "Use metric units (°C, km/h, mm). "
        "If severe weather alerts exist, mention them prominently."
    ),
    tools=weather_mcp.definitions,
)
print(f"Agent created: {agent.id}")

# ── 4. Run a conversation ─────────────────────────────────────────────────────

thread = client.agents.threads.create()

client.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="What's the weather like in Mumbai today? Any storms coming?",
)

# process=True makes the SDK poll until the run completes
run = client.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id,
    tool_choice="auto",
)
print(f"Run status: {run.status}")

# ── 5. Print the response ────────────────────────────────────────────────────

messages = client.agents.messages.list(thread_id=thread.id)
for msg in messages:
    if msg.role == "assistant":
        print("\nAssistant:", msg.content[0].text.value)
        break

# ── 6. Clean up (optional) ───────────────────────────────────────────────────

client.agents.delete_agent(agent.id)
```

### Environment variables required

```bash
AZURE_AI_FOUNDRY_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<project-id>
WEATHER_MCP_SERVER_URL=https://weather-mcp-fn-XXXXX.azurewebsites.net/api/mcp
```

---

## 8. Test and Verify in the Foundry Playground

Once the MCP server is registered and the agent is created, you can test it directly in the Azure AI Foundry portal.

### Steps

1. Navigate to [ai.azure.com](https://ai.azure.com) → select your **Project**
2. Go to **Build** → **Agents** → select your `weather-assistant` agent
3. Click **Test** to open the **Agents Playground**
4. Type a weather question, e.g.:
   - *"What is the weather in Delhi right now?"*
   - *"Give me a 7-day forecast for London."*
   - *"Is it safe to travel to Chennai today?"*
5. In the **Trace** panel on the right, expand the tool call to see:
   - The exact `tools/call` request sent to your MCP server
   - The raw JSON response returned by the server
   - How the LLM incorporated the data into its answer

### Expected trace output

```
Run: weather-assistant
├── [user] "What is the weather in Mumbai right now?"
├── [tool call] current_weather(city="Mumbai")
│   └── MCP server: weather  →  GET open-meteo API
│       Response: { "city": "Mumbai", "temperature_c": 32.1, ... }
└── [assistant] "The current weather in Mumbai, India is 32°C (feels like 36°C)..."
```

---

## 9. Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                    AZURE AI FOUNDRY                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FOUNDRY AGENT SERVICE                                       │  │
│  │                                                              │  │
│  │   weather-assistant agent                                    │  │
│  │   ┌─────────────────┐    ┌────────────────────────────────┐ │  │
│  │   │  gpt-4o-mini    │───►│  MCP Client                    │ │  │
│  │   │  (reasoning)    │◄───│  (built into Agent Service)    │ │  │
│  │   └─────────────────┘    └──────────────┬─────────────────┘ │  │
│  └─────────────────────────────────────────│───────────────────┘  │
│                                            │                       │
│              Entra Managed Identity Auth   │  JSON-RPC over HTTPS  │
└────────────────────────────────────────────│───────────────────────┘
                                             │
                              ┌──────────────▼──────────────────┐
                              │  AZURE FUNCTIONS                  │
                              │  weather-mcp-fn                  │
                              │                                  │
                              │  FastMCP Server                  │
                              │  ┌────────────────────────────┐  │
                              │  │ Tool: current_weather      │  │
                              │  │ Tool: weather_forecast     │  │
                              │  │ Tool: weather_alerts       │  │
                              │  └────────────┬───────────────┘  │
                              └───────────────│──────────────────┘
                                             │
                                             │ HTTPS
                                             ▼
                              ┌──────────────────────────────────┐
                              │  Open-Meteo Weather API           │
                              │  (free, no key required)         │
                              └──────────────────────────────────┘
```

---

## 10. Cost Breakdown

Understanding costs before you deploy is important. The weather MCP stack uses three Azure services — here is what each costs.

### Azure Functions (hosts the MCP server)

| Plan | Cost model | Best for |
|---|---|---|
| **Consumption** (default) | First **1 million executions/month free**, then ~$0.20 per million. Plus ~$0.000016 per GB-second of execution time. | Development, demos, low-to-moderate traffic |
| **Flex Consumption** | Per-instance-second billing with faster cold starts. From ~$0.0000135/vCPU-sec. | Production with unpredictable traffic spikes |
| **Premium** | Fixed monthly cost (~$140+/month for EP1). | Production requiring VNet integration or always-warm instances |

**Practical estimate for a weather agent (dev/test):**

- Each MCP tool call ≈ 1 Azure Function execution, runs in ~500 ms, uses ~128 MB memory
- 10,000 calls/month ≈ well within the free tier → **$0/month**
- 1,000,000 calls/month → still mostly free tier → **~$1–2/month**

### Azure Storage Account (required by Functions)

- ~$0.018 per GB stored per month for LRS
- Functions uses < 1 MB of storage for code
- **Typical cost: < $0.10/month**

### Azure AI Foundry Agent Service (runs the agent)

Billed by the underlying model's token usage — the Foundry service itself has no additional per-call fee.

| Model | Input tokens | Output tokens |
|---|---|---|
| **gpt-4o-mini** | $0.15 / 1M tokens | $0.60 / 1M tokens |
| **gpt-4o** | $2.50 / 1M tokens | $10.00 / 1M tokens |

**Practical estimate for a weather query:**

- A typical weather question + tool call + response ≈ 500 input + 200 output tokens
- 1,000 queries/month with gpt-4o-mini → $0.075 input + $0.12 output → **~$0.20/month**

### Open-Meteo Weather API

- **Free, no API key required**, no rate-limit charges for reasonable use (< 10,000 calls/day)
- For higher volume, a commercial plan starts at ~€29/month

### Total estimated cost — typical dev/demo scenario

| Component | Monthly cost |
|---|---|
| Azure Functions (Consumption) | $0 (free tier) |
| Azure Storage Account | < $0.10 |
| Foundry Agent Service (gpt-4o-mini, ~1K queries) | ~$0.20 |
| Open-Meteo API | $0 |
| **Total** | **< $0.50/month** |

> To avoid surprise bills, set a **budget alert** in the Azure portal:
> **Cost Management** → **Budgets** → set a monthly budget with email alerts at 80% and 100% thresholds.

---

## 11. Security Considerations

| Concern | Recommendation |
|---|---|
| **Authentication** | Enable Entra EasyAuth on your Azure Function — only your Foundry agent's Managed Identity can call it |
| **Network isolation** | Deploy the Function App in a VNet and use Private Endpoints to restrict access |
| **Tool allow-listing** | Use `allowed_tools` in `McpTool` to restrict which tools each agent can call |
| **Input validation** | Validate city names in your weather service before forwarding to the external API |
| **API rate limits** | Cache weather results (e.g., 10-minute TTL using Azure Cache for Redis) to avoid hammering the weather API |
| **Secrets** | Store weather API keys in Azure Key Vault and reference them as Key Vault references in Function App settings |
| **HTTPS only** | Always use HTTPS for your MCP server URL — Azure Functions enforces this by default |

---

## 12. Quick Reference

### MCP server transports supported by Foundry

| Transport | Use case |
|---|---|
| `streamable-http` (SSE) | Production — HTTP endpoint, works with Foundry agents |
| `stdio` | Local testing — MCP Inspector, Claude Desktop |

### Useful FastMCP CLI commands

```bash
# Run with HTTP transport
fastmcp run weather_mcp_server.py --transport streamable-http --port 8000

# Inspect tools interactively
npx @modelcontextprotocol/inspector python weather_mcp_server.py

# List tools from a running server
fastmcp inspect http://localhost:8000/mcp
```

### MCP-related classes in `azure-ai-projects`

| Class | Purpose |
|---|---|
| `McpTool` | Defines a connection to an MCP server |
| `ToolSet` | Groups multiple tool providers (MCP + built-in) for an agent |
| `agent.tools` | List of tool definitions sent to the LLM |

### Minimal `.env` for local development

```bash
AZURE_AI_FOUNDRY_ENDPOINT=https://<project>.services.ai.azure.com/api/projects/<id>
WEATHER_MCP_SERVER_URL=http://localhost:8000/mcp
```

---

## Further Reading

- [MCP Support in Azure AI Foundry (Microsoft Docs)](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/model-context-protocol)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Open-Meteo Free Weather API](https://open-meteo.com/en/docs)
- [Azure Functions Python Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure AI Foundry Agent Service Overview](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [McpTool SDK Reference](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.models.mcptool)
