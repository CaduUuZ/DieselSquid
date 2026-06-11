import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { ClipboardList, DollarSign, AlertTriangle, Package } from 'lucide-react'
import api from '../api/client'

const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const STATUS_COLORS = {
  aberta: '#3b82f6', em_andamento: '#f97316',
  aguardando_pecas: '#eab308', concluida: '#22c55e', cancelada: '#6b7280'
}

function KPICard({ icon: Icon, label, value, sub, color = 'text-brand' }) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`p-2.5 rounded-lg bg-gray-800 ${color}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-2xl font-bold mt-0.5">{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: kpis } = useQuery({ queryKey: ['kpis'], queryFn: () => api.get('/dashboard/kpis').then(r => r.data) })
  const { data: mensal = [] } = useQuery({ queryKey: ['mensal'], queryFn: () => api.get('/dashboard/faturamento-mensal').then(r => r.data) })
  const { data: porStatus = [] } = useQuery({ queryKey: ['status'], queryFn: () => api.get('/dashboard/os-por-status').then(r => r.data) })
  const { data: critico = [] } = useQuery({ queryKey: ['critico'], queryFn: () => api.get('/dashboard/estoque-critico').then(r => r.data) })
  const { data: topClientes = [] } = useQuery({ queryKey: ['topClientes'], queryFn: () => api.get('/dashboard/top-clientes').then(r => r.data) })

  const mensalFormatado = mensal.map(m => ({
    name: `${MESES[m.mes - 1]}/${String(m.ano).slice(2)}`,
    faturamento: m.faturamento
  }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard icon={ClipboardList} label="OS Abertas" value={kpis?.os_abertas ?? '—'} />
        <KPICard icon={ClipboardList} label="Em Andamento" value={kpis?.os_em_andamento ?? '—'} color="text-orange-400" />
        <KPICard
          icon={DollarSign} label="Faturamento do Mês"
          value={kpis ? `R$ ${kpis.faturamento_mes.toFixed(2)}` : '—'}
          sub={`Ticket médio: R$ ${kpis?.ticket_medio?.toFixed(2) ?? '0'}`}
          color="text-green-400"
        />
        <KPICard
          icon={Package} label="Estoque Crítico"
          value={kpis?.pecas_estoque_critico ?? '—'}
          color={kpis?.pecas_estoque_critico > 0 ? 'text-red-400' : 'text-gray-400'}
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Faturamento mensal */}
        <div className="card lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-400 mb-4">Faturamento Mensal (R$)</h2>
          {mensalFormatado.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={mensalFormatado}>
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} width={60}
                  tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                  formatter={v => [`R$ ${v.toFixed(2)}`, 'Faturamento']}
                />
                <Bar dataKey="faturamento" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-600 text-sm">Sem dados ainda</div>
          )}
        </div>

        {/* OS por status */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-400 mb-4">OS por Status</h2>
          {porStatus.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={porStatus} dataKey="total" nameKey="status" cx="50%" cy="50%" outerRadius={65} innerRadius={35}>
                    {porStatus.map(s => <Cell key={s.status} fill={STATUS_COLORS[s.status] ?? '#6b7280'} />)}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                    formatter={(v, n) => [v, n.replace('_', ' ')]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-2">
                {porStatus.map(s => (
                  <div key={s.status} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-gray-400 capitalize">
                      <span className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[s.status] }} />
                      {s.status.replace('_', ' ')}
                    </span>
                    <span className="font-semibold">{s.total}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-40 flex items-center justify-center text-gray-600 text-sm">Sem dados ainda</div>
          )}
        </div>
      </div>

      {/* Tabelas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top clientes */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-400 mb-4">Top Clientes</h2>
          {topClientes.length > 0 ? (
            <table className="w-full text-sm">
              <thead><tr className="text-gray-500 text-left">
                <th className="pb-2 font-medium">Cliente</th>
                <th className="pb-2 font-medium text-right">OS</th>
                <th className="pb-2 font-medium text-right">Total</th>
              </tr></thead>
              <tbody>
                {topClientes.slice(0, 5).map(c => (
                  <tr key={c.cliente_id} className="table-row">
                    <td className="py-2 pr-2 text-gray-200">{c.nome}</td>
                    <td className="py-2 text-right text-gray-400">{c.total_os}</td>
                    <td className="py-2 text-right text-green-400 font-medium">R$ {c.gasto_total.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="text-gray-600 text-sm">Sem dados ainda</p>}
        </div>

        {/* Estoque crítico */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
            <AlertTriangle size={14} className="text-red-400" /> Estoque Crítico
          </h2>
          {critico.length > 0 ? (
            <table className="w-full text-sm">
              <thead><tr className="text-gray-500 text-left">
                <th className="pb-2 font-medium">Peça</th>
                <th className="pb-2 font-medium text-right">Atual</th>
                <th className="pb-2 font-medium text-right">Mín.</th>
              </tr></thead>
              <tbody>
                {critico.map(p => (
                  <tr key={p.peca_id} className="table-row">
                    <td className="py-2 pr-2 text-gray-200">{p.nome}</td>
                    <td className="py-2 text-right text-red-400 font-bold">{p.estoque_atual}</td>
                    <td className="py-2 text-right text-gray-500">{p.estoque_minimo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="text-gray-600 text-sm">Tudo em ordem ✓</p>}
        </div>
      </div>
    </div>
  )
}
