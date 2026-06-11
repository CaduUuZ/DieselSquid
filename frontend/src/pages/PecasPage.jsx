import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Trash2, Edit2, X, TrendingDown, TrendingUp } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-lg">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="btn-ghost p-1"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

function PecaForm({ initial = {}, onSubmit, loading }) {
  const [form, setForm] = useState({ codigo: '', nome: '', marca: '', unidade: 'un', preco_custo: 0, preco_venda: 0, estoque_atual: 0, estoque_minimo: 1, ...initial })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit({ ...form, preco_custo: Number(form.preco_custo), preco_venda: Number(form.preco_venda), estoque_atual: Number(form.estoque_atual), estoque_minimo: Number(form.estoque_minimo) }) }} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div><label className="text-xs text-gray-400 mb-1 block">Código *</label><input className="input" value={form.codigo} onChange={set('codigo')} required /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Unidade</label>
          <select className="input" value={form.unidade} onChange={set('unidade')}>
            {['un','litro','kg','metro','par','jogo'].map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>
        <div className="col-span-2"><label className="text-xs text-gray-400 mb-1 block">Nome *</label><input className="input" value={form.nome} onChange={set('nome')} required /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Marca</label><input className="input" value={form.marca} onChange={set('marca')} /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Preço Custo (R$)</label><input className="input" type="number" step="0.01" value={form.preco_custo} onChange={set('preco_custo')} /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Preço Venda (R$) *</label><input className="input" type="number" step="0.01" value={form.preco_venda} onChange={set('preco_venda')} required /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Estoque Atual</label><input className="input" type="number" value={form.estoque_atual} onChange={set('estoque_atual')} /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Estoque Mínimo</label><input className="input" type="number" value={form.estoque_minimo} onChange={set('estoque_minimo')} /></div>
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </form>
  )
}

function AjusteForm({ peca, onClose }) {
  const qc = useQueryClient()
  const [qtd, setQtd] = useState(0)
  const ajuste = useMutation({
    mutationFn: d => api.patch(`/pecas/${peca.id}/estoque`, d),
    onSuccess: () => { toast.success('Estoque ajustado!'); qc.invalidateQueries(['pecas']); onClose() },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  return (
    <form onSubmit={e => { e.preventDefault(); ajuste.mutate({ quantidade: Number(qtd) }) }} className="space-y-4">
      <p className="text-sm text-gray-400">Estoque atual: <span className="text-white font-semibold">{peca.estoque_atual} {peca.unidade}</span></p>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">Quantidade (+ entrada / − saída)</label>
        <input className="input" type="number" value={qtd} onChange={e => setQtd(e.target.value)} required />
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={ajuste.isPending}>Confirmar</button>
      </div>
    </form>
  )
}

export default function PecasPage() {
  const qc = useQueryClient()
  const [busca, setBusca] = useState('')
  const [modal, setModal] = useState(null)
  const [ajustePeca, setAjustePeca] = useState(null)

  const { data: pecas = [], isLoading } = useQuery({
    queryKey: ['pecas', busca],
    queryFn: () => api.get('/pecas', { params: { busca: busca || undefined, limit: 50 } }).then(r => r.data)
  })

  const criar = useMutation({
    mutationFn: d => api.post('/pecas', d),
    onSuccess: () => { toast.success('Peça criada!'); qc.invalidateQueries(['pecas']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  const atualizar = useMutation({
    mutationFn: ({ id, ...d }) => api.put(`/pecas/${id}`, d),
    onSuccess: () => { toast.success('Atualizado!'); qc.invalidateQueries(['pecas']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  const deletar = useMutation({
    mutationFn: id => api.delete(`/pecas/${id}`),
    onSuccess: () => { toast.success('Removida'); qc.invalidateQueries(['pecas']) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Peças</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => setModal('novo')}><Plus size={16} /> Nova Peça</button>
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input className="input pl-9" placeholder="Buscar por código, nome ou marca..." value={busca} onChange={e => setBusca(e.target.value)} />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-800">
            <tr className="text-gray-500 text-left">
              <th className="px-4 py-3 font-medium">Código</th>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Marca</th>
              <th className="px-4 py-3 font-medium text-right">Custo</th>
              <th className="px-4 py-3 font-medium text-right">Venda</th>
              <th className="px-4 py-3 font-medium text-right">Estoque</th>
              <th className="px-4 py-3 font-medium w-28"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7} className="text-center py-10 text-gray-500">Carregando...</td></tr>
            ) : pecas.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-10 text-gray-500">Nenhuma peça</td></tr>
            ) : pecas.map(p => (
              <tr key={p.id} className="table-row">
                <td className="px-4 py-3 font-mono text-xs text-brand">{p.codigo}</td>
                <td className="px-4 py-3 text-gray-200">{p.nome}</td>
                <td className="px-4 py-3 text-gray-400">{p.marca ?? '—'}</td>
                <td className="px-4 py-3 text-right text-gray-400">R$ {Number(p.preco_custo).toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-gray-200 font-medium">R$ {Number(p.preco_venda).toFixed(2)}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`font-bold ${p.estoque_baixo ? 'text-red-400' : 'text-green-400'}`}>
                    {p.estoque_atual}
                  </span>
                  <span className="text-gray-600 text-xs ml-1">{p.unidade}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1 justify-end">
                    <button className="btn-ghost p-1.5 text-green-400" title="Ajustar estoque" onClick={() => setAjustePeca(p)}><TrendingUp size={14} /></button>
                    <button className="btn-ghost p-1.5" onClick={() => setModal(p)}><Edit2 size={14} /></button>
                    <button className="btn-ghost p-1.5 text-red-400" onClick={() => { if (confirm('Remover peça?')) deletar.mutate(p.id) }}><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal === 'novo' && <Modal title="Nova Peça" onClose={() => setModal(null)}><PecaForm onSubmit={d => criar.mutate(d)} loading={criar.isPending} /></Modal>}
      {modal && modal !== 'novo' && <Modal title="Editar Peça" onClose={() => setModal(null)}><PecaForm initial={modal} onSubmit={d => atualizar.mutate({ id: modal.id, ...d })} loading={atualizar.isPending} /></Modal>}
      {ajustePeca && <Modal title={`Ajustar Estoque — ${ajustePeca.nome}`} onClose={() => setAjustePeca(null)}><AjusteForm peca={ajustePeca} onClose={() => setAjustePeca(null)} /></Modal>}
    </div>
  )
}
