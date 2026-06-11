import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Trash2, Edit2, X } from 'lucide-react'
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

function VeiculoForm({ initial = {}, clientes, onSubmit, loading }) {
  const [form, setForm] = useState({
    cliente_id: '', placa: '', marca: '', modelo: '', ano: new Date().getFullYear(), cor: '', km_atual: 0, ...initial
  })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit({ ...form, ano: Number(form.ano), km_atual: Number(form.km_atual), cliente_id: Number(form.cliente_id) }) }} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="text-xs text-gray-400 mb-1 block">Cliente *</label>
          <select className="input" value={form.cliente_id} onChange={set('cliente_id')} required>
            <option value="">Selecionar...</option>
            {clientes.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Placa *</label>
          <input className="input uppercase" value={form.placa} onChange={set('placa')} placeholder="ABC1234" required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Cor</label>
          <input className="input" value={form.cor} onChange={set('cor')} />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Marca *</label>
          <input className="input" value={form.marca} onChange={set('marca')} required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Modelo *</label>
          <input className="input" value={form.modelo} onChange={set('modelo')} required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Ano *</label>
          <input className="input" type="number" value={form.ano} onChange={set('ano')} required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">KM Atual</label>
          <input className="input" type="number" value={form.km_atual} onChange={set('km_atual')} />
        </div>
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? 'Salvando...' : 'Salvar'}</button>
      </div>
    </form>
  )
}

export default function VeiculosPage() {
  const qc = useQueryClient()
  const [busca, setBusca] = useState('')
  const [modal, setModal] = useState(null)

  const { data: veiculos = [], isLoading } = useQuery({
    queryKey: ['veiculos', busca],
    queryFn: () => api.get('/veiculos', { params: { busca: busca || undefined, limit: 50 } }).then(r => r.data)
  })
  const { data: clientes = [] } = useQuery({
    queryKey: ['clientes-select'],
    queryFn: () => api.get('/clientes', { params: { limit: 200 } }).then(r => r.data)
  })

  const criar = useMutation({
    mutationFn: d => api.post('/veiculos', d),
    onSuccess: () => { toast.success('Veículo cadastrado!'); qc.invalidateQueries(['veiculos']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  const atualizar = useMutation({
    mutationFn: ({ id, ...d }) => api.put(`/veiculos/${id}`, d),
    onSuccess: () => { toast.success('Atualizado!'); qc.invalidateQueries(['veiculos']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  const deletar = useMutation({
    mutationFn: id => api.delete(`/veiculos/${id}`),
    onSuccess: () => { toast.success('Removido'); qc.invalidateQueries(['veiculos']) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Veículos</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => setModal('novo')}>
          <Plus size={16} /> Novo Veículo
        </button>
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input className="input pl-9" placeholder="Buscar por placa, marca ou modelo..." value={busca} onChange={e => setBusca(e.target.value)} />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-800">
            <tr className="text-gray-500 text-left">
              <th className="px-4 py-3 font-medium">Placa</th>
              <th className="px-4 py-3 font-medium">Veículo</th>
              <th className="px-4 py-3 font-medium">Ano</th>
              <th className="px-4 py-3 font-medium">KM</th>
              <th className="px-4 py-3 font-medium">Cliente</th>
              <th className="px-4 py-3 font-medium w-20"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="text-center py-10 text-gray-500">Carregando...</td></tr>
            ) : veiculos.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-10 text-gray-500">Nenhum veículo</td></tr>
            ) : veiculos.map(v => (
              <tr key={v.id} className="table-row">
                <td className="px-4 py-3 font-mono font-bold text-brand">{v.placa}</td>
                <td className="px-4 py-3 text-gray-200">{v.marca} {v.modelo} {v.cor && <span className="text-gray-500">· {v.cor}</span>}</td>
                <td className="px-4 py-3 text-gray-400">{v.ano}</td>
                <td className="px-4 py-3 text-gray-400">{v.km_atual.toLocaleString()} km</td>
                <td className="px-4 py-3 text-gray-400">{v.cliente.nome}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button className="btn-ghost p-1.5" onClick={() => setModal(v)}><Edit2 size={14} /></button>
                    <button className="btn-ghost p-1.5 text-red-400" onClick={() => { if (confirm('Remover?')) deletar.mutate(v.id) }}><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal === 'novo' && (
        <Modal title="Novo Veículo" onClose={() => setModal(null)}>
          <VeiculoForm clientes={clientes} onSubmit={d => criar.mutate(d)} loading={criar.isPending} />
        </Modal>
      )}
      {modal && modal !== 'novo' && (
        <Modal title="Editar Veículo" onClose={() => setModal(null)}>
          <VeiculoForm initial={modal} clientes={clientes} onSubmit={d => atualizar.mutate({ id: modal.id, ...d })} loading={atualizar.isPending} />
        </Modal>
      )}
    </div>
  )
}
