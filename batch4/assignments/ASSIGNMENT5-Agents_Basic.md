# Agent Assignments

Based on demos 01 to 04, complete the following two tasks.

---

## Task 1 — Extend the Weather Agent to Answer "How is the weather in Mumbai tomorrow?"

**Reference file:** `01agent_weather.py`

**Background:** The current agent hard-codes the question `"How is the weather in Mumbai?"` and only fetches current weather. The `get_weather` function does not return data to the caller, and there is no concept of a date. Work through the steps below one at a time before writing any code.

---

### Step 1 — Explore the OpenWeatherMap API

Before changing anything, understand what the API actually offers.

- The current code calls `data/3.0/onecall` — what does this endpoint return? Does it include tomorrow's forecast?
- Look up the `data/2.5/forecast` endpoint. What format does it return data in? How are future dates represented?
- How many hours ahead does the free forecast go? How are entries spaced?

> **Goal:** Know exactly which API call you need and what the response looks like before touching the code.

---

### Step 2 — Update the Tool to Accept a Date Parameter

Once you understand the API, update `get_weather`:

1. Add a `date` parameter to the function (e.g., `"today"` or `"tomorrow"`, or an actual date string like `"2026-04-23"`).
2. Switch the API call to `data/2.5/forecast` to get multi-day forecast data.
3. Filter the returned forecast entries to only those matching the requested date.
4. Make `get_weather` **return** a formatted string (temperature, description, rain probability) instead of just printing — the agent needs to pass this back to the LLM.
5. Update the function schema to include the `date` parameter with a clear description so the LLM knows how to use it.

---

### Step 3 — Explore: How Should the LLM Handle "tomorrow"?

This is the most interesting design question in the task. When the user says _"How is the weather in Mumbai tomorrow?"_, something needs to convert the word "tomorrow" into an actual date. Think about the options:

#### Option A — Let the LLM resolve it via the tool parameter
Pass `"tomorrow"` as-is in the `date` parameter and handle the conversion inside `get_weather` using Python's `datetime`. Simple, but the tool is doing date reasoning that arguably belongs elsewhere.

#### Option B — Use a second tool
Add a separate `get_current_date()` tool that returns today's date. The LLM can call this first, then calculate tomorrow's date itself before calling `get_weather`.
- Does the LLM correctly chain two tool calls?
- Look at how demo 04 handles multiple tools — can you adapt that pattern here?

#### Option C — Prompt engineering
Tell the LLM today's date in the system prompt (e.g., `"Today's date is 2026-04-22"`). The LLM can then resolve "tomorrow" to `2026-04-23` on its own before passing it to the tool.
- Simple and effective — but what happens if the system prompt date goes stale?

#### Option D — Pre-process the user query
Before sending the message to the LLM, replace relative terms like "tomorrow" or "next Monday" with actual dates in your Python code.
- More control, but you are now doing NLP work yourself. Is that the right layer for this?

> **Explore:** Try at least two of these approaches. Which produces the most reliable results? Which is the simplest to implement? What are the trade-offs?

---

### Step 4 — Close the Loop: Two-Turn Agent Pattern

Update the agent loop so the LLM can produce a natural language response:

1. First call → LLM returns a function call (name + arguments).
2. Execute the function with those arguments.
3. Second call → pass the function result back to the LLM and let it synthesize a natural response.

This is the same two-turn pattern from demo 03. Change the user message to: `"How is the weather in Mumbai tomorrow?"`

---

### Bonus Explorations

- **What if the user asks about a city that doesn't exist?** Add error handling so the agent responds gracefully instead of crashing.
- **What if the user asks for weather "this weekend" or "on Friday"?** How would you extend your chosen date-resolution approach to handle these?
- **Temperature units:** The API returns Kelvin by default. Add a `units` parameter (`metric` for Celsius, `imperial` for Fahrenheit) and expose it as a tool parameter.

**Expected outcome:** Running the script prints a natural language answer describing tomorrow's weather in Mumbai, with a clear understanding of *why* you chose your date-resolution approach.

---

## Task 2 — Add a Currency Converter Tool to the Multi-Tool Agent

**Reference file:** `04agent_multi_tools.py`

**Background:** Demo 04 has `get_weather`, `get_stock_price`, and `get_company_info` wired up using a dynamic function-definition approach via `inspect`. Adding a new function to `available_functions` is enough to expose it to the LLM automatically.

**Steps:**

1. Add a new function `get_exchange_rate(base_currency: str, target_currency: str)` that fetches the live exchange rate using the free API (no key required):
   ```
   https://open.exchangerate-api.com/v6/latest/{base_currency}
   ```
2. The function should return a dict with `base_currency`, `target_currency`, `rate`, and `date`.
3. Add a `format_function_result` branch for `"get_exchange_rate"` that returns a readable string, for example:
   ```
   1 USD = 83.45 INR (as of 2026-04-22)
   ```
4. Register the function in the `available_functions` dict — `get_function_definitions()` will pick it up automatically via `inspect`.
5. Update the system prompt to mention the new tool and describe when to use it.
6. Test with questions like:
   - `"What is 1 USD in INR?"`
   - `"Convert EUR to JPY"`

**Expected outcome:** The Streamlit app handles currency conversion queries alongside weather and stock queries, all within the same multi-tool agent loop.

---

## Key Concept to Remember

Both tasks reinforce the **two-turn agent loop**:

1. **First call** — LLM decides which function to call and returns the function name + arguments.
2. **You execute** the function with those arguments.
3. **Second call** — LLM receives the function result and synthesizes a natural language response.

This is the foundation of how tool-using agents work.
