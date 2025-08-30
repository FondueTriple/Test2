export async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  })
  if (!res.ok) {
    let err
    try { err = await res.json() } catch { err = { error: res.statusText } }
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text()
}

export async function listBottles() {
  return api('/api/bottles')
}

export async function addBottle(data) {
  return api('/api/bottles', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateBottle(id, data) {
  return api(`/api/bottles/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export async function deleteBottle(id) {
  return api(`/api/bottles/${id}`, { method: 'DELETE' })
}

export async function addComment(id, text) {
  return api(`/api/bottles/${id}/comments`, { method: 'POST', body: JSON.stringify({ text }) })
}

export async function fetchRating(id) {
  return api(`/api/bottles/${id}/fetch-rating`, { method: 'POST' })
}

export async function fetchAllRatings() {
  return api('/api/bottles/fetch-all-ratings', { method: 'POST' })
}
