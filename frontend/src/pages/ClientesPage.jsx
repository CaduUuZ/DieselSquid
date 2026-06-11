import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Trash2, Edit2, X, Car } from 'lucide-react'
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

function ClienteForm({ initial = {}, onSubmit, loading }) {
  const [form, setForm] = useState({ nome: '', cpf: '', telefone: '', email: '', endereco: '', ...initial })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit(form) }} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="text-xs text-gray-400 mb-1 block">Nome *</label>
          <input className="input" value={form.nome} onChange={set('nome')} required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">CPF *</label>
          <input className="input" value={form.cpf} onChange={set('cpf')} placeholder="12345678901" required />
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Telefone</label>
          <input className="input" value={form.telefone} onChange={set('telefone')} />
        </div>
        <div className="col-span-2">
          <label className="text-xs text-gray-400 mb-1 block">E-mail</label>
          <input className="input" type="email" value={form.email} onChange={set('email')} />
        </div>
        <div className="col-span-2">
          <label className="text-xs text-gray-400 mb-1 block">Endereço</label>
          <input className="input" value={form.endereco} onChange={set('endereco')} />
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </form>
  )
}

export default function ClientesPage() {
  const qc = useQueryClient()
  const [busca, setBusca] = useState('')
  const [modal, setModal] = useState(null) // null | 'novo' | cliente

  const { data: clientes = [], isLoading } = useQuery({
    queryKey: ['clientes', busca],
    queryFn: () => api.get('/clientes', { params: { busca: busca || undefined, limit: 50 } }).then(r => r.data)
  })

  const criar = useMutation({
    mutationFn: d => api.post('/clientes', d),
    onSuccess: () => { toast.success('Cliente criado!'); qc.invalidateQueries(['clientes']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro ao criar')
  })

  const atualizar = useMutation({
    mutationFn: ({ id, ...d }) => api.put(`/clientes/${id}`, d),
    onSuccess: () => { toast.success('Cliente atualizado!'); qc.invalidateQueries(['clientes']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro ao atualizar')
  })

  const deletar = useMutation({
    mutationFn: id => api.delete(`/clientes/${id}`),
    onSuccess: () => { toast.success('Cliente removido'); qc.invalidateQueries(['clientes']) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro ao deletar')
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Clientes</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => setModal('novo')}>
          <Plus size={16} /> Novo Cliente
        </button>
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input className="input pl-9" placeholder="Buscar por nome ou CPF..." value={busca} onChange={e => setBusca(e.target.value)} />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-800">
            <tr className="text-gray-500 text-left">
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">CPF</th>
              <th className="px-4 py-3 font-medium">Telefone</th>
              <th className="px-4 py-3 font-medium">E-mail</th>
              <th className="px-4 py-3 font-medium w-24"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="text-center py-10 text-gray-500">Carregando...</td></tr>
            ) : clientes.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-10 text-gray-500">Nenhum cliente encontrado</td></tr>
            ) : clientes.map(c => (
              <tr key={c.id} className="table-row">
                <td className="px-4 py-3 font-medium text-gray-200">{c.nome}</td>
                <td className="px-4 py-3 text-gray-400 font-mono text-xs">{c.cpf}</td>
                <td className="px-4 py-3 text-gray-400">{c.telefone ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400">{c.email ?? '—'}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button className="btn-ghost p-1.5" onClick={() => setModal(c)} title="Editar"><Edit2 size={14} /></button>
                    <button className="btn-ghost p-1.5 text-red-400 hover:text-red-300" onClick={() => { if (confirm('Remover cliente?')) deletar.mutate(c.id) }}><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal === 'novo' && (
        <Modal title="Novo Cliente" onClose={() => setModal(null)}>
          <ClienteForm onSubmit={d => criar.mutate(d)} loading={criar.isPending} />
        </Modal>
      )}
      {modal && modal !== 'novo' && (
        <Modal title="Editar Cliente" onClose={() => setModal(null)}>
          <ClienteForm initial={modal} onSubmit={d => atualizar.mutate({ id: modal.id, ...d })} loading={atualizar.isPending} />
        </Modal>
      )}
    </div>
  )
}
