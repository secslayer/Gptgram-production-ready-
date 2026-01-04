import { useState, useEffect } from 'react'
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
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Bot,
  GitBranch,
  Zap,
  AlertCircle,
  CheckCircle,
  Clock,
  BarChart2,
  PieChart as PieChartIcon,
  Calendar,
  Filter,
  Download
} from 'lucide-react'

export default function CompleteAnalytics() {
  // Revenue and cost data
  const revenueData = [
    { date: 'Oct 25', revenue: 450, cost: 320, profit: 130 },
    { date: 'Oct 26', revenue: 520, cost: 380, profit: 140 },
    { date: 'Oct 27', revenue: 480, cost: 350, profit: 130 },
    { date: 'Oct 28', revenue: 610, cost: 420, profit: 190 },
    { date: 'Oct 29', revenue: 580, cost: 400, profit: 180 },
    { date: 'Oct 30', revenue: 720, cost: 480, profit: 240 },
    { date: 'Oct 31', revenue: 850, cost: 550, profit: 300 }
  ]

  // Agent performance data
  const agentPerformance = [
    { name: 'n8n Summarizer', successRate: 95, calls: 234, avgLatency: 1200 },
    { name: 'Sentiment Analyzer', successRate: 98, calls: 456, avgLatency: 800 },
    { name: 'n8n Translator', successRate: 92, calls: 123, avgLatency: 1500 },
    { name: 'Content Moderator', successRate: 90, calls: 89, avgLatency: 600 },
    { name: 'Text Formatter', successRate: 88, calls: 67, avgLatency: 400 },
    { name: 'Keyword Extractor', successRate: 94, calls: 112, avgLatency: 1100 }
  ]

  // Transform method distribution
  const transformMethods = [
    { name: 'Direct', value: 745, percentage: 74.5, color: '#10b981' },
    { name: 'Deterministic', value: 170, percentage: 17.0, color: '#3b82f6' },
    { name: 'GAT', value: 64, percentage: 6.4, color: '#f59e0b' },
    { name: 'LLM', value: 21, percentage: 2.1, color: '#ef4444' }
  ]

  // Chain success rates
  const chainSuccess = [
    { chain: 'Text Processing', runs: 47, success: 44, rate: 93.6 },
    { chain: 'Sentiment Analysis', runs: 35, success: 31, rate: 88.6 },
    { chain: 'Translation Flow', runs: 28, success: 26, rate: 92.9 },
    { chain: 'Content Pipeline', runs: 22, success: 19, rate: 86.4 },
    { chain: 'Keyword Extraction', runs: 18, success: 17, rate: 94.4 }
  ]

  // GAT recommendations impact
  const gatImpact = [
    { month: 'Aug', withGAT: 82, withoutGAT: 68 },
    { month: 'Sep', withGAT: 85, withoutGAT: 70 },
    { month: 'Oct', withGAT: 92, withoutGAT: 73 }
  ]

  // Platform metrics
  const metrics = {
    totalRevenue: 4210,
    totalCost: 2850,
    totalProfit: 1360,
    activeUsers: 47,
    totalAgents: 12,
    totalChains: 8,
    totalRuns: 1234,
    successRate: 92,
    avgLatency: 890,
    llmUsage: 2.1,
    gatSuggestions: 64,
    costSavings: 32
  }

  const StatCard = ({ title, value, icon: Icon, trend, trendValue, color = 'text-primary' }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            {trend === 'up' ? (
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-500 mr-1" />
            )}
            {trendValue} from last period
          </p>
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Platform performance metrics and insights
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Last 7 days
          </Button>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Revenue"
          value={`$${(metrics.totalRevenue / 100).toFixed(2)}`}
          icon={DollarSign}
          trend="up"
          trendValue="+23%"
          color="text-green-500"
        />
        <StatCard
          title="Success Rate"
          value={`${metrics.successRate}%`}
          icon={Activity}
          trend="up"
          trendValue="+3%"
          color="text-blue-500"
        />
        <StatCard
          title="Total Runs"
          value={metrics.totalRuns.toLocaleString()}
          icon={Zap}
          trend="up"
          trendValue="+156"
          color="text-purple-500"
        />
        <StatCard
          title="Cost Savings"
          value={`${metrics.costSavings}%`}
          icon={TrendingUp}
          trend="up"
          trendValue="+8%"
          color="text-yellow-500"
        />
      </div>

      {/* Revenue & Cost Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue & Cost Analysis</CardTitle>
          <CardDescription>
            Daily revenue, costs, and profit over the last 7 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => `$${(value / 100).toFixed(2)}`} />
              <Legend />
              <Area
                type="monotone"
                dataKey="revenue"
                stackId="1"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="cost"
                stackId="2"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.6}
              />
              <Line
                type="monotone"
                dataKey="profit"
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transform Methods Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Transform Methods</CardTitle>
            <CardDescription>
              Distribution of transform methods used
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={transformMethods}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {transformMethods.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            
            <div className="mt-4 space-y-2">
              {transformMethods.map((method) => (
                <div key={method.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded"
                      style={{ backgroundColor: method.color }}
                    />
                    <span className="text-sm">{method.name}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {method.value} calls ({method.percentage}%)
                  </div>
                </div>
              ))}
            </div>
            
            {metrics.llmUsage < 5 && (
              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-600">
                    LLM usage at {metrics.llmUsage}% - well below 5% threshold
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Agent Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Performance</CardTitle>
            <CardDescription>
              Success rates by agent
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={agentPerformance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis dataKey="name" type="category" width={120} />
                <Tooltip />
                <Bar dataKey="successRate" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
            
            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold">{metrics.totalAgents}</p>
                <p className="text-xs text-muted-foreground">Total Agents</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{metrics.avgLatency}ms</p>
                <p className="text-xs text-muted-foreground">Avg Latency</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{metrics.successRate}%</p>
                <p className="text-xs text-muted-foreground">Overall Success</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* GAT Impact */}
      <Card>
        <CardHeader>
          <CardTitle>GAT Recommendations Impact</CardTitle>
          <CardDescription>
            Success rate comparison with and without GAT suggestions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={gatImpact}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis domain={[60, 100]} />
              <Tooltip formatter={(value) => `${value}%`} />
              <Legend />
              <Line
                type="monotone"
                dataKey="withGAT"
                stroke="#10b981"
                strokeWidth={2}
                name="With GAT"
              />
              <Line
                type="monotone"
                dataKey="withoutGAT"
                stroke="#ef4444"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Without GAT"
              />
            </LineChart>
          </ResponsiveContainer>
          
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Zap className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">GAT Performance Boost</span>
              </div>
              <Badge variant="default">
                +{metrics.successRate - 73}% improvement
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.gatSuggestions} successful mapping suggestions this month
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Chain Success Rates */}
      <Card>
        <CardHeader>
          <CardTitle>Chain Performance</CardTitle>
          <CardDescription>
            Success rates by chain type
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {chainSuccess.map((chain) => (
              <div key={chain.chain} className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1">
                  <GitBranch className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{chain.chain}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-muted-foreground">
                    {chain.success}/{chain.runs} runs
                  </span>
                  <Badge variant={chain.rate >= 90 ? 'success' : 'warning'}>
                    {chain.rate.toFixed(1)}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
