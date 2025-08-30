import { useEffect, useMemo, useState } from 'react'
import { addBottle, addComment, deleteBottle, listBottles, updateBottle, fetchRating, fetchAllRatings } from './api'

function Stars({ rating = 0 }) {
  const pct = Math.max(0, Math.min(5, Number(rating) || 0)) / 5 * 100
  const cls = `w-${Math.round(pct/10)*10}`
  return (
    <span className="stars" aria-label={`Note Vivino: ${Number(rating).toFixed(1)}/5`}>
      <span className="base">★★★★★</span>
      <span className={`fill ${cls}`}>★★★★★</span>
    </span>
  )
}

function BottleRow({ b, onChange, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ name: b.name, year: b.year, color: b.color || 'white', vivino_rating: b.vivino_rating || 0, pos_row: b.pos_row || '', pos_col: b.pos_col || '' })
  const [comment, setComment] = useState('')

  useEffect(() => {
    setForm({ name: b.name, year: b.year, color: b.color || 'white', vivino_rating: b.vivino_rating || 0, pos_row: b.pos_row || '', pos_col: b.pos_col || '' })
  }, [b])

  async function save() {
    await onChange(b.id, {
      name: form.name,
      year: Number(form.year),
      color: form.color,
      vivino_rating: Number(form.vivino_rating),
      pos_row: form.pos_row === '' ? null : Number(form.pos_row),
      pos_col: form.pos_col === '' ? null : Number(form.pos_col),
    })
    setEditing(false)
  }

  async function addCmt() {
    if (!comment.trim()) return
    await onChange(b.id, await addComment(b.id, comment.trim()))
    setComment('')
  }

  return (
    <tr>
      <td>{b.id}</td>
      <td className="cell-name">
        <strong>{b.name}</strong>
        <br/>
        {b.vivino_url ? <a className="muted" href={b.vivino_url} target="_blank" rel="noopener">Vivino</a> : null}
      </td>
      <td>{b.year}</td>
      <td><Stars rating={b.vivino_rating} /> <span className="muted">{b.vivino_rating ? Number(b.vivino_rating).toFixed(1) : ''}</span></td>
      <td>
        {b.comments && b.comments.length ? b.comments.map((c, i) => (
          <div key={i} className="muted">• {c}</div>
        )) : <span className="muted">(aucun)</span>}
        <div className="row" style={{ display: 'flex', gap: '.5rem', alignItems: 'center' }}>
          <input type="text" placeholder="Ajouter un commentaire" value={comment} onChange={e => setComment(e.target.value)} />
          <button className="btn" onClick={addCmt}>Ajouter</button>
        </div>
      </td>
      <td className="actions">
        {editing ? (
          <div style={{ display: 'grid', gap: '.35rem' }}>
            <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            <input type="number" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} />
            <select value={form.color} onChange={e => setForm({ ...form, color: e.target.value })}>
              <option value="white">Blanc</option>
              <option value="red">Rouge</option>
            </select>
            <label style={{ color: 'var(--muted)' }}>Note Vivino (0-5)</label>
            <input type="number" step="0.1" min="0" max="5" value={form.vivino_rating} onChange={e => setForm({ ...form, vivino_rating: e.target.value })} />
            <div style={{ display: 'flex', gap: '.5rem' }}>
              <select value={form.pos_col} onChange={e => setForm({ ...form, pos_col: e.target.value })}>
                <option value="">Colonne (vide)</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
              </select>
              <select value={form.pos_row} onChange={e => setForm({ ...form, pos_row: e.target.value })}>
                <option value="">Ligne (vide)</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '.5rem' }}>
              <button className="btn" onClick={save}>Enregistrer</button>
              <button className="btn" onClick={() => setEditing(false)}>Annuler</button>
              <button className="btn" onClick={async () => { await onChange(b.id, { pos_row: null, pos_col: null }); }}>Retirer du casier</button>
            </div>
          </div>
        ) : (
          <>
            <button className="btn" onClick={() => setEditing(true)}>Éditer</button>
            <button className="btn danger" onClick={() => onDelete(b.id)}>Supprimer</button>
            <button className="btn" onClick={async () => { try { const nb = await fetchRating(b.id); await onChange(b.id, nb) } catch (e) { alert(String(e.message||e)) }}}>⟳ Note auto</button>
          </>
        )}
      </td>
    </tr>
  )
}

export default function App() {
  const [bottles, setBottles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newB, setNewB] = useState({ name: '', year: new Date().getFullYear(), color: 'white' })
  const [selectedToPlace, setSelectedToPlace] = useState('')
  const [sort, setSort] = useState({ col: 'year', dir: 'asc' })

  useEffect(() => {
    let cancel = false
    async function run() {
      try {
        const data = await listBottles()
        if (!cancel) setBottles(data)
      } catch (e) {
        setError(String(e.message || e))
      } finally {
        if (!cancel) setLoading(false)
      }
    }
    run()
    return () => { cancel = true }
  }, [])

  const sorted = useMemo(() => {
    const { col, dir } = sort
    const s = [...bottles].sort((a, b) => {
      const av = col === 'name' ? String(a[col]).toLowerCase() : a[col]
      const bv = col === 'name' ? String(b[col]).toLowerCase() : b[col]
      if (av < bv) return -1
      if (av > bv) return 1
      return 0
    })
    if (dir === 'desc') s.reverse()
    return s
  }, [bottles, sort])

  function toggleSort(col) {
    setSort(s => ({ col, dir: s.col === col && s.dir === 'asc' ? 'desc' : 'asc' }))
  }

  async function refresh() {
    const data = await listBottles()
    setBottles(data)
  }

  async function onAdd() {
    setError('')
    try {
      await addBottle({ name: newB.name.trim(), year: Number(newB.year), color: newB.color })
      setNewB({ name: '', year: new Date().getFullYear(), color: 'white' })
      await refresh()
    } catch (e) { setError(String(e.message || e)) }
  }

  async function onChange(id, dataOrBottle) {
    // dataOrBottle can be the whole updated bottle (from addComment) or a patch object
    try {
      if (dataOrBottle && dataOrBottle.id) {
        setBottles(bs => bs.map(b => b.id === id ? dataOrBottle : b))
      } else {
        await updateBottle(id, dataOrBottle)
        await refresh()
      }
    } catch (e) { setError(String(e.message || e)) }
  }

  async function onDelete(id) {
    if (!confirm('Supprimer cette bouteille ?')) return
    try {
      await deleteBottle(id)
      setBottles(bs => bs.filter(b => b.id !== id))
    } catch (e) { setError(String(e.message || e)) }
  }

  function Rack({ bottles }) {
    const occ = useMemo(() => {
      const m = new Map()
      for (const b of bottles) {
        if (b.pos_row && b.pos_col) {
          m.set(`${b.pos_row},${b.pos_col}`, b)
        }
      }
      return m
    }, [bottles])

    async function handleClick(r, c) {
      const key = `${r},${c}`
      const current = occ.get(key)
      if (!selectedToPlace) {
        // If nothing selected and cell occupied, select that bottle for moving
        if (current) {
          setSelectedToPlace(String(current.id))
        }
        return
      }
      // Place/move the selected bottle into this cell
      await onChange(Number(selectedToPlace), { pos_row: r, pos_col: c })
      await refresh()
    }

    const cells = []
    for (let r = 1; r <= 6; r++) {
      for (let c = 1; c <= 4; c++) {
        const key = `${r},${c}`
        const b = occ.get(key)
        const cls = `slot${b ? ' occ' : ''}${b && b.color === 'red' ? ' red' : ''}`
        const title = b ? `${b.name} [${b.id}]` : `${r},${c}`
        cells.push(
          <div key={key} className={cls} title={title} onClick={() => handleClick(r, c)}>
            {b ? <span className="dot">●</span> : null}
            <span className="mini">{r},{c}</span>
          </div>
        )
      }
    }
    return (
      <div className="rack-wrap">
        <div className="rack-title">Cave (4 × 6) — survolez pour voir le nom, cliquez pour placer</div>
        <div className="rack-controls">
          <label>Bouteille à placer&nbsp;
            <select value={selectedToPlace} onChange={e => setSelectedToPlace(e.target.value)}>
              <option value="">(Sélectionner...)</option>
              {bottles.map(b => (
                <option key={b.id} value={b.id}>[{b.id}] {b.name} ({b.year})</option>
              ))}
            </select>
          </label>
        </div>
        <div className="rack">{cells}</div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="fr-banner"></div>
      <h1>Cave à vins</h1>
      <p className="subnav"><a className="active" href="#">Liste des bouteilles</a></p>

      {error ? <p className="muted">Erreur: {error}</p> : null}
      {loading ? <p>Chargement…</p> : (
        <>
          <div className="row" style={{ display: 'flex', gap: '.5rem' }}>
            <button className="btn" onClick={refresh}>Actualiser</button>
            <button className="btn" onClick={async () => { try { const r = await fetchAllRatings(); alert(`Notes mises à jour: ${r.updated} succès, ${r.failed} échecs`) ; await refresh() } catch (e) { alert(String(e.message||e)) } }}>⟳ Mettre à jour toutes les notes</button>
          </div>

          <Rack bottles={bottles} />
          <table>
            <thead>
              <tr>
                <th><a onClick={() => toggleSort('id')}>ID</a></th>
                <th><a onClick={() => toggleSort('name')}>Nom</a></th>
                <th><a onClick={() => toggleSort('year')}>Millésime</a></th>
                <th>Note</th>
                <th>Commentaires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sorted.length ? sorted.map(b => (
                <BottleRow key={b.id} b={b} onChange={onChange} onDelete={onDelete} />
              )) : (
                <tr><td className="muted" colSpan={6}>Aucune bouteille</td></tr>
              )}
            </tbody>
          </table>

          <h2>Ajouter une bouteille</h2>
          <div className="grid">
            <label>Nom<br/><input type="text" value={newB.name} onChange={e => setNewB({ ...newB, name: e.target.value })} /></label>
            <label>Couleur<br/>
              <select value={newB.color} onChange={e => setNewB({ ...newB, color: e.target.value })}>
                <option value="white">Blanc</option>
                <option value="red">Rouge</option>
              </select>
            </label>
            <label>Millésime<br/><input type="number" min="1900" max="2100" value={newB.year} onChange={e => setNewB({ ...newB, year: e.target.value })} /></label>
            <div className="row"><button className="btn" onClick={onAdd}>Ajouter</button></div>
          </div>
        </>
      )}
    </div>
  )
}
