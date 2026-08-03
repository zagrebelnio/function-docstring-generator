const SAMPLE = `class Repository(BaseStore):
    table: str = "items"

    def __init__(self, url: str, retries: int = 3) -> None:
        self.url = url
        self.retries: int = retries

    def fetch(self, key: str, *, strict: bool = False) -> dict:
        if not key:
            raise ValueError("empty key")
        return {}


async def stream_rows(limit: int, *, offset: int = 0):
    for row in range(offset, limit):
        yield row
`;

const el = (id) => document.getElementById(id);
const codeInput = el('code');
const output = el('output');
const status = el('status');
const runButton = el('run');
const tabs = { docstrings: el('tab-docstrings'), facts: el('tab-facts') };

let mode = 'docstrings';

const cache = new Map();

const cacheKey = (endpoint, body) => `${endpoint}:${JSON.stringify(body)}`;

const escapeHtml = (value) =>
  String(value).replace(
    /[&<>"]/g,
    (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch],
  );

el('load-sample').addEventListener('click', () => {
  codeInput.value = SAMPLE;
  codeInput.focus();
});

Object.entries(tabs).forEach(([name, button]) => {
  button.addEventListener('click', () => {
    mode = name;
    Object.entries(tabs).forEach(([key, other]) =>
      other.setAttribute('aria-selected', String(key === name)),
    );
    run();
  });
});

runButton.addEventListener('click', run);

codeInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) run();
});

async function run() {
  const code = codeInput.value.trim();
  if (!code) {
    output.innerHTML =
      '<p class="empty">Nothing to read yet. Paste a function or a class.</p>';
    return;
  }

  const endpoint = mode === 'facts' ? '/parse' : '/generate';
  const body =
    mode === 'facts'
      ? { code }
      : {
          code,
          style: el('style').value,
          include_example: el('example').checked,
          skip_documented: el('skip').checked,
        };

  const key = cacheKey(endpoint, body);
  if (cache.has(key)) {
    render(cache.get(key));
    return;
  }

  runButton.disabled = true;
  status.textContent =
    mode === 'facts' ? 'Reading the signature…' : 'Writing docstrings…';

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();

    if (!response.ok) {
      renderError(data);
      return;
    }

    cache.set(key, data);
    render(data);
  } catch (error) {
    output.innerHTML =
      '<p class="error">The service did not answer. Is it running on this port?</p>';
  } finally {
    runButton.disabled = false;
    status.textContent = '';
  }
}

function render(data) {
  data.symbols ? renderFacts(data.symbols) : renderDocstrings(data.results);
}

function renderError(data) {
  const detail = data.detail;
  if (typeof detail === 'string') {
    output.innerHTML = `<p class="error">${escapeHtml(detail)}</p>`;
    return;
  }
  if (detail && detail.detail) {
    const where = detail.line
      ? ` (line ${detail.line}, column ${detail.offset ?? '?'})`
      : '';
    output.innerHTML = `<p class="error">${escapeHtml(detail.detail)}${where}</p>`;
    return;
  }
  output.innerHTML = `<p class="error">The request was rejected. Check the style and the code length.</p>`;
}

function renderDocstrings(results) {
  output.innerHTML = results
    .map(
      (result) => `
      <article class="result">
        <div class="result-head">
          <span class="symbol">${escapeHtml(result.symbol_name)}</span>
          <span class="badge">${escapeHtml(result.kind)}</span>
          ${result.degraded ? '<span class="badge degraded">from signature only</span>' : ''}
          <button type="button" class="quiet copy" data-docstring="${escapeHtml(result.docstring)}">Copy</button>
        </div>
        <pre>${escapeHtml(result.docstring)}</pre>
      </article>`,
    )
    .join('');

  output.querySelectorAll('.copy').forEach((button) => {
    button.addEventListener('click', async () => {
      await navigator.clipboard.writeText(button.dataset.docstring);
      button.textContent = 'Copied';
      setTimeout(() => (button.textContent = 'Copy'), 1200);
    });
  });
}

function renderFacts(symbols) {
  output.innerHTML = symbols
    .map(
      (symbol) => `
      <article class="result">
        <div class="result-head">
          <span class="symbol">${escapeHtml(symbol.qualified_name)}</span>
          <span class="badge">${escapeHtml(symbol.kind)}</span>
        </div>
        <dl class="facts">${(symbol.kind === 'class' ? classRows(symbol) : functionRows(symbol)).join('')}</dl>
      </article>`,
    )
    .join('');
}

const row = (term, value) =>
  value ? `<div><dt>${term}</dt><dd>${escapeHtml(value)}</dd></div>` : '';

function functionRows(fn) {
  const parameters = fn.parameters
    .map((p) => {
      const parts = [
        p.annotation,
        p.default ? `= ${p.default}` : null,
        p.kind,
      ].filter(Boolean);
      return `${p.name} — ${parts.join(', ')}`;
    })
    .join('\n');

  return [
    row('parameters', parameters || 'none'),
    row(
      'returns',
      fn.return_annotation || (fn.returns_value ? 'value, not annotated' : ''),
    ),
    row('generator', fn.is_generator ? 'yes' : ''),
    row('async', fn.is_async ? 'yes' : ''),
    row('raises', fn.raises.join(', ')),
    row('has docstring', fn.existing_docstring ? 'yes' : ''),
  ];
}

function classRows(cls) {
  const attributes = cls.attributes
    .map((a) =>
      [a.name, a.annotation, a.default ? `= ${a.default}` : null]
        .filter(Boolean)
        .join(' — '),
    )
    .join('\n');

  return [
    row('bases', cls.bases.join(', ')),
    row('attributes', attributes || 'none'),
    row('public methods', cls.method_names.join(', ')),
    row('has docstring', cls.existing_docstring ? 'yes' : ''),
  ];
}
