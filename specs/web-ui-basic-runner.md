# Plan: Web UI — Basic Pipeline Runner

## Task Description
Add a minimal Flask web interface to the job finder project. The page presents a single "Run Pipeline" button. Clicking it triggers `run.main()` on the server, waits for completion, and displays the outcome (success/failure) plus the tail of the log file so the user can see what happened.

## Objective
A user can open `http://localhost:5000` in a browser, click **Run Pipeline**, and see whether the job-finder script ran successfully along with the last 50 log lines — without touching a terminal.

## Assumptions
- **Synchronous execution is fine for v1.** The pipeline typically completes in under 60 seconds; the browser will wait. Async/streaming is out of scope for this "basic" iteration.
- **No auth needed.** This is a local dev tool only.
- **Flask is already installed** (app.py already imports it) but is not pinned in requirements.txt — we add it.
- **Logging stays file-based.** We read the tail of `logs/run.log` after the run rather than redirecting stdout, which avoids conflicting with `run.py`'s own logging setup.

## Problem Statement
The job-finder pipeline can only be triggered from the command line (`python run.py`). A browser-based trigger is needed so the pipeline can be kicked off without a terminal.

## Solution Approach
Expand the stub `app.py` into a real Flask app with two routes:
- `GET /` — renders a static HTML page with the Run button and a results area.
- `POST /run` — calls `run.main()`, reads the last 50 lines of the log, returns JSON `{success: bool, logs: str}`.

The HTML page uses vanilla JS (`fetch`) to POST to `/run`, show a spinner while waiting, then display the result without a full page reload.

## Verified API Patterns
N/A — no external APIs in this plan. Flask is a local dependency.

## Relevant Files
- **`app.py`** — Flask app stub; will be expanded with the two routes and inline HTML serving.
- **`run.py`** — Contains `main() -> int` (0 = success, 1 = failure); imported and called directly by the web route.
- **`config.py`** — Provides `LOG_PATH`; used to read the log tail after each run.
- **`requirements.txt`** — Missing `flask`; needs it added.

### New Files
- **`templates/index.html`** — Minimal HTML page: Run button, status indicator, log output area.

## Implementation Phases

### Phase 1: Foundation
Add `flask` to `requirements.txt` so the dependency is tracked.

### Phase 2: Core Implementation
Expand `app.py` with the `GET /` and `POST /run` routes. Create `templates/index.html` with the button UI and fetch-based JS to call `/run` and display results.

### Phase 3: Integration & Polish
Verify the full round-trip: start Flask dev server, click button, confirm pipeline runs and log tail displays correctly.

## Team Orchestration

You operate as the team lead. Do not write code directly — deploy the builder and validator agents.

### Team Members

- Builder
  - Name: builder-web-ui
  - Role: Implement the Flask routes and HTML template
  - Agent Type: general-purpose
  - Resume: true

- Builder
  - Name: builder-deps
  - Role: Add Flask to requirements.txt
  - Agent Type: general-purpose
  - Resume: true

- Validator
  - Name: validator-web-ui
  - Role: Verify the Flask app starts, routes respond, and the run button works end-to-end
  - Agent Type: general-purpose
  - Resume: false

### Pipeline Determinism Map

| Node | Determinism | Inputs | Output | Can Change? |
|------|------------|--------|--------|-------------|
| Context7 lookup | NON-DETERMINISTIC | N/A | N/A | N/A |
| Plan creation | NON-DETERMINISTIC | Prompt + codebase | Plan document | Already non-deterministic |
| builder-deps | DETERMINISTIC | Plan document | requirements.txt edit | NO |
| builder-web-ui | DETERMINISTIC | Plan document + existing files | app.py + templates/index.html | NO |
| validator-web-ui | DETERMINISTIC | Code + acceptance criteria | Pass/Fail | NO |

## Step by Step Tasks

### 1. Add Flask to requirements.txt
- **Task ID**: add-flask-dep
- **Depends On**: none
- **Assigned To**: builder-deps
- **Agent Type**: general-purpose
- **Parallel**: true
- Open `requirements.txt` and add `flask>=3.0.0` on a new line after the existing deps.

### 2. Expand app.py with routes and template
- **Task ID**: build-flask-app
- **Depends On**: none
- **Parallel**: true
- **Assigned To**: builder-web-ui
- **Agent Type**: general-purpose
- Replace the stub `app.py` with the full implementation below.

**`app.py` target implementation:**
```python
import run as pipeline
import config
from flask import Flask, render_template, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_pipeline():
    exit_code = pipeline.main()
    try:
        with open(config.LOG_PATH, encoding="utf-8") as f:
            lines = f.readlines()
        log_tail = "".join(lines[-50:])
    except OSError:
        log_tail = "(log file not found)"
    return jsonify(success=(exit_code == 0), logs=log_tail)


if __name__ == "__main__":
    app.run(debug=True)
```

- Create `templates/index.html` with:
  - A centered card layout (no external CSS frameworks — inline styles only).
  - A `<button id="run-btn">Run Pipeline</button>`.
  - A `<div id="status">` showing idle / running / success / error state.
  - A `<pre id="log-output">` for displaying the log tail.
  - A `<script>` block using `fetch("POST /run")` — disable button while running, re-enable after, set status text and populate `<pre>` with `data.logs`.

**`templates/index.html` target implementation:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Job Finder</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #f5f5f5; display: flex; justify-content: center; padding: 3rem 1rem; }
    .card { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.12); padding: 2rem 2.5rem; max-width: 700px; width: 100%; }
    h1 { margin: 0 0 1.5rem; font-size: 1.4rem; }
    button { padding: .6rem 1.4rem; font-size: 1rem; border: none; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    #status { margin: 1rem 0 .5rem; font-weight: 600; }
    .success { color: #16a34a; }
    .error   { color: #dc2626; }
    .running { color: #9333ea; }
    pre { background: #1e1e1e; color: #d4d4d4; border-radius: 6px; padding: 1rem; font-size: .78rem; overflow-x: auto; max-height: 420px; overflow-y: auto; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Job Finder Pipeline</h1>
    <button id="run-btn" onclick="runPipeline()">Run Pipeline</button>
    <div id="status"></div>
    <pre id="log-output" style="display:none"></pre>
  </div>
  <script>
    async function runPipeline() {
      const btn = document.getElementById('run-btn');
      const status = document.getElementById('status');
      const logOutput = document.getElementById('log-output');

      btn.disabled = true;
      status.className = 'running';
      status.textContent = 'Running…';
      logOutput.style.display = 'none';

      try {
        const res = await fetch('/run', { method: 'POST' });
        const data = await res.json();
        status.className = data.success ? 'success' : 'error';
        status.textContent = data.success ? 'Pipeline completed successfully.' : 'Pipeline failed — see log below.';
        logOutput.textContent = data.logs;
        logOutput.style.display = 'block';
      } catch (err) {
        status.className = 'error';
        status.textContent = 'Request failed: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
```

### 3. Validate end-to-end
- **Task ID**: validate-all
- **Depends On**: add-flask-dep, build-flask-app
- **Assigned To**: validator-web-ui
- **Agent Type**: general-purpose
- **Parallel**: false
- Confirm `flask` appears in `requirements.txt`.
- Confirm `app.py` has `GET /` and `POST /run` routes.
- Confirm `templates/index.html` exists with the button and fetch script.
- Run `python -c "from app import app; print('OK')"` to verify the module imports cleanly.
- Optionally: `python -m flask --app app run` and navigate to `http://localhost:5000` to confirm the page loads.

## Acceptance Criteria
- `flask>=3.0.0` is present in `requirements.txt`.
- `GET /` serves an HTML page containing a "Run Pipeline" button.
- `POST /run` calls `run.main()`, returns JSON `{success: bool, logs: str}`.
- Clicking the button in the browser disables it, shows "Running…", then displays success/failure state and the log tail.
- `python -c "from app import app"` exits 0.

## Validation Commands
```bash
# Dependency check
python -c "import flask; print(flask.__version__)"

# Import check
python -c "from app import app; print('app import OK')"

# Start dev server (manual verification)
python app.py
# Then open http://localhost:5000 and click Run Pipeline
```

## Notes
- `run.py`'s `_setup_logging()` adds handlers each call; in the Flask process this will accumulate duplicate handlers on repeated `/run` calls. Not a bug for v1, but worth noting for future refactor.
- The `POST /run` route is synchronous; if the pipeline exceeds the browser's default timeout (varies, usually 5+ minutes) the request may be abandoned in the browser. The pipeline should complete well within that window.
- Future iterations: add SSE streaming of log output, a job results table, and a scheduler UI.
