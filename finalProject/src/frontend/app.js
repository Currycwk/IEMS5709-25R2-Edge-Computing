const backendBase = window.location.origin.includes('9898') ? 'http://localhost:8001' : '';

const statusButton = document.getElementById('statusButton');
const statusText = document.getElementById('statusText');
const indexButton = document.getElementById('indexButton');
const askButton = document.getElementById('askButton');
const questionInput = document.getElementById('questionInput');
const answerOutput = document.getElementById('answerOutput');
const sourceList = document.getElementById('sourceList');

async function requestJson(path, options = {}) {
  const response = await fetch(`${backendBase}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Request failed');
  }
  return data;
}

function renderSources(sources) {
  if (!sources || !sources.length) {
    sourceList.innerHTML = '尚无检索结果。';
    return;
  }

  sourceList.innerHTML = sources
    .map((source) => `
      <article class="source-card">
        <h3>${source.source}</h3>
        <div class="meta">相似度分数：${source.score ?? 'n/a'}</div>
        <div>${source.content}</div>
      </article>
    `)
    .join('');
}

statusButton.addEventListener('click', async () => {
  statusText.textContent = '检查中...';
  try {
    const status = await requestJson('/api/status');
    statusText.textContent = `backend=${status.backend} | index=${status.index_ready} | qwen=${status.qwen_ready}`;
  } catch (error) {
    statusText.textContent = `状态检查失败：${error.message}`;
  }
});

indexButton.addEventListener('click', async () => {
  answerOutput.textContent = '正在构建索引...';
  try {
    const result = await requestJson('/api/index', { method: 'POST', body: '{}' });
    answerOutput.textContent = `索引构建完成。documents=${result.documents}, chunks=${result.chunks}`;
  } catch (error) {
    answerOutput.textContent = `索引构建失败：${error.message}`;
  }
});

askButton.addEventListener('click', async () => {
  const question = questionInput.value.trim();
  if (!question) {
    answerOutput.textContent = '请输入问题。';
    return;
  }
  answerOutput.textContent = '思考中...';
  sourceList.innerHTML = '正在检索...';
  try {
    const result = await requestJson('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
    answerOutput.textContent = result.answer;
    renderSources(result.sources);
  } catch (error) {
    answerOutput.textContent = `问答失败：${error.message}`;
    sourceList.innerHTML = '无可展示的来源。';
  }
});
