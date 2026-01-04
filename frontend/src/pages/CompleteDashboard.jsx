import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { 
  Wallet, 
  Bot, 
  GitBranch, 
  PlayCircle,
  TrendingUp,
  DollarSign,
  Activity,
  Zap,
  Plus,
  ArrowRight
} from 'lucide-react'
import axios from 'axios'

export default function CompleteDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    walletBalance: 0,
    totalAgents: 0,
    totalChains: 0,
    totalRuns: 0,
    successRate: 0,
    totalSpent: 0,
    activeRuns: 0
  })
  const [recentRuns, setRecentRuns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token')
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      }

      // Fetch wallet balance
      const walletRes = await axios.get('http://localhost:8000/api/wallet/balance')
      
      // Fetch agents
      const agentsRes = await axios.get('http://localhost:8000/api/agents')
      
      // Fetch runs
      const runsRes = await axios.get('http://localhost:8000/api/runs/')
      
      // Calculate stats from real data
      const totalRuns = runsRes.data?.length || 0
      const successfulRuns = runsRes.data?.filter(r => r.status === 'completed').length || 0
      const successRate = totalRuns > 0 ? Math.round((successfulRuns / totalRuns) * 100) : 0
      const totalSpent = runsRes.data?.reduce((sum, r) => sum + (r.total_cost || 0), 0) || 0
      const activeRuns = runsRes.data?.filter(r => r.status === 'running').length || 0
      
      setStats({
        walletBalance: walletRes.data.balance || 0,
        totalAgents: agentsRes.data?.length || 0,
        totalChains: new Set(runsRes.data?.map(r => r.chain_id)).size || 0,
        totalRuns: totalRuns,
        successRate: successRate,
        totalSpent: totalSpent,
        activeRuns: activeRuns
      })

      // Map execution history to recent runs
      const runs = (runsRes.data || []).map(run => ({
        id: run.execution_id,
        chain: run.chain_id,
        status: run.status,
        cost: run.total_cost,
        duration: `${Math.round(run.duration_ms / 1000 * 10) / 10}s`,
        nodes: run.execution_log?.length || 0
      }))
      setRecentRuns(runs)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setLoading(false)
    }
  }

  const QuickActionCard = ({ icon: Icon, title, description, onClick, color = 'blue' }) => (
    <Card 
      className="cursor-pointer hover:shadow-lg transition-all hover:scale-105"
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className={`w-12 h-12 rounded-lg bg-${color}-100 flex items-center justify-center mb-4`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
        <h3 className="font-semibold mb-1">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )

  const StatCard = ({ title, value, icon: Icon, trend, color = 'text-primary' }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <p className="text-xs text-muted-foreground mt-1">
            <TrendingUp className="inline h-3 w-3 mr-1" />
            {trend}
          </p>
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header with Wallet */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's an overview of your agent orchestration platform.
          </p>
        </div>
        <Card className="w-64">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Wallet className="h-5 w-5" />
                <span className="font-semibold">Wallet Balance</span>
              </div>
            </div>
            <div className="text-2xl font-bold">
              ${(stats.walletBalance / 100).toFixed(2)}
            </div>
            <Button 
              className="w-full mt-3" 
              variant="outline" 
              size="sm"
              onClick={() => navigate('/wallet')}
            >
              <Plus className="h-4 w-4 mr-1" />
              Top Up
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickActionCard
            icon={Bot}
            title="Create Agent"
            description="Add a new A2A-compliant agent"
            onClick={() => navigate('/agents')}
            color="blue"
          />
          <QuickActionCard
            icon={GitBranch}
            title="Build Chain"
            description="Design a new DAG workflow"
            onClick={() => navigate('/chains')}
            color="purple"
          />
          <QuickActionCard
            icon={PlayCircle}
            title="View Runs"
            description="Monitor execution history"
            onClick={() => navigate('/runs')}
            color="green"
          />
          <QuickActionCard
            icon={Wallet}
            title="Top Up Wallet"
            description="Add credits to your account"
            onClick={() => {}}
            color="yellow"
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Platform Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard 
            title="Total Agents" 
            value={stats.totalAgents}
            icon={Bot}
            trend="+2 this week"
          />
          <StatCard 
            title="Total Chains" 
            value={stats.totalChains}
            icon={GitBranch}
            trend="+1 this week"
            color="text-blue-500"
          />
          <StatCard 
            title="Success Rate" 
            value={`${stats.successRate}%`}
            icon={Activity}
            trend="+3% from last week"
            color="text-green-500"
          />
          <StatCard 
            title="Total Runs" 
            value={stats.totalRuns}
            icon={PlayCircle}
            trend="+12 today"
            color="text-purple-500"
          />
          <StatCard 
            title="Total Spent" 
            value={`$${(stats.totalSpent / 100).toFixed(2)}`}
            icon={DollarSign}
            color="text-yellow-500"
          />
          <StatCard 
            title="Active Runs" 
            value={stats.activeRuns}
            icon={Zap}
            color="text-orange-500"
          />
        </div>
      </div>

      {/* Recent Runs */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Recent Runs</CardTitle>
              <CardDescription>
                Your latest chain executions and their status
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/runs')}>
              View All
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentRuns.map(run => (
              <div key={run.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-2 h-2 rounded-full ${
                    run.status === 'succeeded' ? 'bg-green-500' : 
                    run.status === 'running' ? 'bg-yellow-500 animate-pulse' : 
                    'bg-red-500'
                  }`} />
                  <PlayCircle className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{run.chain}</p>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>{run.nodes} nodes</span>
                      <span>•</span>
                      <span>{run.duration}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <Badge variant={
                    run.status === 'succeeded' ? 'success' : 
                    run.status === 'running' ? 'warning' : 
                    'destructive'
                  }>
                    {run.status}
                  </Badge>
                  <span className="text-sm font-medium">
                    ${(run.cost / 100).toFixed(2)}
                  </span>
                  <Button size="sm" variant="ghost">View</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Live Chain Execution Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Live Execution</CardTitle>
          <CardDescription>Real-time chain execution monitoring</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <Bot className="h-6 w-6 text-green-600" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-ping" />
              </div>
              <div>
                <p className="font-medium">n8n Summarizer</p>
                <p className="text-sm text-muted-foreground">Processing input...</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Elapsed</p>
              <p className="font-mono">1.2s</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
