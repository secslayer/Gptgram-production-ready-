import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Wallet, 
  Bot, 
  GitBranch, 
  PlayCircle,
  TrendingUp,
  DollarSign,
  Activity,
  Zap
} from 'lucide-react'
import axios from 'axios'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    totalAgents: 0,
    totalChains: 0,
    totalRuns: 0,
    successRate: 0,
    totalSpent: 0,
    activeRuns: 0
  })
  const [recentRuns, setRecentRuns] = useState([])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      // In production, these would be real API calls
      // For demo, using mock data
      setStats({
        totalAgents: 12,
        totalChains: 5,
        totalRuns: 47,
        successRate: 92,
        totalSpent: 4250,
        activeRuns: 2
      })

      setRecentRuns([
        { 
          id: '1', 
          chain: 'Summarizer Pipeline', 
          status: 'succeeded', 
          cost: 45,
          duration: '2.3s'
        },
        { 
          id: '2', 
          chain: 'Sentiment Analysis', 
          status: 'running', 
          cost: 32,
          duration: '1.1s'
        },
        { 
          id: '3', 
          chain: 'Translation Flow', 
          status: 'succeeded', 
          cost: 78,
          duration: '3.7s'
        }
      ])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    }
  }

  const StatCard = ({ title, value, icon: Icon, trend, color = 'text-primary' }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <p className="text-xs text-muted-foreground">
            <TrendingUp className="inline h-3 w-3 mr-1" />
            {trend}
          </p>
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's an overview of your agent orchestration platform.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-4 gap-4">
        <Button 
          className="flex flex-col h-20 space-y-1"
          variant="outline"
          onClick={() => navigate('/agents')}
        >
          <Bot className="h-5 w-5" />
          <span className="text-xs">Create Agent</span>
        </Button>
        <Button 
          className="flex flex-col h-20 space-y-1"
          variant="outline"
          onClick={() => navigate('/chains')}
        >
          <GitBranch className="h-5 w-5" />
          <span className="text-xs">Build Chain</span>
        </Button>
        <Button 
          className="flex flex-col h-20 space-y-1"
          variant="outline"
          onClick={() => navigate('/runs')}
        >
          <PlayCircle className="h-5 w-5" />
          <span className="text-xs">View Runs</span>
        </Button>
        <Button 
          className="flex flex-col h-20 space-y-1"
          variant="outline"
        >
          <Wallet className="h-5 w-5" />
          <span className="text-xs">Top Up Wallet</span>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4">
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

      {/* Recent Runs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
          <CardDescription>
            Your latest chain executions and their status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentRuns.map(run => (
              <div key={run.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <PlayCircle className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{run.chain}</p>
                    <p className="text-sm text-muted-foreground">
                      Duration: {run.duration}
                    </p>
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
    </div>
  )
}
