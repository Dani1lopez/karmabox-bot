const $ = (id) => document.getElementById(id);

const state = {
    leads: [],
    selectedId: null,
    q: "",
    sort: "created_desc",
    page: 1,
    pageSize: 20,
    loading: false,
};

const setDot = (mode) => {
    const dot = $("statusDot");
    dot.classList.remove("ok", "err");
    if (mode) dot.classList.add(mode);
};

const setLastSync = (text) => {
    $("lastSync").textContent = text;
};

const toast = (msg) => {
    const el = $("toast");
    $("toastText").textContent = msg;
    el.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => (el.hidden = true), 2200);
};

const escapeHtml = (s) =>
    (s ?? "").toString().replace(
        /[&<>"']/g,
        (c) =>
            ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;",
            })[c],
    );

const normalize = (v) => (v ?? "").toString().toLowerCase().trim();

const fmtDate = (iso) => {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return iso;
        return new Intl.DateTimeFormat("es-ES", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        }).format(d);
    } catch {
        return iso;
    }
};

const api = {
    async getLeads() {
        const res = await fetch("/leads", {
            headers: { Accept: "application/json" },
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) {
            const detail = data?.detail || `HTTP ${res.status}`;
            throw new Error(detail);
        }
        return data ?? [];
    },

    async patchLead(id, payload) {
        const res = await fetch(`/leads/${encodeURIComponent(id)}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) {
            const detail = data?.detail || `HTTP ${res.status}`;

            const msg =
                res.status === 409
                    ? `Duplicado: ${detail}`
                    : res.status === 422
                        ? `Validación: ${detail}`
                        : res.status === 404
                            ? `No encontrado: ${detail}`
                            : `Error: ${detail}`;

            const err = new Error(msg);
            err.status = res.status;
            throw err;
        }
        return data;
    },
};

const ui = {
    setLoading(on) {
        state.loading = on;
        $("loadingState").hidden = !on;
        if (on) $("emptyState").hidden = true;
    },

    setEmpty(on) {
        $("emptyState").hidden = !on;
    },

    clearDetail() {
        $("d_id").textContent = "—";
        $("d_created").textContent = "—";
        $("d_name").textContent = "—";
        $("d_last").textContent = "—";
        $("d_phone").textContent = "—";
        $("d_address").textContent = "—";
        $("btnCopyId").disabled = true;
        $("btnOpenEdit").disabled = true;
    },

    fillDetail(lead) {
        $("d_id").textContent = lead.id || "—";
        $("d_created").textContent = lead.created_at || "—";
        $("d_name").textContent = lead.name || "—";
        $("d_last").textContent = lead.last_name || "—";
        $("d_phone").textContent = lead.phone || "—";
        $("d_address").textContent = lead.address || "—";

        $("btnCopyId").disabled = !lead.id;
        $("btnOpenEdit").disabled = !lead.id;
    },

    render() {
        const q = normalize(state.q);
        let items = state.leads.slice();

        // filter
        if (q) {
            items = items.filter((l) =>
                [l.id, l.name, l.last_name, l.phone, l.address, l.created_at].some(
                    (x) => normalize(x).includes(q),
                ),
            );
        }

        // sort
        items.sort((a, b) => {
            const sa = state.sort;
            if (sa === "created_desc")
                return normalize(b.created_at).localeCompare(normalize(a.created_at));
            if (sa === "created_asc")
                return normalize(a.created_at).localeCompare(normalize(b.created_at));
            if (sa === "name_asc")
                return normalize(a.name).localeCompare(normalize(b.name));
            if (sa === "name_desc")
                return normalize(b.name).localeCompare(normalize(a.name));
            return 0;
        });

        $("totalCount").textContent = items.length;

        const totalPages = Math.max(1, Math.ceil(items.length / state.pageSize));
        state.page = Math.min(state.page, totalPages);

        $("pageNow").textContent = String(state.page);
        $("pageTotal").textContent = String(totalPages);

        const start = (state.page - 1) * state.pageSize;
        const pageItems = items.slice(start, start + state.pageSize);

        const rows = $("rows");
        rows.innerHTML = "";

        if (!pageItems.length) {
            ui.setEmpty(true);
            return;
        }

        ui.setEmpty(false);

        for (const l of pageItems) {
            const tr = document.createElement("tr");

            const leadLabel =
                `${escapeHtml(l.name || "")} ${escapeHtml(l.last_name || "")}`.trim() ||
                "—";
            const created = fmtDate(l.created_at);

            tr.innerHTML = `
        <td>
          <div class="pill">${leadLabel}</div>
          <div class="muted mono" style="margin-top:6px;">${escapeHtml((l.id || "").slice(0, 10))}…</div>
        </td>
        <td class="mono">${escapeHtml(l.phone || "—")}</td>
        <td>${escapeHtml(l.address || "—")}</td>
        <td class="mono">${escapeHtml(created)}</td>
        <td class="td-actions">
          <button class="btn btn-ghost" type="button" data-action="select" data-id="${escapeHtml(l.id)}">Ver</button>
          <button class="btn btn-primary" type="button" data-action="edit" data-id="${escapeHtml(l.id)}">Editar</button>
        </td>
      `;

            tr.addEventListener("click", (e) => {
                const btn = e.target.closest("button[data-action]");
                if (!btn) {
                    ui.select(l.id);
                    return;
                }
                e.preventDefault();
                e.stopPropagation();
                const id = btn.getAttribute("data-id");
                if (!id) return;

                ui.select(id);

                if (btn.getAttribute("data-action") === "edit") {
                    modal.open(id);
                }
            });

            rows.appendChild(tr);
        }
    },

    select(id) {
        state.selectedId = id;
        const lead = state.leads.find((x) => x.id === id);
        if (!lead) {
            ui.clearDetail();
            return;
        }
        ui.fillDetail(lead);
    },
};

const modal = {
    original: null,

    open(id) {
        const lead = state.leads.find((x) => x.id === id);
        if (!lead) return;

        this.original = { ...lead };

        $("m_id").textContent = lead.id;
        $("m_name").value = lead.name || "";
        $("m_last_name").value = lead.last_name || "";
        $("m_phone").value = lead.phone || "";
        $("m_address").value = lead.address || "";
        this.setMsg("");

        $("modalBackdrop").hidden = false;
        const dlg = $("modal");
        if (!dlg.open) dlg.showModal();
    },

    close() {
        $("modalBackdrop").hidden = true;
        const dlg = $("modal");
        if (dlg.open) dlg.close();
    },

    setMsg(text, type = "") {
        const el = $("m_msg");
        el.textContent = text || "";
        el.classList.remove("ok", "err");
        if (type) el.classList.add(type);
    },

    buildPatch() {
        if (!this.original) return null;

        const next = {
            name: $("m_name").value.trim(),
            last_name: $("m_last_name").value.trim(),
            phone: $("m_phone").value.trim(),
            address: $("m_address").value.trim(),
        };

        // Solo cambios reales, y no enviamos vacíos (evita borrar)
        const patch = {};
        for (const k of Object.keys(next)) {
            const prev = (this.original[k] ?? "").toString().trim();
            const cur = (next[k] ?? "").toString().trim();
            if (!cur) continue;
            if (cur !== prev) patch[k] = cur;
        }

        return patch;
    },

    reset() {
        if (!this.original) return;
        $("m_name").value = this.original.name || "";
        $("m_last_name").value = this.original.last_name || "";
        $("m_phone").value = this.original.phone || "";
        $("m_address").value = this.original.address || "";
        this.setMsg("Revertido.", "ok");
        setTimeout(() => this.setMsg(""), 1200);
    },
};

async function load() {
    ui.setLoading(true);
    setDot("");
    setLastSync("Cargando…");

    try {
        const leads = await api.getLeads();
        state.leads = Array.isArray(leads) ? leads : [];
        setDot("ok");
        setLastSync("Actualizado: " + new Date().toLocaleTimeString("es-ES"));
        toast("Leads cargados ✅");
    } catch (e) {
        setDot("err");
        setLastSync("Error al cargar");
        toast("Error cargando leads");
        console.error(e);
    } finally {
        ui.setLoading(false);
        ui.render();

        // refresca detalle si ya había seleccionado
        if (state.selectedId) ui.select(state.selectedId);
        else ui.clearDetail();
    }
}

async function saveEdit() {
    const id = $("m_id").textContent.trim();
    if (!id) return;

    const patch = modal.buildPatch();
    if (!patch || Object.keys(patch).length === 0) {
        modal.setMsg("No hay cambios para guardar.", "err");
        return;
    }

    $("btnSave").disabled = true;
    modal.setMsg("Guardando…");

    try {
        await api.patchLead(id, patch);
        modal.setMsg("Guardado OK ✅", "ok");
        toast("Guardado ✅");
        await load();
        ui.select(id);
        setTimeout(() => modal.close(), 450);
    } catch (e) {
        const msg = e?.message || "Error guardando";
        modal.setMsg(msg, "err");
        toast("Error: " + msg);
    } finally {
        $("btnSave").disabled = false;
    }
}

function wire() {
    $("btnRefresh").addEventListener("click", load);

    $("q").addEventListener("input", (e) => {
        state.q = e.target.value;
        state.page = 1;
        ui.render();
    });

    $("sort").addEventListener("change", (e) => {
        state.sort = e.target.value;
        state.page = 1;
        ui.render();
    });

    $("pageSize").addEventListener("change", (e) => {
        state.pageSize = parseInt(e.target.value, 10) || 20;
        state.page = 1;
        ui.render();
    });

    $("prevPage").addEventListener("click", () => {
        state.page = Math.max(1, state.page - 1);
        ui.render();
    });

    $("nextPage").addEventListener("click", () => {
        const total = Math.max(
            1,
            Math.ceil((state.leads.length || 0) / state.pageSize),
        );
        state.page = Math.min(total, state.page + 1);
        ui.render();
    });

    $("btnCopyId").addEventListener("click", async () => {
        const id = $("d_id").textContent.trim();
        if (!id || id === "—") return;
        try {
            await navigator.clipboard.writeText(id);
            toast("ID copiado");
        } catch {
            toast("No se pudo copiar");
        }
    });

    $("btnOpenEdit").addEventListener("click", () => {
        if (!state.selectedId) return;
        modal.open(state.selectedId);
    });

    $("btnClose").addEventListener("click", modal.close.bind(modal));
    $("btnCancel").addEventListener("click", modal.close.bind(modal));
    $("btnReset").addEventListener("click", modal.reset.bind(modal));

    $("modalBackdrop").addEventListener("click", modal.close.bind(modal));

    $("editForm").addEventListener("submit", (e) => {
        e.preventDefault();
        saveEdit();
    });

    // ESC closes nicely
    $("modal").addEventListener("cancel", (e) => {
        e.preventDefault();
        modal.close();
    });
}

wire();
load();
