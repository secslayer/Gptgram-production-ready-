import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { 
  TrendingUp,
  DollarSign,
  Activity,
  Zap,
  Bot,
  GitBranch
} from 'lucide-react'

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('7d')
  const [metrics, setMetrics] = useState({
    dailyRuns: [],
    agentPerformance: [],
    costBreakdown: [],
    transformMethods: []
  })

  useEffect(() => {
    // In production, fetch real analytics data
    setMetrics({
      dailyRuns: [
        { date: 'Mon', runs: 12, cost: 580 },
        { date: 'Tue', runs: 18, cost: 920 },
        { date: 'Wed', runs: 15, cost: 750 },
        { date: 'Thu', runs: 22, cost: 1100 },
        { date: 'Fri', runs: 28, cost: 1400 },
        { date: 'Sat', runs: 19, cost: 950 },
        { date: 'Sun', runs: 14, cost: 700 }
      ],
      agentPerformance: [
        { name: 'Summarizer', calls: 234, successRate: 95, avgLatency: 1200 },
        { name: 'Sentiment', calls: 456, successRate: 98, avgLatency: 800 },
        { name: 'Translator', calls: 123, successRate: 92, avgLatency: 1500 },
        { name: 'Moderator', calls: 89, successRate: 88, avgLatency: 600 },
        { name: 'Formatter', calls: 178, successRate: 96, avgLatency: 400 }
      ],
      costBreakdown: [
        { name: 'Agent Calls', value: 3200, color: '#3B82F6' },
        { name: 'LLM Transforms', value: 850, color: '#EF4444' },
        { name: 'GAT Suggestions', value: 420, color: '#10B981' },
        { name: 'Platform Fees', value: 890, color: '#F59E0B' }
      ],
      transformMethods: [
        { method: 'Deterministic', count: 782, successRate: 98 },
        { method: 'Mapping Hint', count: 345, successRate: 95 },
        { method: 'GAT', count: 156, successRate: 87 },
        { method: 'LLM', count: 89, successRate: 78 }
      ]
    })
  }, [timeRange])

  const StatCard = ({ title, value, change, icon: Icon, color = 'text-primary' }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <p className="text-xs text-muted-foreground">
            <TrendingUp className="inline h-3 w-3 mr-1" />
            {change} from last period
          </p>
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Platform performance and usage metrics
          </p>
        </div>
        <div className="flex space-x-2">
          {['24h', '7d', '30d', '90d'].map(range => (
            <Badge
              key={range}
              variant={timeRange === range ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setTimeRange(range)}
            >
              {range}
            </Badge>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard 
          title="Total Revenue" 
          value="$543.20"
          change="+12.5%"
          icon={DollarSign}
          color="text-green-500"
        />
        <StatCard 
          title="Active Agents" 
          value="24"
          change="+3"
          icon={Bot}
          color="text-blue-500"
        />
        <StatCard 
          title="Chain Runs" 
          value="128"
          change="+18%"
          icon={GitBranch}
          color="text-purple-500"
        />
        <StatCard 
          title="Avg Success Rate" 
          value="94.2%"
          change="+2.1%"
          icon={Activity}
          color="text-orange-500"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-2 gap-6">
        {/* Daily Runs Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Runs & Cost</CardTitle>
            <CardDescription>Chain executions and spending over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics.dailyRuns}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="runs" 
                  stroke="#3B82F6" 
                  name="Runs"
                  strokeWidth={2}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="cost" 
                  stroke="#10B981" 
                  name="Cost (¢)"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Cost Breakdown Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Cost Breakdown</CardTitle>
            <CardDescription>Where your credits are spent</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={metrics.costBreakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: $${(entry.value/100).toFixed(2)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {metrics.costBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-2 gap-6">
        {/* Agent Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Top Agents by Usage</CardTitle>
            <CardDescription>Most called agents and their performance</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics.agentPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="calls" fill="#3B82F6" name="Calls" />
                <Bar dataKey="successRate" fill="#10B981" name="Success %" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Transform Methods */}
        <Card>
          <CardHeader>
            <CardTitle>Transform Methods</CardTitle>
            <CardDescription>Data transformation method usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {metrics.transformMethods.map(method => (
                <div key={method.method} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium">{method.method}</span>
                      <span className="text-sm text-muted-foreground">
                        {method.count} uses
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${method.successRate}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {method.successRate}% success rate
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* GAT Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>GAT Recommendation Performance</CardTitle>
          <CardDescription>Graph Attention Network mapping suggestions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-muted rounded">
              <Zap className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
              <p className="text-2xl font-bold">42%</p>
              <p className="text-sm text-muted-foreground">
                Successful GAT mappings
              </p>
            </div>
            <div className="text-center p-4 bg-muted rounded">
              <Activity className="h-8 w-8 mx-auto mb-2 text-green-500" />
              <p className="text-2xl font-bold">67ms</p>
              <p className="text-sm text-muted-foreground">
                Avg GAT inference time
              </p>
            </div>
            <div className="text-center p-4 bg-muted rounded">
              <TrendingUp className="h-8 w-8 mx-auto mb-2 text-blue-500" />
              <p className="text-2xl font-bold">$12.40</p>
              <p className="text-sm text-muted-foreground">
                Saved from LLM fallbacks
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
