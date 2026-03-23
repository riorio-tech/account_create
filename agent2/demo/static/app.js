const $ = (id) => document.getElementById(id);

let lastStatus = null;

async function fetchJson(url, opts) {
  const r = await fetch(url, opts);
  const ct = r.headers.get("content-type") || "";
  const body = ct.includes("application/json") ? await r.json() : await r.text();
  if (!r.ok) {
    const msg = typeof body === "object" && body?.detail ? String(body.detail) : String(body);
    throw new Error(msg || r.statusText);
  }
  return body;
}

function hideAlert() {
  const el = $("alert-error");
  el.hidden = true;
  el.textContent = "";
}

function showError(title, detail) {
  const el = $("alert-error");
  el.hidden = false;
  el.replaceChildren();
  const s = document.createElement("strong");
  s.textContent = title;
  el.appendChild(s);
  if (detail) {
    el.appendChild(document.createElement("br"));
    el.appendChild(document.createTextNode(detail));
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setHeaderPill(serverOk) {
  const pill = $("header-pill");
  pill.classList.remove("ok", "bad", "warn");
  if (!serverOk) {
    pill.classList.add("bad");
    pill.textContent = "サーバーに接続できません";
    return;
  }
  pill.classList.add("ok");
  pill.textContent = "接続OK";
}

function applyStatusMeta(data) {
  lastStatus = data;
  const n = data.input_product_count;
  $("run-note").textContent =
    n != null ? `入力ファイルは ${n} 件です。完了まで数分かかることがあります。` : "";
}

function updateResultSummary(statusData, briefCount) {
  const el = $("result-summary");
  el.classList.remove("ok");
  if (briefCount != null && briefCount > 0) {
    const n = statusData?.input_product_count;
    el.classList.add("ok");
    el.textContent =
      n != null
        ? `完了：${briefCount} / ${n} 件の設計書を表示しています。`
        : `完了：${briefCount} 件の設計書を表示しています。`;
    return;
  }
  if (statusData?.content_brief_exists) {
    el.textContent = "保存済みの結果を読み込みました。下に表示します。";
    return;
  }
  el.textContent = "まだ結果がありません。実行するとここに表示されます。";
}

async function refreshStatus() {
  try {
    const data = await fetchJson("/api/status");
    setHeaderPill(true);
    applyStatusMeta(data);
    return data;
  } catch {
    setHeaderPill(false);
    $("run-note").textContent = "デモサーバーを起動してください（詳細にコマンドあり）。";
    throw new Error("status failed");
  }
}

function renderPreview(data) {
  const root = $("input-preview");
  if (!data.preview?.length) {
    root.textContent = "データがありません";
    return;
  }
  const table = document.createElement("table");
  table.className = "preview-table";
  table.innerHTML =
    "<thead><tr><th>ID</th><th>商品名</th><th>カテゴリ</th><th>スコア</th></tr></thead><tbody></tbody>";
  const tb = table.querySelector("tbody");
  for (const row of data.preview) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${escapeHtml(String(row.product_id))}</td><td>${escapeHtml(
      String(row.product_name)
    )}</td><td>${escapeHtml(String(row.category))}</td><td>${escapeHtml(
      String(row.total_score ?? "")
    )}</td>`;
    tb.appendChild(tr);
  }
  root.innerHTML = "";
  const cap = document.createElement("div");
  cap.className = "muted small";
  cap.style.marginBottom = "0.5rem";
  cap.textContent = `全 ${data.count} 件（先頭 ${data.preview.length} 件表示） · ${data.path}`;
  root.appendChild(cap);
  root.appendChild(table);
}

function renderBriefs(list) {
  const root = $("briefs-root");
  root.innerHTML = "";
  if (!Array.isArray(list) || list.length === 0) {
    root.innerHTML =
      '<p class="empty">設計書が 0 件です。ログ（詳細）を確認してください。</p>';
    updateResultSummary(lastStatus, 0);
    return;
  }
  for (const b of list) {
    const ad = b.account_design || {};
    const mf = b.market_facts || {};
    const acc = b.tiktok_account_design || {};
    const ch = b.character_design || {};
    const pr = b.profile_proposal || {};
    const vo = b.voice_for_sales || {};
    const src = b.input_source === "natural_language" ? "自然言語" : "エージェント①";
    const el = document.createElement("article");
    el.className = "brief";
    el.innerHTML = `
      <div class="brief-head">
        <div class="brief-title">${escapeHtml(String(b.product_name || ""))}</div>
        <div class="brief-meta">${escapeHtml(String(b.product_id || ""))} · ${escapeHtml(src)} · スコア ${escapeHtml(
      String(b.total_score ?? "")
    )}</div>
      </div>
      <div class="brief-body">
        <div class="brief-meta">クリエイタータイプ: ${escapeHtml(String(ad.creator_type || "—"))} · CVR ${escapeHtml(
      String(ad.cvr_expectation || "—")
    )}</div>
        <div class="brief-block"><h4>市場ファクト（仮説）</h4><p class="brief-meta">${escapeHtml(
          String(mf.summary || "—")
        )}</p></div>
        <div class="brief-block"><h4>アカウント設計</h4><p class="brief-meta">${escapeHtml(
          String(acc.positioning || "—")
        )}</p><p class="brief-meta">${escapeHtml(String(acc.value_proposition || ""))}</p></div>
        <div class="brief-block"><h4>キャラクター</h4><p class="brief-meta">${escapeHtml(
          String(ch.persona_label || "—")
        )} — ${escapeHtml((ch.personality || []).join("・"))}</p></div>
        <div class="brief-block"><h4>プロフィール文案</h4><div class="bio-preview">${escapeHtml(
          String(pr.bio_text || "—")
        )}</div></div>
        <div class="brief-block"><h4>画像の提案</h4><p class="brief-meta"><strong>アイコン</strong> ${escapeHtml(
          String(pr.icon_image_brief || "—")
        )}</p><p class="brief-meta"><strong>ヘッダー</strong> ${escapeHtml(
      String(pr.header_image_brief || "—")
    )}</p></div>
        <div class="brief-block"><h4>売れる「声」</h4><p class="brief-meta">${escapeHtml(
          String(vo.voice_summary || "—")
        )}</p><p class="brief-meta">${escapeHtml(String(vo.why_converts || ""))}</p></div>
        <details><summary>全フィールド（JSON）</summary><pre>${escapeHtml(
          JSON.stringify(b, null, 2)
        )}</pre></details>
      </div>
    `;
    root.appendChild(el);
  }
  updateResultSummary(lastStatus, list.length);
}

async function loadBriefs() {
  try {
    const data = await fetchJson("/api/briefs");
    renderBriefs(data);
  } catch {
    $("briefs-root").innerHTML = "";
    if (lastStatus?.content_brief_exists) {
      $("result-summary").classList.remove("ok");
      $("result-summary").textContent =
        "結果ファイルはありますが読み込めませんでした。詳細のログを確認してください。";
    } else {
      updateResultSummary(lastStatus, null);
    }
  }
}

$("btn-preview").addEventListener("click", async () => {
  const btn = $("btn-preview");
  btn.disabled = true;
  $("input-preview").textContent = "読み込み中…";
  try {
    const data = await fetchJson("/api/input-preview");
    renderPreview(data);
  } catch (e) {
    $("input-preview").textContent = String(e.message || e);
  } finally {
    btn.disabled = false;
  }
});

$("btn-refresh-briefs").addEventListener("click", async () => {
  hideAlert();
  try {
    await refreshStatus();
  } catch {
    /* header already shows error */
  }
  await loadBriefs();
});

$("btn-run").addEventListener("click", async () => {
  const btn = $("btn-run");
  const note = $("run-note");
  const logsWrap = $("logs-wrap");
  const logs = $("run-logs");
  hideAlert();
  btn.disabled = true;
  const prevNote = note.textContent;
  note.textContent = "実行中です。しばらくお待ちください…";
  logsWrap.hidden = true;
  const modeEl = document.querySelector('input[name="input-mode"]:checked');
  const mode = modeEl ? modeEl.value : "agent1";
  const nl = ($("nl-input") && $("nl-input").value) ? $("nl-input").value.trim() : "";
  if (mode === "natural_language" && !nl) {
    showError("自然言語モード", "テキストエリアに商品のイメージを入力してください。");
    note.textContent = "";
    btn.disabled = false;
    return;
  }
  const runBody =
    mode === "natural_language"
      ? { mode: "natural_language", natural_language: nl }
      : { mode: "agent1" };

  try {
    const res = await fetchJson("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(runBody),
    });
    const out = [res.stdout, res.stderr].filter(Boolean).join("\n---\n");
    logs.textContent = out || "(ログなし)";
    logsWrap.hidden = false;

    if (!res.ok) {
      const tail = (res.stderr || res.stdout || "").trim().slice(-2000);
      showError(
        "実行は終了しましたが、エラーで止まった可能性があります。",
        `\n終了コード: ${res.exit_code}\n\n${tail || "詳細は下の「実行ログ」を開いてください。"}`
      );
      note.textContent = "エラーが出た可能性があります。上の赤い枠とログを確認してください。";
    } else {
      note.textContent = "完了しました。下に結果が表示されます。";
    }
    try {
      await refreshStatus();
    } catch {
      note.textContent = prevNote || note.textContent;
    }
    await loadBriefs();
  } catch (e) {
    showError("実行できませんでした", "\n" + String(e.message || e));
    note.textContent = "エラー内容を上に表示しました。";
    logsWrap.hidden = false;
    logs.textContent = String(e.message || e);
  } finally {
    btn.disabled = false;
  }
});

refreshStatus()
  .then(loadBriefs)
  .catch(() => {});
