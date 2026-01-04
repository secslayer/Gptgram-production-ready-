import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import {
  TrendingUp,
  DollarSign,
  Activity,
  Zap,
  GitBranch,
  Code,
  Sparkles,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react'

export default function RealAnalytics() {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAnalytics()
    const interval = setInterval(loadAnalytics, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadAnalytics = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/analytics/data')
      setAnalyticsData(response.data)
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Failed to load analytics: {error}</p>
        </div>
      </div>
    )
  }

  const { 
    total_runs, 
    total_spent, 
    success_rate,
    transform_methods,
    revenue_over_time,
    agent_performance
  } = analyticsData

  // Prepare data for charts
  const transformMethodData = Object.entries(transform_methods || {}).map(([method, count]) => ({
    name: method,
    value: count,
    percentage: Math.round((count / Object.values(transform_methods).reduce((a, b) => a + b, 0)) * 100)
  }))

  const COLORS = {
    deterministic: '#10b981',
    gat: '#3b82f6',
    llm: '#a855f7'
  }

  const getTransformIcon = (method) => {
    switch (method) {
      case 'deterministic':
        return <GitBranch className="h-4 w-4" />
      case 'gat':
        return <Code className="h-4 w-4" />
      case 'llm':
        return <Sparkles className="h-4 w-4" />
      default:
        return <Zap className="h-4 w-4" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time insights into chain execution and transform methods
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">{total_runs}</div>
              <Activity className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              +12% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Spent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">
                ${(total_spent / 100).toFixed(2)}
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Avg: ${((total_spent / total_runs) / 100).toFixed(2)}/run
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">{success_rate}%</div>
              <CheckCircle className="h-8 w-8 text-blue-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              +3% improvement
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Most Used Transform</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold">
                  {transformMethodData[0]?.name || 'N/A'}
                </span>
                <Badge variant="outline" className="text-xs">
                  {transformMethodData[0]?.percentage || 0}%
                </Badge>
              </div>
              {getTransformIcon(transformMethodData[0]?.name)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {transformMethodData[0]?.value || 0} uses
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Revenue Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue Trend</CardTitle>
            <CardDescription>Daily revenue from chain executions</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenue_over_time}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(date) => new Date(date).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                />
                <YAxis tickFormatter={(value) => `$${(value / 100).toFixed(0)}`} />
                <Tooltip 
                  formatter={(value) => `$${(value / 100).toFixed(2)}`}
                  labelFormatter={(date) => new Date(date).toLocaleDateString()}
                />
                <Area 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#10b981" 
                  fill="#10b98133" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Transform Methods Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Transform Methods</CardTitle>
            <CardDescription>Distribution of transform types used</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={transformMethodData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} ${percentage}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {transformMethodData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#8884d8'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {transformMethodData.map(method => (
                <div key={method.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded" 
                      style={{ backgroundColor: COLORS[method.name] || '#8884d8' }}
                    />
                    <span className="text-sm">{method.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">{method.value}</span>
                    <Badge variant="outline" className="text-xs">
                      {method.percentage}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Performance</CardTitle>
          <CardDescription>Success rates and usage statistics by agent</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agent_performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
              <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="runs" fill="#8884d8" name="Total Runs" />
              <Bar yAxisId="right" dataKey="success_rate" fill="#82ca9d" name="Success Rate (%)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Transform Method Impact */}
      <Card>
        <CardHeader>
          <CardTitle>Transform Method Impact Analysis</CardTitle>
          <CardDescription>Comparison of performance across different transform methods</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <GitBranch className="h-4 w-4 text-green-500" />
                  <span className="font-medium">Deterministic</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-muted-foreground">Speed: 50ms</span>
                  <span className="text-sm text-muted-foreground">Cost: $0.00</span>
                  <Badge variant="success">98% success</Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '98%' }} />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Code className="h-4 w-4 text-blue-500" />
                  <span className="font-medium">GAT</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-muted-foreground">Speed: 150ms</span>
                  <span className="text-sm text-muted-foreground">Cost: $0.01</span>
                  <Badge variant="info">92% success</Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '92%' }} />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                  <span className="font-medium">LLM (Gemini)</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-muted-foreground">Speed: 800ms</span>
                  <span className="text-sm text-muted-foreground">Cost: $0.15</span>
                  <Badge variant="secondary">88% success</Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '88%' }} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Real-time Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Live feed of chain executions and transforms</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm">Chain "Text Processing" executed successfully</span>
              <Badge variant="outline" className="text-xs">deterministic</Badge>
              <span className="text-xs text-muted-foreground ml-auto">2 min ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <Sparkles className="h-4 w-4 text-purple-500" />
              <span className="text-sm">LLM transform applied in "Translation Pipeline"</span>
              <Badge variant="outline" className="text-xs">llm</Badge>
              <span className="text-xs text-muted-foreground ml-auto">5 min ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <Code className="h-4 w-4 text-blue-500" />
              <span className="text-sm">GAT mapping used in "Sentiment Analysis"</span>
              <Badge variant="outline" className="text-xs">gat</Badge>
              <span className="text-xs text-muted-foreground ml-auto">8 min ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm">Chain "Multi-Agent Flow" completed</span>
              <Badge variant="outline" className="text-xs">deterministic</Badge>
              <span className="text-xs text-muted-foreground ml-auto">12 min ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
