import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, X, ChevronRight, Package } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

const STATUS_LABEL = { aberta:'Aberta', em_andamento:'Em andamento', aguardando_pecas:'Aguard. peças', concluida:'Concluída', cancelada:'Cancelada' }
const STATUS_COLOR = { aberta:'bg-blue-500/20 text-blue-400', em_andamento:'bg-orange-500/20 text-orange-400', aguardando_pecas:'bg-yellow-500/20 text-yellow-400', concluida:'bg-green-500/20 text-green-400', cancelada:'bg-gray-500/20 text-gray-400' }
const PROXIMOS_STATUS = { aberta:['em_andamento','cancelada'], em_andamento:['aguardando_pecas','concluida','cancelada'], aguardando_pecas:['em_andamento','cancelada'] }

function Modal({ title, onClose, children, wide }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className={`card w-full ${wide ? 'max-w-3xl' : 'max-w-lg'}`}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="btn-ghost p-1"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

function NovaOSForm({ veiculos, onSubmit, loading }) {
  const [form, setForm] = useState({ veiculo_id: '', descricao_problema: '', km_entrada: 0 })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit({ ...form, veiculo_id: Number(form.veiculo_id), km_entrada: Number(form.km_entrada) }) }} className="space-y-3">
      <div>
        <label className="text-xs text-gray-400 mb-1 block">Veículo *</label>
        <select className="input" value={form.veiculo_id} onChange={set('veiculo_id')} required>
          <option value="">Selecionar...</option>
          {veiculos.map(v => <option key={v.id} value={v.id}>{v.placa} — {v.marca} {v.modelo} ({v.cliente.nome})</option>)}
        </select>
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">KM na Entrada *</label>
        <input className="input" type="number" value={form.km_entrada} onChange={set('km_entrada')} required />
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">Descrição do Problema *</label>
        <textarea className="input min-h-24 resize-none" value={form.descricao_problema} onChange={set('descricao_problema')} required />
      </div>
      <div className="flex justify-end pt-1">
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? 'Salvando...' : 'Abrir OS'}</button>
      </div>
    </form>
  )
}

function OSDetalhe({ os, onClose }) {
  const qc = useQueryClient()
  const [pecaId, setPecaId] = useState('')
  const [qtd, setQtd] = useState(1)

  const { data: pecas = [] } = useQuery({ queryKey: ['pecas-select'], queryFn: () => api.get('/pecas', { params: { limit: 200 } }).then(r => r.data) })

  const mudarStatus = useMutation({
    mutationFn: s => api.patch(`/ordens/${os.id}/status`, { status: s }),
    onSuccess: () => { toast.success('Status atualizado!'); qc.invalidateQueries(['ordens']); onClose() },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  const addItem = useMutation({
    mutationFn: d => api.post(`/ordens/${os.id}/itens`, d),
    onSuccess: () => { toast.success('Peça adicionada!'); qc.invalidateQueries(['ordens']); setPecaId(''); setQtd(1) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })
  const removeItem = useMutation({
    mutationFn: itemId => api.delete(`/ordens/${os.id}/itens/${itemId}`),
    onSuccess: () => { toast.success('Item removido'); qc.invalidateQueries(['ordens']) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })

  const proximos = PROXIMOS_STATUS[os.status] ?? []
  const podeEditar = !['concluida','cancelada'].includes(os.status)

  return (
    <div className="space-y-5">
      {/* Cabeçalho */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLOR[os.status]}`}>{STATUS_LABEL[os.status]}</span>
        <span className="text-gray-400 text-sm">{os.veiculo.placa} · {os.veiculo.marca} {os.veiculo.modelo}</span>
        <span className="text-gray-500 text-sm">Cliente: {os.cliente.nome}</span>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-1">Problema relatado</p>
        <p className="text-sm text-gray-200">{os.descricao_problema}</p>
      </div>

      {/* Peças */}
      {podeEditar && (
        <div className="border border-gray-800 rounded-lg p-3 space-y-2">
          <p className="text-xs font-medium text-gray-400">Adicionar Peça</p>
          <div className="flex gap-2">
            <select className="input flex-1 text-sm" value={pecaId} onChange={e => setPecaId(e.target.value)}>
              <option value="">Selecionar peça...</option>
              {pecas.map(p => <option key={p.id} value={p.id}>{p.nome} (estoque: {p.estoque_atual} {p.unidade})</option>)}
            </select>
            <input className="input w-20 text-sm" type="number" min={1} value={qtd} onChange={e => setQtd(Number(e.target.value))} />
            <button className="btn-primary px-3" onClick={() => { if (pecaId) addItem.mutate({ peca_id: Number(pecaId), quantidade: qtd }) }} disabled={!pecaId || addItem.isPending}>
              <Plus size={16} />
            </button>
          </div>
        </div>
      )}

      {os.itens?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-400 mb-2">Peças utilizadas</p>
          <table className="w-full text-sm">
            <tbody>
              {os.itens.map(item => (
                <tr key={item.id} className="table-row">
                  <td className="py-1.5 text-gray-200">{item.peca?.nome ?? `Peça #${item.peca_id}`}</td>
                  <td className="py-1.5 text-gray-400 text-right">{item.quantidade}x R$ {Number(item.preco_unitario).toFixed(2)}</td>
                  <td className="py-1.5 text-right font-medium pl-4">R$ {Number(item.subtotal).toFixed(2)}</td>
                  {podeEditar && <td className="py-1.5 pl-2"><button className="btn-ghost p-1 text-red-400" onClick={() => removeItem.mutate(item.id)}><X size={12} /></button></td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Totais */}
      <div className="border-t border-gray-800 pt-3 space-y-1 text-sm">
        <div className="flex justify-between text-gray-400"><span>Mão de obra</span><span>R$ {Number(os.valor_mao_obra).toFixed(2)}</span></div>
        <div className="flex justify-between text-gray-400"><span>Peças</span><span>R$ {Number(os.valor_pecas).toFixed(2)}</span></div>
        <div className="flex justify-between font-bold text-base text-gray-100 pt-1"><span>Total</span><span className="text-green-400">R$ {Number(os.valor_total).toFixed(2)}</span></div>
      </div>

      {/* Ações de status */}
      {proximos.length > 0 && (
        <div className="flex gap-2 flex-wrap pt-1">
          {proximos.map(s => (
            <button key={s} className={`btn-secondary text-sm ${s === 'cancelada' ? 'text-red-400' : ''}`}
              onClick={() => { if (confirm(`Mudar para "${STATUS_LABEL[s]}"?`)) mudarStatus.mutate(s) }}
              disabled={mudarStatus.isPending}>
              <ChevronRight size={14} className="inline mr-1" />{STATUS_LABEL[s]}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function OrdensPage() {
  const qc = useQueryClient()
  const [busca, setBusca] = useState('')
  const [modal, setModal] = useState(null)
  const [detalhe, setDetalhe] = useState(null)

  const { data: ordens = [], isLoading } = useQuery({
    queryKey: ['ordens', busca],
    queryFn: () => api.get('/ordens', { params: { limit: 50 } }).then(r => r.data)
  })
  const { data: veiculos = [] } = useQuery({
    queryKey: ['veiculos-select'],
    queryFn: () => api.get('/veiculos', { params: { limit: 200 } }).then(r => r.data)
  })

  const criar = useMutation({
    mutationFn: d => api.post('/ordens', d),
    onSuccess: () => { toast.success('OS aberta!'); qc.invalidateQueries(['ordens']); setModal(null) },
    onError: e => toast.error(e.response?.data?.detail ?? 'Erro')
  })

  // Recarrega OS ao abrir detalhe para ter itens frescos
  const { data: osDetalhe } = useQuery({
    queryKey: ['os-detalhe', detalhe],
    queryFn: () => api.get(`/ordens/${detalhe}`).then(r => r.data),
    enabled: !!detalhe
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Ordens de Serviço</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => setModal('novo')}><Plus size={16} /> Nova OS</button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-800">
            <tr className="text-gray-500 text-left">
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Veículo</th>
              <th className="px-4 py-3 font-medium">Cliente</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Total</th>
              <th className="px-4 py-3 font-medium">Data</th>
              <th className="px-4 py-3 font-medium w-10"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7} className="text-center py-10 text-gray-500">Carregando...</td></tr>
            ) : ordens.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-10 text-gray-500">Nenhuma OS</td></tr>
            ) : ordens.map(o => (
              <tr key={o.id} className="table-row cursor-pointer" onClick={() => setDetalhe(o.id)}>
                <td className="px-4 py-3 text-gray-500 font-mono">#{o.id}</td>
                <td className="px-4 py-3 font-medium text-brand">{o.veiculo.placa} <span className="text-gray-400 font-normal">{o.veiculo.marca} {o.veiculo.modelo}</span></td>
                <td className="px-4 py-3 text-gray-400">{o.cliente.nome}</td>
                <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOR[o.status]}`}>{STATUS_LABEL[o.status]}</span></td>
                <td className="px-4 py-3 text-right text-green-400 font-medium">R$ {Number(o.valor_total).toFixed(2)}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{new Date(o.created_at).toLocaleDateString('pt-BR')}</td>
                <td className="px-4 py-3"><ChevronRight size={14} className="text-gray-600" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal === 'novo' && (
        <Modal title="Nova Ordem de Serviço" onClose={() => setModal(null)}>
          <NovaOSForm veiculos={veiculos} onSubmit={d => criar.mutate(d)} loading={criar.isPending} />
        </Modal>
      )}

      {detalhe && osDetalhe && (
        <Modal title={`OS #${detalhe}`} onClose={() => setDetalhe(null)} wide>
          <OSDetalhe os={osDetalhe} onClose={() => setDetalhe(null)} />
        </Modal>
      )}
    </div>
  )
}
